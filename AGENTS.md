# AGENTS

## Runbook (verified)
- Create env and install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Optional preflight check: `python scripts/smoke_check.py` (validates `.env`, MongoDB ping, and Ollama `/api/tags`).
- Start app: `streamlit run main.py` (this is the only documented entrypoint).
- Required env vars are loaded from `.env` at import time via `Settings()`: `MONGO_DB_URL`, `MONGO_DB_NAME`, `OLLAMA_URL`, `OLLAMA_MODELS`.
- Use `env_template.txt` as the source for required keys and example values.
- Pinned dependencies in `requirements.txt`: `streamlit==1.49.1`, `ollama==0.5.3`, `llama-index==0.14.0`, `llama-index-llms-ollama==0.7.2`, `pymongo==4.14.1`, `pydantic==2.11.7`, `pydantic-settings==2.10.1`, `python-dotenv==1.1.1`.

## Minimal project shape to regenerate
- `main.py`: Streamlit UI, sidebar history, model picker, chat input/output, orchestration for DB + LLM calls.
- `config/settings.py`: `Settings(BaseSettings)` with `.env` loading (`load_dotenv()` + `env_file = ".env"`).
- `db/mongo.py`: cached `Settings()` and cached MongoDB database (`MongoClient(..., tz_aware=True)`).
- `db/conversations.py`: conversation CRUD and sorting logic.
- `llm_factory/get_llm.py`: Ollama LLM factory with module-level single-instance cache per selected model.
- `services/get_models_list.py`: parse `OLLAMA_MODELS` env string into list.
- `services/chat_utilities.py`: convert history to `ChatMessage[]` and call `llm.chat(...)`.
- `services/get_title.py`: generate conversation title from first user prompt.
- `env_template.txt`, `requirements.txt`, `README.md`.

## Input pack for zero-to-one regeneration (without copying code)
- Required instruction/context files: `AGENTS.md`, `requirements.txt`, `env_template.txt`, `README.md`.
- Rule: when regenerating from this pack, treat source files as to-be-implemented from specs in this document; do not copy old code verbatim.
- Expected outputs to implement: `main.py`, `config/settings.py`, `db/mongo.py`, `db/conversations.py`, `llm_factory/get_llm.py`, `services/get_models_list.py`, `services/chat_utilities.py`, `services/get_title.py`, `scripts/smoke_check.py`.
- Exclude from regeneration inputs: `.env`, `.venv/`, `__pycache__/`, `.ruff_cache/`, `.git/`.

<details>
<summary>Version en espanol (referencia rapida)</summary>

- **Paquete minimo de entrada (sin copiar codigo):** `AGENTS.md`, `requirements.txt`, `env_template.txt`, `README.md`.
- **Regla clave:** regenerar desde especificaciones; no copiar codigo fuente previo de forma literal.
- **Archivos que el agente debe construir:** `main.py`, `config/settings.py`, `db/mongo.py`, `db/conversations.py`, `llm_factory/get_llm.py`, `services/get_models_list.py`, `services/chat_utilities.py`, `services/get_title.py`, `scripts/smoke_check.py`.
- **Excluir de entradas:** `.env`, `.venv/`, `__pycache__/`, `.ruff_cache/`, `.git/`.

</details>

## Architecture you need before editing
- UI + orchestration is all in `main.py`; there is no separate backend server in this repo.
- Conversation persistence is MongoDB in `db/conversations.py` using collection `conversations` with `_id` as UUID string.
- Opening a conversation calls `get_conversation()` which updates `last_interacted`; just viewing a chat reorders it in sidebar history.
- LLM calls go through `llm_factory/get_llm.py` (`llama-index` Ollama client); it caches one active model instance at module scope.
- Chat responses are built in `services/chat_utilities.py` and always prepend a fixed system message.
- Model picker options come from `OLLAMA_MODELS` in `.env` (comma-separated), parsed by `services/get_models_list.py`; the app does not query Ollama for installed models.
- New conversation titles are generated from the first user prompt via `services/get_title.py`; on failure the title falls back to `New Chat`.

