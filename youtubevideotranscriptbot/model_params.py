# model_params.py
import openai
import deepseek
import logging
from config import OPENAI_API_KEY
from config import DEEPSEEK_API_KEY
from config import XAI_API_KEY
from config import ANTHROPIC_API_KEY
from config import MODEL_TO_USE  # Import the model selection
import tiktoken
import math
import asyncio

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
    """
    if "gpt" in model.lower():
        logger.info(f"Using OpenAI {model} model.")
        return {
            "tokens_per_chunk": 100000,
            "max_chunks_allowed": 4,
            "max_tokens": 1024,
            "model": model or "gpt-4o-mini",
            "client": openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1")
        }
    elif "deepseek" in model.lower():
        logger.info(f"Using DeepSeek {model}.")
        return {
            "tokens_per_chunk": 64000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "deepseek-chat",
            "client": openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        }
    elif "grok" in model.lower():
        logger.info(f"Using xAI Grok {model}.")
        return {
            "tokens_per_chunk": 100000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "grok-3-mini",
            "client": openai.OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
        }
    elif "claude" in model.lower():
        logger.info(f"Using Anthropic's Claude {model}.")
        return {
            "tokens_per_chunk": 180000,
            "max_chunks_allowed": 3,
            "max_tokens": 1024,
            "model": model or "claude-3-haiku-20240307",
            "client": openai.OpenAI(api_key=ANTHROPIC_API_KEY, base_url="https://api.anthropic.com/v1/")
        } 
    else:
        logger.error("Invalid model selection in config. Please select 'gpt' for OpenAI or 'deepseek' for DeepSeek.")
        logger.warning("Falling back to DeepSeek model as default.")
        return {
            "tokens_per_chunk": 64000,
            "max_chunks_allowed": 5,
            "max_tokens": 1024,
            "model": model or "deepseek-chat",
            "client": openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        }
    

# if MODEL_TO_USE:
#     if "gpt" in MODEL_TO_USE.lower():
#         model_to_use = 1  # OpenAI model
#     elif "deepseek" in MODEL_TO_USE.lower():
#         model_to_use = 2
#     else:
#         logger.error("Invalid model selection in config. Please select 'gpt' for OpenAI or 'deepseek' for DeepSeek.")
#         logger.warning("Falling back to DeepSeek model as default.")
#         model_to_use = 2 # 1 for OpenAI, 2 for DeepSeek
#         raise ValueError("Invalid model selection in config. Please select 'gpt' for OpenAI or 'deepseek' for DeepSeek.")

# if model_to_use == 1:
#     tokens_per_chunk = 100000
#     max_chunks_allowed = 4
#     max_tokens = 1024
#     model = "gpt-4o-mini"
#     client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1")
#     logger.info(f"Using OpenAI {model} model for summarization.")
# elif model_to_use == 2:
#     tokens_per_chunk = 64000
#     max_chunks_allowed = 5
#     max_tokens = 1024
#     model = "deepseek-chat"
#     # for DeepSeek backward compatibility, you can still use `https://api.deepseek.com/v1` as `base_url`.
#     client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
#     logger.info(f"Using DeepSeek {model} for summarization.")
# else:
#     logger.error("Invalid model selection. Please select 1 for OpenAI or 2 for DeepSeek.")