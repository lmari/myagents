## Un esempio (semplice e per scopo didattico) di framework per architetture multi-agente

_Luca Mari, aprile 2025_

Da installare:
* (base) `openai` `markdown`
* (strumenti) `duckduckgo_search` `python-pptx` `beautifulsoup4`

Configurato per accedere a un modello di linguaggio accessibile via l'API di OpenAI con `base_url = "http://localhost:1234/v1"` all'endpoint `v1/chat/completions` (esposto per esempio da LM Studio).

Lo scopo di questo framework è di essere il più semplice possibile, sia da usare per creare architetture multiagente (è solo necessario istanziare oggetti delle classi `Context` e `MyAgent`) sia da comprendere nella sua logica (le parti più complesse sono forse quelle per leggere le _docstrings_ delle funzioni da trattare come strumenti e per leggere le _dataclasses_ che specificano i formati di output, e creare i corrispondenti JSON in formato OpenAI: entrambe sono utili ma non rilevanti per comprendere la logica del framework).
Dato questo obiettivo di semplicità, non c'è in pratica gestione degli errori, e richieste non corrette vengono solitamente ignorate.

Gestisce output standard o in streaming (`Context.output_channel`), con testo non formattato o markdown (`Context.output_format`).

Gestisce output formattato (via `@dataclass`: vedi gli esempi in `agentformats.py`, dove aggiungere nuove classi) e chiamata a funzioni (vedi gli esempi in `agenttools.py`, dove aggiungere nuove funzioni).

Gestisce casi semplici di orchestrazione, per ora solo di tipo deterministico (via oggetti della classe `MyManager`): `manager.sequence([azione1, azione2, ...])`, dove ogni azione può essere:
* una coppia `(agente, richiesta)`
* una coppia `(agente, [richiesta1, richiesta2, ...])`
* una tripla `(agente, richiesta, {"action": "loop", "count": numero})`
* una tripla `(agente, richiesta, {"action": "loop", "data": "last_result"})`
* una tripla `(agente, richiesta, {"action": "loop", "data": lista})`

Il notebook `agents.ipynb` contiene vari esempi di uso di base, realizzati con il modello `gemma-3-4b-it-Q4_K_M.gguf`. Il notebook `agents2.ipynb` contiene vari esempi di uso orchestrato, realizzati con lo stesso modello.
