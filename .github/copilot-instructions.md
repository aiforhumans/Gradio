# Copilot Instructions for this Repo

This repo contains a Gradio chat application with Docker Model Runner (DMR) integration via Pydantic AI and OpenAI-compatible API. Keep edits focused, tested, and maintain the streaming chat patterns with structured output validation.

## Architecture & Data Flow

- `app.py` — Single-file Gradio app with tabbed interface (Chat + Settings) that connects to DMR via Pydantic AI agents
- **Chat Tab**: `gr.Chatbot(type="messages")` with streaming responses from DMR models using structured output
- **Settings Tab**: Dynamic model dropdown + environment variable configuration
- **Data Flow**: User message → `user()` function → `bot()` creates Pydantic AI agent → structured response → character streaming → UI updates

## Core Patterns

### Message Format
Always use `type="messages"` for chatbots. History format: `[{"role": "user|assistant|system", "content": str}, ...]`

### Pydantic AI Agent Pattern
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIProvider

class ChatResponse(BaseModel):
    message: str = Field(description="The response message to the user")

def create_dmr_agent():
    provider = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "dmr"),
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:12434/engines/v1")
    )
    
    return Agent(
        model=provider.get_model(os.getenv("OPENAI_MODEL", "ai/gemma3")),
        result_type=ChatResponse,
        system_prompt="You are a helpful AI assistant..."
    )
```

### Streaming Implementation with Structured Output
```python
def bot(history: list[dict]):
    # Add empty assistant message first
    history.append({"role": "assistant", "content": ""})
    
    # Create agent and get structured response
    agent = create_dmr_agent()
    result = agent.run_sync(user_message)
    
    # Extract message and stream character by character
    response_text = result.output.message
    for i in range(len(response_text)):
        history[-1]["content"] = response_text[:i+1]
        yield history
        time.sleep(0.01)  # Streaming effect
```

### DMR Integration
- **Base URL**: `http://localhost:12434/engines/v1` (host) or `http://model-runner.docker.internal/engines/v1` (containers)
- **API Key**: Use `"dmr"` (any non-empty string works)
- **Models**: Format `ai/model-name` (e.g., `ai/gemma3`, `ai/qwen2.5`, `ai/smollm2`, `ai/llama3.2`)
- **Provider**: OpenAIProvider abstracts DMR connection for Pydantic AI
- **Error Handling**: Robust validation with fallback to error messages instead of crashes

### Environment Configuration
Settings persist via `os.environ` and are configurable through the Settings tab:
- `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`
- Dynamic model refresh fetches available models from DMR `/models` endpoint
- Agent recreation on settings change: `save_settings()` recreates global agent

## Development Workflows

### Run & Debug
```powershell
python app.py  # Launches with debug=True and logging.INFO
```
- Terminal shows HTTP requests to DMR endpoints
- Gradio serves on `http://127.0.0.1:7861` with live reloading
- Pydantic AI validation errors appear in logs

### Key Functions
- `create_dmr_agent()` — Factory for Pydantic AI agents with current environment
- `user()` — Appends user message, clears input
- `bot()` — Creates agent, gets structured response, streams to UI
- `get_available_models()` — Fetches live models from DMR with ai/ filtering
- `save_settings()` — Persists config and recreates agent

## Structured Output Design

### ChatResponse Model
```python
class ChatResponse(BaseModel):
    message: str = Field(description="The response message to the user")
```
- Ensures type safety and validation
- Extensible for future structured features (metadata, tool calls, etc.)
- Pydantic AI automatically validates against schema

### Agent Configuration
- **Result Type**: Always use `result_type=ChatResponse` for structured output
- **System Prompt**: Configurable via agent creation
- **Model Selection**: Dynamic via OpenAIProvider.get_model()
- **Error Recovery**: Agent recreation on configuration errors

## Critical Details
- Enable queueing: `.queue().launch()` for streaming support
- Agent recreation: Always recreate agent when settings change to pick up new config
- Character streaming: Use `time.sleep(0.01)` for smooth streaming effect
- Settings changes apply immediately via environment variables + agent recreation
- Height management: `height="80vh"` keeps chat area sized properly
- Model filtering: Prefer `ai/` prefixed models for DMR compatibility

## Troubleshooting
- DMR connection errors show friendly messages in chat instead of crashing
- Model dropdown falls back to defaults if DMR unavailable
- Pydantic AI validation errors logged but don't crash the interface
- Agent recreation failures handled gracefully with error messages
- Logging enabled shows request/response flow and validation issues for debugging

## Migration Notes (from direct OpenAI SDK)
- Replace direct OpenAI client calls with Pydantic AI agents
- Add structured output models (ChatResponse) for type safety
- Use OpenAIProvider instead of direct OpenAI client initialization
- Character-based streaming replaces chunk-based streaming
- Agent recreation replaces client recreation for settings changes