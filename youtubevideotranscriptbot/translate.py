# translate.py
from deep_translator import GoogleTranslator
import logging
import time
import openai
import asyncio
from model_params import get_model_params
from utils import get_token_count
from config import MODEL_TO_USE  # Import the model selection
import math

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


async def translate_chunk(chunk, src_lang='auto', dest_lang='en', max_retries=3, model_params=None):
    if model_params:
        logger.info(f"Using model: {model_params['model']} for translation of a chunk.")
        try:
            # Define the prompt for summarization
            system_role = "You are a professional translator of video transcripts and texts from and into various languages."
            if src_lang == 'auto':
                prompt = (
                    f"Provide full translation of the following text into language '{dest_lang}':\n\n{chunk}"
                )
            else:
                prompt = (
                    f"Provide full translation of the following text from '{src_lang}' to '{dest_lang}':\n\n{chunk}"
                )

            response = model_params["client"].chat.completions.create(
                    model=model_params["model"],
                    messages=[
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": prompt},
                ],
                    temperature=0.5,
                    stream=False
                )

            # Access the response attributes correctly
            translation = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            estimated_cost = (tokens_used / 100000) * model_params["cost_per_100k_tokens_output"]  # Adjust based on DeepSeek pricing
            word_count = len(translation.split())
            logger.info(f"Translation successful for a chunk: {word_count} words, {tokens_used} tokens, cost: ${estimated_cost:.2f}")
            return translation, tokens_used, estimated_cost, word_count

        except Exception as e:
            logger.error(f"Translation failed for chunk: {e}")
            raise
    else:
        logger.warning("Model parameters are not provided for translation. Defaulting to Google Translator.")

        try:
            retries = 0
            while retries < max_retries:
                try:
                    logger.info(f"Attempting to translate chunk from '{src_lang}' to '{dest_lang}'")
                    translated = GoogleTranslator(source=src_lang, target=dest_lang).translate(chunk)
                    break  # Exit the retry loop on success
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Translation failed after {max_retries} retries: {src_lang} --> {dest_lang}: {e}")
                        return None
                    logger.warning(f"Retrying translation ({retries}/{max_retries}): {src_lang} --> {dest_lang}")
                    time.sleep(2)  # Wait before retrying
            
            return translated, 0, 0.0, len(translated.split())
        except Exception as e:
            logger.error(f"Translation failed: {src_lang} --> {dest_lang}: {e}")
            return None


# Translate text in chunks to handle large inputs
async def translate_text(text, src_lang='auto', dest_lang='en', max_retries=3, model_params=None):
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
    logger.info(f"Original text length: {len(text.split())} words.")

    # Attempt translation with an LLM model
    # model_params = get_model_params(MODEL_TO_USE)

    src_lang = normalize_language_code(src_lang)
    dest_lang = normalize_language_code(dest_lang)

    if model_params:
        tokens_per_chunk, max_chunks_allowed, max_tokens, model, client, cost_input, cost_output = model_params.values()

        token_count = get_token_count(text, model=model)

        if token_count:
            number_of_chunks = token_count / tokens_per_chunk # 15,000 tokens per chunk for GPT-3.5-turbo
            logger.info(f"Number of chunks for summarization of the transcript: {number_of_chunks}")

        if number_of_chunks > max_chunks_allowed:
            logger.error("The transcript is too long to summarize")
            raise ValueError("The transcript is too long to summarize")

        if number_of_chunks <= 1:
            chunks = [text]
        else:
            chuck_size = math.floor(len(text) / number_of_chunks)
            chunks = split_text(text, chunk_size=chuck_size)

    else:
        model_params = None
        chunks = split_text(text)
   

    logger.info(f"Text split into {len(chunks)} chunks for translation.")

    combined_translation = ""
    total_tokens_used = 0
    if not model_params:
        total_estimated_cost = 0.0
    else:
        total_estimated_cost = token_count / 100000 * cost_input
    total_word_count = 0

    try:
        tasks = [translate_chunk(chunk, src_lang, dest_lang, max_retries=3, model_params=model_params) for chunk in chunks]
        results = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Translation failed due to: {e}")
        raise

    try:
        for translation, tokens_used, estimated_cost, word_count in results:
            combined_translation += translation + "\n\n"
            total_tokens_used += tokens_used
            total_estimated_cost += estimated_cost
            total_word_count += word_count
            logger.info(f"Translation successful: {word_count} words, {tokens_used} tokens, cost: ${estimated_cost:.2f}")
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

    logger.info(f"Translation completed for all chunks. Total word count: {total_word_count}. Total tokens used: {total_tokens_used}. Estimated cost: ${total_estimated_cost:.2f}")

    return combined_translation.strip(), total_tokens_used, total_estimated_cost, total_word_count








