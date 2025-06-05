# summarize.py
import openai
import logging
from translate import translate_text  # Import the translation function
from translate import split_text
from model_params import get_model_params
from database import store_summarization_request_async
from utils import get_token_count
from config import OPENAI_API_KEY
from config import DEEPSEEK_API_KEY
from config import MODEL_TO_USE  # Import the model selection
import math
import asyncio

# Set up OpenAI
# openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

async def summarize_chunk(chunk, language, model=MODEL_TO_USE):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _summarize_sync, chunk, language, model)

def _summarize_sync(chunk, language, model=MODEL_TO_USE):
    """
    Synchronously summarizes a chunk of text using the OpenAI API.

    Args:
        chunk (str): A chunk of text to summarize.
        language (str): The language of the text.

    Returns:
        summary (str): The summarized text.
        tokens_used (int): The number of tokens used for the OpenAI API call.
        estimated_cost (float): The estimated cost of the OpenAI API call.
        word_count (int): The word count of the summary.
    """
    
    if not model:
        model_params = get_model_params(MODEL_TO_USE)
    else:
        model_params = get_model_params(model)
    logger.info(f"Using model: {model_params['model']} for summarization.")

    try:
        # Define the prompt for summarization
        system_role = "You are a master of extracting pearls of knowledge from YouTube video transcripts. You grasp the very essence and distill it in a concise form for users. You always provide the response in the same language in which the transcript is provided. Your answers are always clear, concise and nicely formatted."
        prompt = (
            f"If I did not have time to read this YouTube video transcript, what are the most important things I absolutely must know. Enlighten me in no more than 200 words. "
            f"Always provide your response in the same language as the transcript. In this case it might be in '{language}' language. Here is the transcript itself:\n\n{chunk}"
        )
        # prompt = (
        #     f"If I did not have time to read this YouTube video transcript, what are the most important things I absolutely must know. Enlighten me in no more than 200 words. "
        #     f"Provide your response strictly in the following language: '{language}'. Here is the transcript itself:\n\n{chunk}"
        # )

        response = model_params["client"].chat.completions.create(
                model=model_params["model"],
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt},
            ],
                max_tokens=model_params["max_tokens"],
                temperature=0.5,
                stream=False
            )

        # Access the response attributes correctly
        summary = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        estimated_cost = (tokens_used / 100000) * model_params["cost_per_100k_tokens_output"]  # Adjust based on DeepSeek pricing
        word_count = len(summary.split())

        return summary, tokens_used, estimated_cost, word_count

    except Exception as e:
        logger.error(f"Summarization failed for chunk: {e}")
        raise


# Summarize text using OpenAI GPT
async def summarize_text(text, language, model=MODEL_TO_USE, num_key_points=3):
    """
    Summarizes the given text in the specified language.

    Args:
        text (str): The original transcript (in the original language).
        language (str): The target language for the summary (e.g., 'en', 'ru').
        num_key_points (int): The number of key points to include in the summary.

    Returns:
        summary (str): The summarized text in the target language.
        tokens_used (int): The number of tokens used for the OpenAI API call.
        estimated_cost (float): The estimated cost of the OpenAI API call.
        word_count (int): The word count of the summary.
    """

    tokens_per_chunk, max_chunks_allowed, max_tokens, model, client, cost_input, cost_output = get_model_params(model).values()
    logger.info(f"Tokens per chunk: {tokens_per_chunk} of type {type(tokens_per_chunk)}")

    token_count = get_token_count(text, model=model)

    if token_count:
        number_of_chunks = token_count / int(tokens_per_chunk) # 15,000 tokens per chunk for GPT-3.5-turbo
        logger.info(f"Number of chunks for summarization of the transcript: {number_of_chunks}")

    if number_of_chunks > max_chunks_allowed:
        logger.error("The transcript is too long to summarize")
        raise ValueError("The transcript is too long to summarize")

    if number_of_chunks <= 1:
        chunks = [text]
    else:
        chuck_size = math.floor(len(text) / number_of_chunks)
        chunks = split_text(text, chunk_size=chuck_size)

    combined_summary = ""
    total_tokens_used = 0
    total_estimated_cost = token_count / 100000 * cost_input
    total_word_count = 0

    try:
        tasks = [summarize_chunk(chunk, language, model) for chunk in chunks]
        results = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Summarization process failed due to: {e}")
        raise

    try:
        for summary, tokens_used, estimated_cost, word_count in results:
            combined_summary += summary + "\n\n"
            total_tokens_used += tokens_used
            total_estimated_cost += estimated_cost
            total_word_count += word_count
            logger.info(f"Summarization successful: {word_count} words, {tokens_used} tokens, cost: ${estimated_cost:.2f}")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise

    logger.info(f"Summarization completed for all chunks. Total word count: {total_word_count}. Total tokens used: {total_tokens_used}. Estimated cost: ${total_estimated_cost:.2f}")

    return combined_summary.strip(), total_tokens_used, total_estimated_cost, total_word_count


