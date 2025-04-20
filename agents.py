# *************************************************************
# Functions to parse docstrings and create OpenAI tool JSON ***
# *************************************************************
import inspect
import re
import json
from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints

def parse_docstring_for_openai_tools(func: Callable) -> Dict[str, Any]:
    """
    Parse a function's docstring and signature to generate an OpenAI tool schema.
    
    This function extracts information from the docstring and function signature
    to create a schema compatible with OpenAI's tool calling API format.
    
    Args:
        func: The function to parse for OpenAI tool calling
        
    Returns:
        A dictionary formatted according to OpenAI's tool definition schema
    """
    # Get the function's docstring and parse it
    docstring = inspect.getdoc(func) or ""
    
    # Extract basic information
    description_match = re.search(r"(.*?)(?:\n\s*\n|\n\s*Args:|\n\s*Parameters:|\Z)", docstring, re.DOTALL)
    description = description_match.group(1).strip() if description_match else ""
    
    # Get parameter information from docstring
    params_match = re.search(r"(?:Args|Parameters):(.*?)(?:\n\s*\n|\n\s*Returns:|\n\s*Raises:|\Z)", docstring, re.DOTALL)
    params_text = params_match.group(1) if params_match else ""
    
    # Parse parameters
    param_descriptions = {}
    if params_text:
        param_matches = re.findall(r'\s*[-*]?\s*(\w+)(?:\s*\(([^)]+)\))?:\s*(.*?)(?=\s*\n\s*[-*]?\s*\w+:|$)', params_text, re.DOTALL)
        for name, type_hint, desc in param_matches:
            param_descriptions[name] = {
                "description": desc.strip(),
                "type_hint": type_hint.strip() if type_hint else None
            }
    
    # Get return information
    returns_match = re.search(r"Returns:(.*?)(?:\n\s*\n|\n\s*Raises:|\Z)", docstring, re.DOTALL)
    returns_desc = returns_match.group(1).strip() if returns_match else ""
    
    # Get function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Build parameters schema for OpenAI format
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Process each parameter
    for param_name, param in sig.parameters.items():
        # Skip self, cls, and *args, **kwargs
        if param_name in ('self', 'cls') or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        
        # Get parameter type
        param_type = type_hints.get(param_name, None)
        
        # Get parameter description from docstring
        param_info = param_descriptions.get(param_name, {"description": "", "type_hint": None})
        
        # Create parameter schema
        param_schema = {"description": param_info["description"]}
        
        # Determine parameter type for schema
        if param_type:
            if param_type is str:
                param_schema["type"] = "string"
            elif param_type is int:
                param_schema["type"] = "integer"
            elif param_type is float:
                param_schema["type"] = "number"
            elif param_type is bool:
                param_schema["type"] = "boolean"
            elif param_type is list or param_type.__origin__ is list if hasattr(param_type, "__origin__") else False:
                param_schema["type"] = "array"
                # Try to get item type if available
                if hasattr(param_type, "__args__") and param_type.__args__: # type: ignore
                    item_type = param_type.__args__[0] # type: ignore
                    if item_type is str:
                        param_schema["items"] = {"type": "string"}
                    elif item_type is int:
                        param_schema["items"] = {"type": "integer"}
                    elif item_type is float:
                        param_schema["items"] = {"type": "number"}
                    elif item_type is bool:
                        param_schema["items"] = {"type": "boolean"}
                    else:
                        param_schema["items"] = {"type": "object"}
            elif param_type is dict or param_type.__origin__ is dict if hasattr(param_type, "__origin__") else False:
                param_schema["type"] = "object"
            else:
                param_schema["type"] = "object"
        else:
            # Default to string if no type hint is available
            param_schema["type"] = "string"
        
        # Add enum if mentioned in docstring
        enum_match = re.search(r"(?:one of|values):\s*\[(.*?)\]", param_info["description"], re.IGNORECASE)
        if enum_match:
            try:
                # Try to parse the enum values from the description
                enum_values = [x.strip().strip("'\"") for x in enum_match.group(1).split(",")]
                if enum_values:
                    param_schema["enum"] = enum_values
            except:
                pass
        
        # Add parameter to properties
        parameters["properties"][param_name] = param_schema
        
        # Check if parameter is required
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(param_name)
    
    # Create the final OpenAI tool schema
    tool_schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": parameters
        }
    }
    
    # Add return type if available
    if "return" in type_hints:
        return_type = type_hints["return"]
        tool_schema["function"]["return_type"] = str(return_type.__name__ if hasattr(return_type, "__name__") else return_type)
    
    return tool_schema

def create_openai_tools_from_functions(functions: List[Callable]) -> List[Dict[str, Any]]:
    tools = []
    for func in functions:
        tool_schema = parse_docstring_for_openai_tools(func)
        tools.append(tool_schema)
    return tools

def validate_openai_tool_schema(tool_schema: Dict[str, Any]) -> bool:
    if not isinstance(tool_schema, dict):
        return False
    if "type" not in tool_schema or tool_schema["type"] != "function":
        return False
    if "function" not in tool_schema or not isinstance(tool_schema["function"], dict):
        return False
    
    function = tool_schema["function"]
    if "name" not in function or not isinstance(function["name"], str):
        return False
    if "description" not in function or not isinstance(function["description"], str):
        return False
    if "parameters" not in function or not isinstance(function["parameters"], dict):
        return False
    
    params = function["parameters"]
    if "type" not in params or params["type"] != "object":
        return False
    if "properties" not in params or not isinstance(params["properties"], dict):
        return False
    
    if "required" in params and not isinstance(params["required"], list):
        return False
    
    return True