## Behavioral spec (regeneration-critical)
- Session state keys used by UI: `conversation_id`, `conversation_title`, `chat_history`, `OLLAMA_MODELS`.
- `chat_history` item shape in UI: `{ "role": str, "content": str }`.
- New chat flow: first user message creates conversation + title, then assistant reply is generated and persisted.
- Existing chat flow: user message is appended to current conversation, assistant reply is generated and appended.
- Sidebar history source: `get_all_conversations()` sorted by `last_interacted` descending.
- Conversation document shape in MongoDB:
  - `_id`: UUID string
  - `title`: string
  - `messages`: list of `{ role, content, ts }`
  - `last_interacted`: UTC timestamp
- DB helpers must update `last_interacted` on both message append and conversation open.

## LLM integration spec
- LLM provider is `llama_index.llms.ollama.Ollama` with `base_url=settings.OLLAMA_URL` and `model=<selected_model>`.
- Factory cache behavior: if requested model matches current cached model, return same instance.
- `services/chat_utilities.py` prepends one system prompt: `You are a helpful chat assistant.`
- Message role conversion uses `MessageRole[msg["role"].upper()]`; allowed roles must map to llama-index role enum.
- Current effective `request_timeout` is library default (30.0s) because app does not override it.

## Verification scope in this repo
- There is no repo-level test/lint/typecheck config (`pytest.ini`, `pyproject.toml`, CI workflows, Makefile, pre-commit config are absent).
- Practical verification after code changes is manual app smoke testing via `streamlit run main.py` with reachable MongoDB + Ollama.

## Regeneration harness (use this exact sequence)
- 1) Runtime sanity: `python3 --version` and ensure `3.12.x` or use an existing working `.venv` pinned to 3.12.
- 2) Recreate env: `rm -rf .venv && /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- 3) Env wiring: `cp env_template.txt .env` and set real values for `MONGO_DB_URL`, `MONGO_DB_NAME`, `OLLAMA_URL`, `OLLAMA_MODELS`.
- 4) Service reachability: confirm MongoDB and Ollama are up before launching Streamlit.
- 5) Launch: `streamlit run main.py` and execute the smoke checklist below end-to-end.

## Definition of done (hardening gate)
- App starts without import, settings, or connection tracebacks.
- New chat path works: first user prompt creates conversation, generates/fallbacks title, persists both messages.
- Existing chat path works: appending user+assistant messages updates same conversation document.
- Conversation ordering works: opening or appending moves conversation upward via `last_interacted`.
- Model picker strictly reflects `.env` `OLLAMA_MODELS` parsing (no runtime model discovery dependency).
- No secrets committed: `.env` remains local and excluded from commits manually (repo `.gitignore` does not ignore `.env`).

## Manual smoke test checklist
- Verify app boots without import/env errors.
- Verify model selectbox loads values from `.env` `OLLAMA_MODELS`.
- Create a new chat and confirm title is generated (or fallback `New Chat`).
- Send at least one turn and confirm both user+assistant messages render and persist.
- Reload app and confirm conversation appears in sidebar history.
- Open an old conversation and confirm it moves upward due to `last_interacted` update.

## Quick validation queries (Mongo harness)
- Conversation list order check: query `conversations` sorted by `last_interacted` descending; most recently opened/updated item must be first.
- Document contract check per conversation:
  - `_id` is UUID string
  - `title` is string
  - `messages` is array of `{role, content, ts}`
  - `last_interacted` is present and UTC-compatible timestamp
- Message role check: stored `role` values should stay in `user|assistant|system` to keep llama-index role mapping safe.

## Gotchas that cause avoidable failures
- If `.env` is missing keys, importing modules that instantiate `Settings()` can fail before UI renders.
- `.env` is currently not ignored by `.gitignore` in this repo; do not commit secrets accidentally.
- Message roles in `chat_history` must map to `MessageRole[...]` in `services/chat_utilities.py` (`user` / `assistant` / `system`); custom role strings will break response generation.
- After macOS/Python upgrades, old `.venv` may break; recreate with a supported Python (repo has been used with 3.12).