# async def translate_summary_async(summary, src_lang, dest_lang):
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(None, translate_summary, summary, src_lang, dest_lang)

# Translate the summary into the target language
async def translate_summary(summary, src_lang, dest_lang, model=MODEL_TO_USE):
    """
    Translates the summary into the target language.

    Args:
        summary (str): The summary to translate.
        src_lang (str): The source language of the summary.
        dest_lang (str): The target language for the translation.

    Returns:
        translated_summary (str): The translated summary.
    """
    if not model:
        model_params = get_model_params(MODEL_TO_USE)
    else:
        model_params = get_model_params(model)
    logger.info(f"Using model: {model_params['model']} for summary translation.")

    try:
        translated_summary, tokens_used, estimated_cost, word_count = await translate_text(summary, src_lang=src_lang, dest_lang=dest_lang, model_params=model_params)
        if not translated_summary:
            raise Exception("Translation failed.")
        return translated_summary, tokens_used, estimated_cost, word_count
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

# Handle summarization request
async def handle_summarization_request(text, original_language, target_language, summary_properties, model=MODEL_TO_USE, num_key_points=3):
    """
    Handles the summarization request.

    Args:
        text (str): The original transcript (in the original language).
        original_language (str): The language code of the original transcript.
        target_language (str): The target language for the summary.
        num_key_points (int): The number of key points to include in the summary.

    Returns:
        summary (str): The summarized text in the target language.
        tokens_used (int): The number of tokens used for the OpenAI API call.
        estimated_cost (float): The estimated cost of the OpenAI API call.
        word_count (int): The word count of the summary.
    """

    logger.info(f"Summarization is handled for original language '{original_language}' and target '{target_language}'")

    if not model:
        model_params = get_model_params(MODEL_TO_USE)
    else:
        model_params = get_model_params(model)
    logger.info(f"Using model: {model_params['model']} for summarization.")

    try:
   
        summary, tokens_used, estimated_cost, word_count = await summarize_text(text, original_language, model_params['model'], num_key_points)
        if target_language == 'orig':
            target_language = original_language

        logger.info(f"Summary generated in requested language {target_language}. Translation skipped.")

        try:
            # Log the summarization request in the database
            await store_summarization_request_async(
                user_id=summary_properties['user_id'],
                video_id=summary_properties['video_id'],
                language=original_language,
                transcript_request_id=summary_properties['transcript_request_id'],
                tokens_used=tokens_used,
                estimated_cost=estimated_cost,
                word_count=word_count,
                status="completed",
                model=model_params['model'],
                summary=summary
            )
            logger.info(f"Summary generated in requested language {target_language} stored in DB.")
        except Exception as e:
            logger.error(f"Failed to store summarization request in the database for original language {original_language}: {e}")

        # Translate the summary if the target language is not the original language
        if target_language != original_language:
            summary, tokens_used, estimated_cost, word_count = await translate_summary(summary, src_lang=original_language, dest_lang=target_language)

            try:
                # Log the summarization request in the database
                await store_summarization_request_async(
                    user_id=summary_properties['user_id'],
                    video_id=summary_properties['video_id'],
                    language=target_language,
                    transcript_request_id=summary_properties['transcript_request_id'],
                    tokens_used=tokens_used,
                    estimated_cost=estimated_cost,
                    word_count=word_count,
                    status="completed",
                    model=model_params['model'],
                    summary=summary
                )
                logger.info(f"Summary translated into target language {target_language} stored in DB.")
            except Exception as e:
                logger.error(f"Failed to store summarization request for translation into {target_language}: {e}")

        return summary, tokens_used, estimated_cost, word_count, model_params['model']
    except Exception as e:
        logger.error(f"Failed to handle summarization request: {e}")
        raise