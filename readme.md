## Un esempio (semplice e per scopo didattico) di framework per architetture multi-agente

_Luca Mari, 20 maggio 2025_

> Da installare:
> * (uso di base) `openai` `openai_functools` `markdown`
> * (per accesso a strumenti) `duckduckgo_search` `python-pptx` `beautifulsoup4`
>
> Configurato per funzionare con modelli di linguaggio nella situazione più semplice possibile, dunque accedendo a un modello di linguaggio locale accessibile via l'API di OpenAI con `base_url = "http://localhost:1234/v1"` all'endpoint `v1/chat/completions`, per come esposto per esempio da LM Studio oppure Ollama.

Questo framework mira a essere il più semplice possibile (è solo necessario istanziare oggetti delle classi `Context` e `MyAgent`), e ha lo scopo di essere usato per sperimentare architetture multiagente e in particolare le logiche dell'orchestrazione tra agenti. Dato questo obiettivo di semplicità, non c'è in pratica gestione degli errori, e richieste non corrette vengono solitamente ignorate.

Il nucleo del framework è la classe `MyAgent`, con un solo metodo `do()`, e in grado di gestire:
* output standard o in streaming (`Context.output_channel`: `silent`, `standard` (default), oppure `stream`), con testo non formattato o markdown (`Context.output_format`: `plaintext` (default) oppure `markdown`);
* output strutturato (_structured output_: https://platform.openai.com/docs/guides/structured-outputs), per l'agente o le singole richieste: vedi gli esempi in `agentformats.py`, dove aggiungere nuove classi;
* il riferimento a funzioni da eseguire (_function calling_: https://platform.openai.com/docs/guides/function-calling, in accordo all'endpoint `Chat Completion`: si vedano gli esempi in `agenttools.py`, dove è possibile aggiungere liberamente nuove funzioni); il parametro `tool_handling` consente di specificare se il modello di linguaggio deve operare solo come traduttore dalla richiesta dell'utente a un JSON (`schema`), se il framework deve anche eseguire le funzioni identificate e restituire il risultato (`standard`), o se il framework deve infine chiamare nuovamente il modello e fargli produrre una risposta in linguaggio naturale (`expanded`).

La classe `MyManager`, che eredita da `MyAgent` (i manager sono anch'essi agenti...) gestisce:
* casi semplici di orchestrazione, mediante `manager.sequence([azione1, azione2, ...])`, dove ogni azione può essere:
    * una coppia `(agente, richiesta)`
    * una coppia `(agente, [richiesta1, richiesta2, ...])`
    * una tripla `(agente, richiesta, {"action": "loop", "count": numero})`
    * una tripla `(agente, richiesta, {"action": "loop", "data": "last_result"})`
    * una tripla `(agente, richiesta, {"action": "loop", "data": lista})`
* casi più complessi di orchestrazione, mediante `manager.round_robin(richiesta, involved_agents=[...], max_rounds=...)` (ancora sperimentale)  
(_metodi per altre strategie da costruire_)

Gli esempi di uso di questo framework sono nei notebook `agents*.ipynb`, e sono stati tutti provati con i modelli `gemma-3-4b-it-Q4_K_M.gguf` o `qwen3-4b-Q4_K_M.gguf` con LM Studio (ma per questi modelli al momento Ollama non gestisce la chiamata a funzioni):
* `agents.ipynb`: esempi in cui ogni agente è chiamato esplicitamente nella sequenza richiesta, senza o con output strutturato e senza o con chiamata a funzioni;
* `agents2.ipynb`: esempi di "orchestrazione algoritmica", in cui la sequenza con cui gli agenti sono chiamati è ancora predeterminata ma può contenere dei loop;
* `agents3.ipynb`: esempi di "orchestrazione flessibile", con un agente manager che controlla le chiamate agli altri agenti.

---

20 maggio: gestione del parametro `tool_handling`.

29 aprile: migliorata la gestione dei parametri di default per la connessione a un modello locale; refactoring vario.

28 aprile: gestione dell'overriding della specifica di output strutturato; gestione della validazione del formato della risposta nel caso di output strutturato; gestione di chiamate ripetute a funzioni in una stessa richiesta al modello; refactoring vario.

26 aprile: gestione del debug; refactoring vario.
