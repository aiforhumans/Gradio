import gradio as gr
import random
import time
import os
import logging
from openai import OpenAI

# Enable Gradio logging
logging.basicConfig(level=logging.INFO)
gr.set_static_paths(paths=[])


def user(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """Append the user's message to history and clear the textbox."""
    return "", history + [{"role": "user", "content": user_message}]


def bot(history: list[dict]):
    """Stream DMR assistant reply using OpenAI SDK."""
    try:
        # Get settings from environment variables
        base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:12434/engines/v1")
        api_key = os.getenv("OPENAI_API_KEY", "dmr")
        model = os.getenv("OPENAI_MODEL", "ai/gemma3")
        
        # Initialize OpenAI client for DMR
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Start with empty assistant message
        history.append({"role": "assistant", "content": ""})
        
        # Prepare messages for API call (exclude the empty assistant message)
        # Ensure content is always a string and validate message structure
        messages = []
        for msg in history[:-1]:
            if msg.get("role") in ["user", "assistant", "system"] and msg.get("content"):
                # Ensure content is a string
                content = str(msg["content"]).strip()
                if content:  # Only add non-empty messages
                    messages.append({
                        "role": msg["role"],
                        "content": content
                    })
        
        # If no valid messages, add a default user message
        if not messages:
            messages = [{"role": "user", "content": "Hello"}]
        
        # Stream response from DMR with additional parameters for compatibility
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            stream=True,
            temperature=0.7,
            max_tokens=2048
        )
        
        for chunk in response:
            try:
                # Check if chunk has choices and the first choice has delta
                if (hasattr(chunk, 'choices') and 
                    len(chunk.choices) > 0 and 
                    hasattr(chunk.choices[0], 'delta') and 
                    hasattr(chunk.choices[0].delta, 'content') and 
                    chunk.choices[0].delta.content is not None):
                    
                    content = chunk.choices[0].delta.content
                    history[-1]["content"] += content
                    yield history
            except (IndexError, AttributeError) as chunk_error:
                # Skip malformed chunks but continue processing
                print(f"Skipping malformed chunk: {chunk_error}")
                continue
                
    except Exception as e:
        # Fallback to error message
        if len(history) == 0 or history[-1].get("role") != "assistant":
            history.append({"role": "assistant", "content": ""})
        history[-1]["content"] = f"Error connecting to DMR: {str(e)}"
        yield history


def save_settings(base_url, api_key, model):
    """Save settings to environment variables."""
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_MODEL"] = model
    return "Settings saved!"


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
        return gr.Dropdown(choices=model_names, value=model_names[0] if model_names else "ai/gemma3")
    except Exception as e:
        print(f"Error fetching models: {e}")
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