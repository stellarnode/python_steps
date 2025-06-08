# utils.py
import openai
import logging
from config import MODEL_TO_USE
import tiktoken
import math
import asyncio
import re

logger = logging.getLogger(__name__)

def get_token_count(text, model="gpt-3.5-turbo"):
    """
    Get the token count for a given text using the specified model.
    """
    try:
        # Load the encoding for the model you're using (e.g., gpt-3.5-turbo)
        encoding = tiktoken.encoding_for_model(model)
        # Count tokens
        token_count = len(encoding.encode(text))
        logger.info(f"Token count submitted: {token_count}")
        return token_count
    except Exception as e:
        logger.error(f"Token count failed for {model}: {e}")
        logger.warning("Falling back to default token count reference gpt-3.5-turbo.")
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            token_count = len(encoding.encode(text))
            logger.info(f"Token count for submitted text (fallback): {token_count}")
            return token_count
        except Exception as e:
            logger.error(f"Token count fallback failed for default gpt-3.5-turbo reference: {e}")
        raise

# Sanitize filename
def sanitize_filename(filename):
    """
    Sanitize the filename by replacing invalid characters with underscores.
    """
    sanitized = re.sub(r'[\\/*?:"<>| ]', '_', filename)
    sanitized = sanitized.strip('_')
    return sanitized