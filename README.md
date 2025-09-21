# Gradio Chat with Docker Model Runner (DMR)

A modern chat interface built with Gradio that connects to Docker Model Runner (DMR) using Pydantic AI for type-safe, structured responses. Features real-time streaming, dynamic model selection, and robust error handling.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Gradio](https://img.shields.io/badge/gradio-latest-orange)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-latest-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- 🚀 **Real-time Streaming**: Character-by-character response streaming for better UX
- 🎯 **Type-safe AI**: Pydantic AI integration with structured output validation
- 🔄 **Dynamic Models**: Live model selection from DMR with automatic refresh
- ⚙️ **Live Configuration**: Runtime settings changes without restart
- 🛡️ **Robust Error Handling**: Graceful fallbacks that never crash the interface
- 📱 **Modern UI**: Clean tabbed interface with responsive design
- 🐳 **Docker Ready**: Compatible with Docker Model Runner ecosystem

## Quick Start

### Prerequisites

- Python 3.8+
- Docker Model Runner (DMR) running on `localhost:12434`
- Or any OpenAI-compatible API endpoint

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/aiforhumans/Gradio.git
   cd Gradio
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://127.0.0.1:7861`

## Architecture

### Core Components

- **`app.py`** - Main application with Gradio interface and DMR integration
- **Chat Tab** - Streaming chat interface with message history
- **Settings Tab** - Live configuration for API endpoints and models
- **Pydantic AI Agent** - Type-safe AI responses with structured output validation

### Data Flow

```
User Input → user() → bot() → Pydantic AI Agent → DMR → Structured Response → Character Streaming → UI Update
```

### Key Technologies

- **[Gradio](https://gradio.app/)** - Web interface framework
- **[Pydantic AI](https://ai.pydantic.dev/)** - Type-safe AI framework
- **[Docker Model Runner](https://github.com/docker/model-runner)** - Local AI model hosting
- **OpenAI SDK** - API communication layer

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_BASE_URL` | `http://localhost:12434/engines/v1` | DMR API endpoint |
| `OPENAI_API_KEY` | `dmr` | API key (any string for DMR) |
| `OPENAI_MODEL` | `ai/gemma3` | Model identifier |

### Supported Models

DMR models with `ai/` prefix:
- `ai/gemma3` - Google Gemma 3 (default)
- `ai/qwen2.5` - Alibaba Qwen 2.5
- `ai/smollm2` - Small Language Model v2
- `ai/llama3.2` - Meta Llama 3.2

## Usage

### Basic Chat

1. Open the **Chat** tab
2. Type your message in the text box
3. Press Enter or click Send
4. Watch the AI response stream in real-time

### Configuration Changes

1. Switch to the **Settings** tab
2. Update API endpoint, key, or model
3. Click **🔄 Refresh Models** to fetch available models
4. Click **Save Settings** to apply changes
5. Return to Chat tab - settings are active immediately

### Code Examples

#### Custom Pydantic AI Agent

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIProvider
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    message: str = Field(description="The response message")
    confidence: float = Field(description="Response confidence")

def create_custom_agent():
    provider = OpenAIProvider(
        api_key="dmr",
        base_url="http://localhost:12434/engines/v1"
    )
    
    return Agent(
        model=provider.get_model("ai/gemma3"),
        result_type=ChatResponse,
        system_prompt="You are a helpful assistant that provides confident responses."
    )
```

#### Streaming Implementation

```python
def bot_with_streaming(history: list[dict]):
    agent = create_dmr_agent()
    result = agent.run_sync(user_message)
    
    response_text = result.output.message
    for i in range(len(response_text)):
        history[-1]["content"] = response_text[:i+1]
        yield history
        time.sleep(0.01)
```

## Development

### Project Structure

```
c:\Gradio\
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .github/
│   └── copilot-instructions.md  # AI development guide
└── guides/               # Gradio documentation
    ├── README.md
    ├── 01_getting-started/
    ├── 02_building-interfaces/
    └── ...
```

### Running in Development

```bash
# Install in development mode
pip install -r requirements.txt

# Run with debug logging
python app.py

# The app will reload automatically on file changes
```

### Docker Model Runner Setup

```bash
# Pull and run DMR (example)
docker run -d -p 12434:8000 \
  --name model-runner \
  docker/model-runner:latest

# Verify DMR is running
curl http://localhost:12434/v1/models
```

## API Integration

### DMR Endpoints

- **Models**: `GET /v1/models` - List available models
- **Chat**: `POST /v1/chat/completions` - Chat completions (OpenAI-compatible)
- **Health**: `GET /health` - Service health check

### Custom Endpoints

The application can work with any OpenAI-compatible API:

```python
# Configure for OpenAI
os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
os.environ["OPENAI_API_KEY"] = "your-openai-key"
os.environ["OPENAI_MODEL"] = "gpt-4"

# Configure for local Ollama
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_MODEL"] = "llama3.2"
```

## Troubleshooting

### Common Issues

**DMR Connection Failed**
```bash
# Check if DMR is running
curl http://localhost:12434/health

# Check available models
curl http://localhost:12434/v1/models
```

**Model Not Found**
- Use the 🔄 Refresh Models button in Settings
- Verify model name uses `ai/` prefix for DMR
- Check DMR logs for model loading errors

**Streaming Issues**
- Ensure `demo.queue().launch()` is used
- Check browser console for WebSocket errors
- Verify no firewall blocking port 7861

**Pydantic AI Errors**
- Check terminal logs for validation errors
- Verify structured response format matches `ChatResponse` model
- Ensure DMR returns valid JSON responses

### Debug Mode

Enable detailed logging:

```bash
# Set environment variable
export GRADIO_LOG_LEVEL=DEBUG

# Or in Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing patterns
4. Test with DMR integration
5. Update documentation if needed
6. Submit a pull request

### Code Style

- Follow existing Pydantic AI patterns
- Use type hints for all functions
- Include error handling for external API calls
- Maintain streaming response patterns
- Update copilot instructions for significant changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Gradio](https://gradio.app/) for the excellent web framework
- [Pydantic AI](https://ai.pydantic.dev/) for type-safe AI interactions
- [Docker Model Runner](https://github.com/docker/model-runner) for local AI hosting
- The open-source AI community for model development

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [copilot instructions](.github/copilot-instructions.md)
3. Search existing issues in the repository
4. Create a new issue with detailed information

---

**Made with ❤️ using Gradio + Pydantic AI + DMR**