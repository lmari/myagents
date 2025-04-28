from openai import OpenAI
from typing import Type
from pydantic import BaseModel
import json
from IPython.display import Markdown, display
from agentformats import _get_format_metadata
from agenttools import _get_tool_metadata, _exec_tool

class Context:
    def __init__(self, output_channel: str="stream", output_format: str="markdown"):
        """
        Context for the agents, in particular maintaining the information on the team of involved agents
        and the memory of their conversation.
        Args:
            output_channel: The output channel for the agent. Options are "silent", "standard" (default), "stream"
            output_format: The output format for the agent. Options are "plaintext" (default), "markdown"
        """
        self.output_channel: str = output_channel if output_channel in ["silent", "standard", "stream"] else "standard"
        self.output_format: str = output_format if output_format in ["plaintext", "markdown"] else "plaintext"
        self.team: list[MyAgent] = []
        self.conversation: list[dict] = []
        self.buffer: str = ""
        self.current_agent: MyAgent|MyManager|None = None
        self.last_result = None

    def _get_agent_by_name(self, name: str) -> 'MyAgent | None':
        for agent in self.team:
            if agent.name == name:
                return agent
        return None
    
    def _get_current_agent_name(self) -> str:
        return self.current_agent.name if self.current_agent else "Unknown"

    def _get_formatted_agent_name(self, name: str) -> str:
        return f"---\n**{name}**" if self.output_format == "markdown" else f"\n[{name}]"

    def _print(self, text: str):
        _text = f"{self._get_formatted_agent_name(self._get_current_agent_name())}: {text}"
        self.buffer += _text
        if self.output_format == "markdown":
            display(Markdown(_text))
        else:
            print(_text)

    def _debug(self, text: str):
        _text = f"\n\n `DEBUG: {text}`"
        self.buffer += _text
        if self.output_format == "markdown":
            display(Markdown(_text))
        else:
            print(_text)

    def _validate(self, text: str):
        _text = f"\n\n `VALIDATE: {text}`"
        self.buffer += _text
        if self.output_format == "markdown":
            display(Markdown(_text))
        else:
            print(_text)

    def _stream(self, response):
        result = ""
        _text = "\n\n" + self._get_formatted_agent_name(self._get_current_agent_name()) + ": "
        self.buffer += _text
        if self.output_format == "plaintext": print(_text, end='', flush=True)
        for chunk in response:
            text = chunk.choices[0].delta
            if hasattr(text, 'content') and text.content:
                result += text.content
                self.buffer += text.content
                if self.output_format == "markdown":
                    display(Markdown(self.buffer), clear=True)
                else:
                    print(text.content, end='', flush=True)
        return result