# **************************************************************************
# Functions to parse dataclasses and create OpenAI formatted output JSON ***
# **************************************************************************
import json
from typing import get_type_hints, Union, get_args, get_origin, List, Optional
from dataclasses import fields, is_dataclass

def is_optional_type(t):
    return get_origin(t) is Union and type(None) in get_args(t)

def unwrap_optional(t):
    if is_optional_type(t):
        return [arg for arg in get_args(t) if arg is not type(None)][0]
    return t
    
def python_type_to_openai(t, metadata=None):
    origin = get_origin(t)
    args = get_args(t)
    metadata = metadata or {}

    if is_optional_type(t):
        return python_type_to_openai(unwrap_optional(t), metadata)

    if origin in (list, List):
        item_type = args[0] if args else str
        schema = {
            "type": "array",
            "items": {
                "type": python_type_to_openai(item_type)
            }
        }
        for key in ["minItems", "maxItems", "uniqueItems"]:
            if key in metadata:
                schema[key] = metadata[key]
        return schema

    if t is str:
        return "string"
    elif t is int:
        return "integer"
    elif t is float:
        return "number"
    elif t is bool:
        return "boolean"
    elif is_dataclass(t):
        return dataclass_to_openai_schema(t)
    else:
        return "string"

def dataclass_to_openai_schema(cls):
    props = {}
    required = []

    type_hints = get_type_hints(cls)

    for f in fields(cls):
        field_type = type_hints.get(f.name, str)
        description = f.metadata.get("description", "")
        json_type = python_type_to_openai(field_type, f.metadata)

        if isinstance(json_type, str):
            prop = {"type": json_type}
        else:
            prop = json_type

        if description:
            prop["description"] = description

        props[f.name] = prop

        # Only required if not Optional
        if not is_optional_type(field_type):
            required.append(f.name)

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "risposta",
            "strict": "true",
            "schema": {
                "type": "object",
                "properties": props,
                "required": required,
            }
        }
    }

    return schema


# ****************
# Main classes ***
# ****************

from openai import OpenAI
from IPython.display import Markdown, display
from agenttools import _exec_tool

def format_json(tool_schema: Dict[str, Any], indent: int = 2) -> str:
    return json.dumps(tool_schema, indent=indent)

base_url = "http://localhost:1234/v1"
model = "gemma3:4b"

class Context:
    def __init__(self, output_channel: str="stream", output_format: str="markdown"):
        self.output_channel = output_channel # output_channel cases: silent, standard, stream
        self.output_format = output_format # output_format cases: plaintext, markdown
        self.team = []
        self.conversation = []
        self.current_agent = None

    def _print(self, text: str):
        if self.output_format == "markdown":
            display(Markdown(f"---\n**{self.current_agent.name}**: {text}")) # type: ignore
        else:
            print(f"---\n[{self.current_agent.name}]: {text}") # type: ignore

    def _stream(self, response):
        result = ""
        buffer = ""
        for text in self.conversation:
            if text["role"] == "assistant":
                buffer += f"---\n**{text['agentname']}**: {text['content']}\n\n"
        buffer += f"---\n**{self.current_agent.name}**: " # type: ignore
        for chunk in response:
            text = chunk.choices[0].delta
            if hasattr(text, 'content') and text.content:
                result += text.content
                buffer += text.content
                if self.output_format == "markdown":
                    display(Markdown(buffer), clear=True)
                else:
                    print(text.content, end='', flush=True)
        return result

class MyAgent:
    def __init__(self, name: str, context: Context,
                 base_url: str=base_url, model: str=model,
                 response_format: dict={}, tools: list=[],
                 role_and_skills: str="", max_tokens: int=-1, temperature: float=0.7):
        self.name = name
        self.context = context
        self.response_format = response_format
        self.client = OpenAI(base_url=base_url)
        self.model = model
        self.role_and_skills = role_and_skills
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.tools = tools
        self.tool_names = ", ".join([tool.__name__ for tool in tools])
        self.tool_schemas = []
        for tool in tools:
            self.tool_schemas.append(parse_docstring_for_openai_tools(tool))
        self.system_message = {"role": "system", "content": self.role_and_skills}
        self.context.team.append(self)

    def do(self, user_request: str=""):
        self.context.current_agent = self # type: ignore
        messages=[self.system_message]
        if self.context.conversation:
            messages += self.context.conversation
        if user_request:
            messages.append({"role": "user", "content": user_request})
            self.context.conversation.append({"role": "user", "content": user_request})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages, # type: ignore
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=self.context.output_channel == "stream" and not self.tools,
            **({"response_format": self.response_format} if self.response_format else {}), # type: ignore
            tools=self.tool_schemas if self.tools else [] # type: ignore
        )
        if self.tool_schemas:
            tool_call_result = _exec_tool(response)
            result = tool_call_result["result"]
            if self.context.output_channel != "silent": self.context._print(result)
        else:
            if self.context.output_channel == "stream":
                result = self.context._stream(response)
            else:
                result = response.choices[0].message.content
                if self.context.output_channel != "silent": self.context._print(result)
        self.context.conversation.append({"role": "assistant", "agentname": self.name, "content": str(result)}) # str() to avoid JSON serialization issues
