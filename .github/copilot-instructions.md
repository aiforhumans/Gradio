# Copilot Instructions for this Repo

This repo contains a minimal Gradio chat app with two ways to run it: (a) a toy streaming chatbot in `app.py`, and (b) an Agents UI (`agents/ui.py`) that routes messages to pluggable agents like Echo and a local DMR-backed LLM. Keep changes small, runnable, and verified.

## Architecture & Layout
- `app.py` — self-contained demo using `gr.Blocks` + `gr.Chatbot(type="messages")`. It streams characters from a random reply via a generator function and calls `demo.launch()` at the bottom.
- `agents/ui.py` — reusable Blocks UI (not launched on import) with an Agent dropdown, `Chatbot(type="messages")`, and a `chat_response` router that calls the selected agent.
- `agents/__init__.py` — central registry: `AGENTS = {"Echo": echo.respond, "DMR Chat": dmr_chat.respond}`.
- `agents/echo.py` — offline echo agent: `def respond(message: str, history: list[dict]) -> str` returns the message.
- `agents/dmr_chat.py` — OpenAI SDK client pointed at DMR; env-configurable (`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`). Sends `history + latest user` to `chat.completions.create()` and returns the model message; exceptions are caught and returned as a friendly `"Error: ..."` string.
- `requirements.txt` — deps: `gradio`, `openai`.
- `guides/` — upstream Gradio docs index; useful references, not required by the app.

Data flow (Agents UI)
User → `(message, history)` → `chat_response()` → `AGENTS[agent_name](message, history)` → string reply → appended/rendered in `gr.Chatbot`.

## Conventions & Patterns
- Always use `type="messages"` for chat UIs; history items are `{ "role": "user"|"assistant", "content": str }`.
- Agent contract: `respond(message: str, history: list[dict]) -> str`.
- Streaming pattern: yield incremental histories (see `app.py`'s `bot()`); non-streaming agents return a final string.
- Queueing is optional here; enable `.queue()` for long/parallel LLM calls when you wire up a launcher (not used in current files).

## Developer Workflows (Windows PowerShell)
- Python 3.11+ recommended. Create venv and install deps, then run the toy demo:
  - `python app.py`
- Launch the Agents UI without editing files:
  - `python -c "from agents.ui import demo; demo.launch()"`
- Bind host/port explicitly if needed:
  - `$env:GRADIO_SERVER_NAME = '127.0.0.1'`; optionally `$env:GRADIO_SERVER_PORT = '7860'`.
- Configure DMR via env vars (defaults in `agents/dmr_chat.py`):
  - `$env:OPENAI_BASE_URL = 'http://localhost:12434/engines/v1'`
  - `$env:OPENAI_API_KEY = 'dmr'`
  - `$env:OPENAI_MODEL = 'ai/gemma3'`

## Add a New Agent (example)
1) Create `agents/my_agent.py` with `def respond(message: str, history: list[dict]) -> str: ...`
2) Register in `agents/__init__.py`: `AGENTS["My Agent"] = my_agent.respond`
3) It appears in the dropdown in `agents/ui.py` automatically.

## Guardrails
- Keep modules importable; only call `.launch()` in a runner (e.g., `app.py` or a `python -c` one-liner). Avoid side-effects on import.
- Add dependencies via `requirements.txt` only. Keep PRs minimal and runnable.

## Troubleshooting
- If `python app.py` exits quickly with code 1, it’s often an interrupted foreground run. Re-run and check PowerShell env vars.
- If DMR isn’t running on `:12434`, `DMR Chat` will return an `Error: ...` string in the chat instead of crashing the UI.

Questions or gaps? Open an issue and propose a tiny change set to evolve these rules.