class MyAgent:
    def __init__(self, name: str, context: Context, base_url: str="http://localhost:1234/v1",
                 model: str="", role_and_skills: str="", response_format: Type[BaseModel]|None=None, tools: list=[],
                 max_tokens: int=-1, temperature: float=0.7):
        """
        Basic agent for OpenAI API.
        Args:
            name: The name of the agent
            context: The context for the agent
            base_url: The base URL for the OpenAI API (default is localhost:1234, as used by LM Studio)
            model: The model to use for the agent (optional for LM Studio)
            role_and_skills: The role and skills of the agent, for setting its system message
            response_format: The optional response format for the agent
            tools: The optional list of tools to use for the agent
            max_tokens: The maximum number of tokens to generate
            temperature: The temperature to use for the agent
        """
        self.name: str = name
        self.context = context
        self.client = OpenAI(base_url=base_url)
        self.model = model
        self.role_and_skills = role_and_skills
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.response_format = response_format
        self.tools = tools
        self.tool_names = ", ".join([tool.__name__ for tool in tools])
        self.tool_schemas = []
        for tool in tools:
            self.tool_schemas.append(_get_tool_metadata(tool))
        self.system_message = {"role": "system", "content": self.role_and_skills}
        self.context.team.append(self)

    def do(self, user_request: str, response_format: Type[BaseModel]|None=None, validate: bool=False,
           expanded_tool_response: bool=False, debug: bool=False) -> None:
        self.context.current_agent = self
        local_response_format = response_format if response_format else self.response_format
        messages = [self.system_message]
        if self.context.conversation:
            messages += self.context.conversation
        messages.append({"role": "user", "content": user_request})
        self.context.conversation.append({"role": "user", "content": user_request})
        if debug: self.context._debug(f"[messages in user request] {messages}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages, # type: ignore
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=self.context.output_channel == "stream" and not self.tools,
            **({"response_format": _get_format_metadata(local_response_format)} if local_response_format else {}), # type: ignore
            tools=self.tool_schemas if self.tools else None # type: ignore
        )

        if self.tool_schemas: # gestione della chiamata a strumenti
            if debug: self.context._debug(f"[response about function call] {response.choices[0].message.tool_calls}")
            tool_call_result = _exec_tool(response)
            if not tool_call_result["correct"]:
                result = tool_call_result["result"]
            else:
                if not expanded_tool_response:
                    result = [result_dict["result"] for result_dict in tool_call_result["result"]]
                    if len(result) == 1: result = result[0] # per evitare di restituire una lista con un solo elemento
                else:
                    messages2 = messages.copy()
                    messages2.append({
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": tool_call.type,
                                "function": tool_call.function,
                            } for tool_call in response.choices[0].message.tool_calls
                        ] # type: ignore
                    })
                    messages2 += tool_call_result["for_completion_messages"]
                    if debug: self.context._debug(f"[messages in function call] {messages2}")
                    response2 = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages2,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        stream=False,
                        **({"response_format": self.response_format} if self.response_format else {}), # type: ignore
                        tools=self.tool_schemas
                    )
                    result = response2.choices[0].message.content
            if self.context.output_channel != "silent": self.context._print(result) # type: ignore
        else:
            if self.context.output_channel == "stream":
                result = self.context._stream(response)
            else:
                result = response.choices[0].message.content
                if self.context.output_channel != "silent": self.context._print(result)
        
        if local_response_format and validate:
            try:
                local_response_format.model_validate(json.loads(result)) # type: ignore
                self.context._validate(f"Response valid!")
            except Exception as e:
                self.context._validate(f"Response format error: {e}")

        self.context.last_result = result # type: ignore
        self.context.conversation.append({"role": "assistant", "agentname": self.name, "content": str(result)}) # str() to avoid JSON serialization issues


class MyManager(MyAgent):
    def __init__(self, name: str, context: Context, base_url: str="http://localhost:1234/v1",
                 model: str="", role_and_skills: str="", response_format: Type[BaseModel]|None=None,
                 max_tokens: int=-1, temperature: float=0.7):
        tools = []
        super().__init__(name, context, base_url, model, role_and_skills, response_format, tools, max_tokens, temperature)

    def sequence(self, requests: list) -> None:
        for request in requests:
            agent = self.context._get_agent_by_name(request[0])
            if agent:
                if len(request) == 2:
                    if isinstance(request[1], str):
                        agent.do(request[1])
                    elif isinstance(request[1], list):
                        for sub_request in request[1]:
                            agent.do(sub_request)
                elif len(request) == 3:
                    if isinstance(request[2], dict):
                        if "action" in request[2]:
                            if request[2]["action"] == "loop":
                                if "count" in request[2]:
                                    for _ in range(request[2]["count"]):
                                        agent.do(request[1])
                                elif "data" in request[2]:
                                    if isinstance(request[2]["data"], list):
                                        for item in request[2]["data"]:
                                            agent.do(request[1] + " " + str(item))
                                    elif request[2]["data"] == "last_result":
                                        if isinstance(self.context.last_result, list):
                                            for item in self.context.last_result: # type: ignore
                                                agent.do(request[1] + " " + str(item))

    def round_robin(self, user_request: str, involved_agents: list, max_rounds: int=5) -> None:
        stop_expression = "Sono soddisfatto"
        self.system_message = {"role": "system", "content": self.role_and_skills + f"\nSe sei soddisfatto, scrivi '{stop_expression}'. Hai a disposizione un massimo di {max_rounds} interazioni per questo compito."}
        messages = [self.system_message]
        if self.context.conversation:
            messages += self.context.conversation
        request = user_request
        for i in range(max_rounds):
            for agent_name in involved_agents:
                agent = self.context._get_agent_by_name(agent_name)
                if agent:
                    agent.do(request) # type: ignore
                    request = self.context.last_result
            self.system_message = {"role": "system", "content": self.role_and_skills + f"Solo se tu e i tuoi colleghi siete davvero soddisfatti del lavoro, scrivi '{stop_expression}'. Hai a disposizione ancora {max_rounds - i - 1} interazioni per questo compito."}
            self.do(f"Solo se tu e i tuoi colleghi siete davvero soddisfatti del lavoro, scrivi '{stop_expression}. Altrimenti dai un breve suggerimento su come proseguire.")
            request = self.context.last_result
            if stop_expression in request: # type: ignore
                break
