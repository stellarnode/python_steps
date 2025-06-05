# model_params.py
import openai
import logging
from config import OPENAI_API_KEY
from config import DEEPSEEK_API_KEY
from config import XAI_API_KEY
from config import ANTHROPIC_API_KEY
from config import MODEL_TO_USE  # Import the model selection


# Set up OpenAI
# openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

def get_model_params(model=MODEL_TO_USE):
    """
    Returns the model parameters based on the selected model.
    
    Args:
        model (str): The model to use, either 'gpt' for OpenAI or 'deepseek' for DeepSeek.
    
    Returns:
        dict: A dictionary containing the model parameters.

        Cost is indicated in USD per 100K tokens.
    """
    if "gpt" in model.lower():
        logger.info(f"Using OpenAI {model} model.")
        return {
            "tokens_per_chunk": 100000,
            "max_chunks_allowed": 4,
            "max_tokens": 1024,
            "model": model or "gpt-4o-mini",
            "client": openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1"),
            "cost_per_100k_tokens_input": 0.25,
            "cost_per_100k_tokens_output": 1  # Example cost, adjust as needed
        }
    elif "deepseek" in model.lower():
        logger.info(f"Using DeepSeek {model}.")
        return {
            "tokens_per_chunk": 64000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "deepseek-chat",
            "client": openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"),
            "cost_per_100k_tokens_input": 0.027,
            "cost_per_100k_tokens_output": 0.11
        }
    elif "grok" in model.lower():
        logger.info(f"Using xAI Grok {model}.")
        return {
            "tokens_per_chunk": 100000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "grok-3-mini",
            "client": openai.OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1"),
            "cost_per_100k_tokens_input": 0.3,
            "cost_per_100k_tokens_output": 1.5
        }
    elif "claude" in model.lower():
        logger.info(f"Using Anthropic's Claude {model}.")
        return {
            "tokens_per_chunk": 180000,
            "max_chunks_allowed": 3,
            "max_tokens": 1024,
            "model": model or "claude-3-haiku-20240307",
            "client": openai.OpenAI(api_key=ANTHROPIC_API_KEY, base_url="https://api.anthropic.com/v1/"),
            "cost_per_100k_tokens_input": 0.25,
            "cost_per_100k_tokens_output": 1.5
        } 
    else:
        logger.error("Invalid model selection in config. Please select 'gpt' for OpenAI or 'deepseek' for DeepSeek.")
        logger.warning("Falling back to DeepSeek model as default.")
        return {
            "tokens_per_chunk": 64000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "deepseek-chat",
            "client": openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"),
            "cost_per_100k_tokens_input": 0.3,
            "cost_per_100k_tokens_output": 1.5
        }
    
