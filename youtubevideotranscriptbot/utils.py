# utils.py
import openai
import logging
from config import MODEL_TO_USE
import tiktoken
import math
import asyncio
import re

logger = logging.getLogger(__name__)

# Normalize language codes (e.g., "en-US" -> "en")
def normalize_language_code(language_code):
    # Split on hyphen and take the first part
    return language_code.split('-')[0]

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


def get_original_language(snippet, transcripts=None):
    """
    Extract the original language from video details. Accepts a snippet dictionary from the video details object and an optional list of transcripts.
    """
    original_language = None

    if not snippet:
        logger.error("Snippet is required to determine the original language. No video details snippets provided.")

    if not transcripts:
        logger.warning("No transcripts provided to determine the original language. Will attempt to extract from video details snippet.")
    
    try:
        logger.info(f"Video snippet object at this point: {snippet}")
        logger.info("Attempting to determine the original language of the video.")
        original_language = snippet.get("defaultAudioLanguage")
        if original_language:
            logger.info(f"Original audio language determined as: {original_language}")
            original_language = normalize_language_code(original_language)
        else:
            original_language = snippet.get("defaultLanguage")
            if original_language:
                original_language = normalize_language_code(original_language)
                logger.warning(f"Original video language determined as: {original_language}")
            elif transcripts:
                # Find first object with name='Alice'
                t = next((t for t in transcripts if t.get('is_generated') == True and t.get('type') == 'transcript'), None)
                original_language = t.get('normalized_language_code') if t else None
                if original_language:
                    logger.warning(f"Original video language determined as: {original_language}")
                    original_language = normalize_language_code(original_language)
                else:
                    raise ValueError("No auto-generated transcript found to determine the original language.")
            else:
                raise ValueError("No language code found in video details snippet.")
    except Exception as e:
        logger.error(f"Error determining the original language: {e}") # Get the language code of the first transcript
        logger.warning(f"Original language could not be determined. Falling back to first random or English: {original_language}")
        original_language = next(iter(transcripts)).get('language_code', 'en') 
        logger.info(f"Original language determined as: {original_language}")
    try:
        original_language = normalize_language_code(original_language)
    except:
        pass

    return original_language