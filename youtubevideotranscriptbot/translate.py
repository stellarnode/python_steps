# translate.py
from deep_translator import GoogleTranslator
import logging
import time

logger = logging.getLogger(__name__)

# Normalize language codes (e.g., "en-US" -> "en")
def normalize_language_code(language_code):
    """
    Normalize the language code by converting it to a two-letter code.
    Example: "en-US" -> "en", "zh-CN" -> "zh".
    """
    # Split on hyphen and take the first part
    return language_code.split('-')[0]

# Split text into chunks of approximately 4000 characters without breaking words
def split_text(text, chunk_size=2000):
    """
    Split the text into chunks of approximately 4000 characters without breaking words.
    """
    # chunks = []
    # current_chunk = ""
    # words = text.split()

    # for word in words:
    #     if len(current_chunk) + len(word) + 1 <= chunk_size:
    #         current_chunk += word + " "
    #     else:
    #         if current_chunk:
    #             chunks.append(current_chunk.strip())
    #         current_chunk = word + " "
    
    # if current_chunk:
    #     chunks.append(current_chunk.strip())
    
    # return chunks

    chunks = []
    while len(text) > chunk_size:
        # Find the last space within the max_length limit
        split_at = text.rfind(' ', 0, chunk_size)
        if split_at == -1:
            # If no space is found, split at max_length
            split_at = chunk_size
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()  # Remove leading whitespace from the remaining text
    chunks.append(text)
    return chunks


# Translate text in chunks to handle large inputs
def translate_text(text, src_lang='auto', dest_lang='en', max_retries=3):
    """
    Translate text from the source language to the target language.

    Args:
        text (str): The text to translate.
        src_lang (str): The source language code (e.g., "en").
        dest_lang (str): The target language code (e.g., "ru").
        max_retries (int): The maximum number of retries for translation.

    Returns:
        translated_text (str): The translated text.
    """
    try:
        # Normalize source and destination language codes
        src_lang = normalize_language_code(src_lang)
        dest_lang = normalize_language_code(dest_lang)
        
        # Split text into chunks without breaking words
        chunks = split_text(text)
        
        # Translate each chunk and combine the results
        translated_chunks = []
        for chunk in chunks:
            retries = 0
            while retries < max_retries:
                try:
                    logger.info(f"Attempting to translate chunk from '{src_lang}' to '{dest_lang}'")
                    translated = GoogleTranslator(source=src_lang, target=dest_lang).translate(chunk)
                    translated_chunks.append(translated)
                    break  # Exit the retry loop on success
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Translation failed after {max_retries} retries: {src_lang} --> {dest_lang}: {e}")
                        return None
                    logger.warning(f"Retrying translation ({retries}/{max_retries}): {src_lang} --> {dest_lang}")
                    time.sleep(2)  # Wait before retrying
        
        return " ".join(translated_chunks)
    except Exception as e:
        logger.error(f"Translation failed: {src_lang} --> {dest_lang}: {e}")
        return None