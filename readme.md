## Un esempio (semplice e per scopo didattico) di framework per architetture multi-agente

_Luca Mari, aprile 2025_

Da installare:
* (base) `openai` `markdown`
* (strumenti) `duckduckgo_search` `python-pptx` `beautifulsoup4`

Configurato per accedere a un modello di linguaggio accessibile via l'API di OpenAI con `base_url = "http://localhost:1234/v1"` all'endpoint `v1/chat/completions` (esposto per esempio da LM Studio).

Gestisce output standard o in streaming (`Context.output_channel`), con testo non formattato o markdown (`Context.output_format`).

Gestisce output formattato (via `@dataclass`: vedi gli esempi in `agentformats.py`, dove aggiungere nuove classi) e chiamata a funzioni (vedi gli esempi in `agenttools.py`, dove aggiungere nuove funzioni).

Il notebook `agents.ipynb` contiene vari esempi di uso, realizzati con il modello `gemma-3-4b-it-Q4_K_M.gguf`.
