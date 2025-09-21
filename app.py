import gradio as gr
import random
import time
import os
import logging
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing import Optional

# Enable Gradio logging
logging.basicConfig(level=logging.INFO)
gr.set_static_paths(paths=[])

# Pydantic models for structured responses
class ChatResponse(BaseModel):
    """Structured chat response with validation"""
    message: str = Field(..., min_length=1, description="The chat response message")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Response confidence score")
    source: str = Field(default="ai", description="Source of the response")

# Configure Pydantic AI agent for DMR integration
def create_dmr_agent():
    """Create a Pydantic AI agent configured for DMR"""
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:12434/engines/v1")
    api_key = os.getenv("OPENAI_API_KEY", "dmr")
    model_name = os.getenv("OPENAI_MODEL", "ai/gemma3")
    
    # Create OpenAI-compatible provider for DMR
    provider = OpenAIProvider(
        base_url=base_url,
        api_key=api_key
    )
    
    # Create OpenAI chat model with DMR provider
    model = OpenAIChatModel(model_name, provider=provider)
    
    # Create agent with structured output
    return Agent(
        model=model,
        output_type=ChatResponse,
        system_prompt="You are a helpful AI assistant. Provide clear, accurate responses to user questions.",
    )

agent = create_dmr_agent()


def user(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """Append the user's message to history and clear the textbox."""
    return "", history + [{"role": "user", "content": user_message}]


def bot(history: list[dict]):
    """Stream response from Pydantic AI agent with structured output and error handling"""
    if not history:
        return history
    
    try:
        # Get the last user message
        user_message = history[-1]["content"]
        
        # Add empty assistant message
        history.append({"role": "assistant", "content": ""})
        
        # Convert history to Pydantic AI message format (exclude the empty assistant message)
        conversation_history = []
        for msg in history[:-1]:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                content = str(msg["content"]).strip()
                if content:
                    conversation_history.append({
                        "role": msg["role"],
                        "content": content
                    })
        
        # Run the agent and get structured response
        try:
            # Recreate agent with current settings to pick up any configuration changes
            agent = create_dmr_agent()
            
            # Use only the latest user message for simplicity
            result = agent.run_sync(user_message)
            
            # Extract the message from the structured response
            if hasattr(result.output, 'message'):
                response_text = result.output.message
            else:
                response_text = str(result.output)
            
            # Stream the response character by character for better UX
            for i in range(len(response_text)):
                history[-1]["content"] = response_text[:i+1]
                yield history
                time.sleep(0.01)  # Small delay for streaming effect
                
        except Exception as e:
            logging.error(f"Error from Pydantic AI agent: {e}")
            error_message = f"Error from AI model: {str(e)}"
            
            # Stream error message
            for i in range(len(error_message)):
                history[-1]["content"] = error_message[:i+1]
                yield history
                time.sleep(0.01)
            
    except Exception as e:
        logging.error(f"Error in bot function: {e}")
        # Fallback to error message
        if len(history) == 0 or history[-1].get("role") != "assistant":
            history.append({"role": "assistant", "content": ""})
        history[-1]["content"] = f"Sorry, I encountered an error: {str(e)}"
        yield history


def save_settings(base_url, api_key, model):
    """Save settings to environment variables and recreate agent."""
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_MODEL"] = model
    
    # Recreate the global agent with new settings
    global agent
    agent = create_dmr_agent()
    
    return "Settings saved and agent updated!"


def get_available_models():
    """Fetch available models from DMR."""
    try:
        base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:12434/engines/v1")
        api_key = os.getenv("OPENAI_API_KEY", "dmr")
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        models = client.models.list()
        model_names = [model.id for model in models.data]
        
        # Filter for AI models (DMR typically uses ai/ prefix)
        ai_models = [name for name in model_names if name.startswith('ai/')]
        
        if ai_models:
            return gr.Dropdown(choices=ai_models, value=ai_models[0])
        else:
            return gr.Dropdown(choices=model_names, value=model_names[0] if model_names else "ai/gemma3")
            
    except Exception as e:
        logging.warning(f"Error fetching models: {e}")
        # Return default dropdown with common models
        default_models = ["ai/gemma3", "ai/qwen2.5", "ai/smollm2", "ai/llama3.2"]
        return gr.Dropdown(choices=default_models, value="ai/gemma3")


with gr.Blocks(title="DMR Chat with Gradio") as demo:
    with gr.Tabs():
        with gr.Tab("Chat"):
            chatbot = gr.Chatbot(type="messages", label="Chat", height="80vh")
            with gr.Row():
                msg = gr.Textbox(placeholder="Type a message and press Enter", scale=4)
                clear = gr.Button("Clear", scale=1)

            msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot, chatbot, chatbot
            )
            # Clear both the textbox and the chat history
            clear.click(lambda: ("", []), None, [msg, chatbot], queue=False)

        with gr.Tab("Settings"):
            gr.Markdown("Configure API settings for DMR or OpenAI.")
            base_url = gr.Textbox(label="OPENAI_BASE_URL", value=os.getenv("OPENAI_BASE_URL", "http://localhost:12434/engines/v1"))
            api_key = gr.Textbox(label="OPENAI_API_KEY", value=os.getenv("OPENAI_API_KEY", "dmr"))
            
            with gr.Row():
                model = gr.Dropdown(
                    label="OPENAI_MODEL", 
                    choices=["ai/gemma3", "ai/qwen2.5", "ai/smollm2", "ai/llama3.2"],
                    value=os.getenv("OPENAI_MODEL", "ai/gemma3"),
                    allow_custom_value=True
                )
                refresh_models = gr.Button("🔄 Refresh Models", size="sm")
            
            save_btn = gr.Button("Save Settings")
            status = gr.Textbox(label="Status", interactive=False)

            # Event handlers
            refresh_models.click(get_available_models, outputs=model)
            save_btn.click(save_settings, [base_url, api_key, model], status)


if __name__ == "__main__":
    demo.queue().launch(debug=True)