# summarize.py
import openai
import deepseek
import logging
from translate import translate_text  # Import the translation function
from config import OPENAI_API_KEY
from config import DEEPSEEK_API_KEY
import tiktoken
from translate import split_text
import math

# Set up OpenAI
# openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

model_to_use = 2 # 1 for OpenAI, 2 for DeepSeek

if model_to_use == 1:
    tokens_per_chunk = 100000
    max_chunks_allowed = 4
    max_tokens = 1024
    model = "gpt-4o-mini"
    client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1")
    logger.info(f"Using OpenAI {model} model for summarization.")
elif model_to_use == 2:
    tokens_per_chunk = 64000
    max_chunks_allowed = 3
    max_tokens = 1024
    model = "deepseek-chat"
    # for DeepSeek backward compatibility, you can still use `https://api.deepseek.com/v1` as `base_url`.
    client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    logger.info(f"Using DeepSeek {model} for summarization.")
else:
    logger.error("Invalid model selection. Please select 1 for OpenAI or 2 for DeepSeek.")


# Summarize text using OpenAI GPT
def summarize_text(text, language, num_key_points=3):
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

    try:
        # Load the encoding for the model you're using (e.g., gpt-3.5-turbo)
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        # Count tokens
        token_count = len(encoding.encode(text))
        logger.info(f"Token count for transcript submitted for summarization: {token_count}")
    except Exception as e:
        logger.error(f"Token count failed: {e}")
        raise

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

    combined_summary = ""
    total_tokens_used = 0
    total_estimated_cost = 0.0
    total_word_count = 0

    for chunk in chunks:
        try:
            # Define the prompt for summarization
            system_role = "You are a master of extracting pearls of knowledge from YouTube video transcripts. You grasp the very essence and distill it in a concise form for users. You always provide the response in the same language in which the transcript is provided. Your answers are always clear, concise and nicely formatted."
            prompt = (
                f"If I did not have time to read this YouTube video transcript, what are the most important things I absolutely must know. Enlighten me in no more than 200 words. "
                f"Always provide your response in the same language as the transcript. In this case it might be in '{language}' language. Here is the transcript itself:\n\n{chunk}"
            )

            response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": prompt},
                ],
                    max_tokens=max_tokens,
                    temperature=0.5,
                    stream=False
                )

            # if model_to_use == 1:
            #     # Call the OpenAI API
            #     response = openai.ChatCompletion.create(
            #         model="gpt-3.5-turbo",
            #         messages=[
            #             {"role": "system", "content": system_role},
            #             {"role": "user", "content": prompt}
            #         ],
            #         max_tokens=500,  # Increased token limit to ensure the summary is complete
            #         temperature=0.5
            #     )
            # elif model_to_use == 2:
            #     # DeepSeek API
            #     response = client.chat.completions.create(
            #         model="deepseek-chat",
            #         messages=[
            #             {"role": "system", "content": system_role},
            #             {"role": "user", "content": prompt},
            #     ],
            #         max_tokens=1024,
            #         temperature=0.5,
            #         stream=False
            #     )

            # else:
            #     logger.error("Invalid model selection. Please select 1 for OpenAI or 2 for DeepSeek.")

            # summary = response['choices'][0]['message']['content']
            # tokens_used = response['usage']['total_tokens']
            # estimated_cost = (tokens_used / 1000) * 0.002  # Adjust based on GPT pricing
            # word_count = len(summary.split())

            # Access the response attributes correctly
            summary = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            estimated_cost = (tokens_used / 1000) * 0.002  # Adjust based on DeepSeek pricing
            word_count = len(summary.split())

            combined_summary += summary + "\n\n"
            total_tokens_used += tokens_used
            total_estimated_cost += estimated_cost
            total_word_count += word_count
            logger.info(f"Chunk summarization successful: {word_count} words, {tokens_used} tokens, cost: ${estimated_cost:.2f}")
        except Exception as e:
            logger.error(f"Summarization failed for chunk: {e}")
            raise


    logger.info(f"Summarization completed for all chunks.")

    return combined_summary.strip(), total_tokens_used, total_estimated_cost, total_word_count

    # try:
    #     # Define the prompt for summarization
    #     prompt = (
    #         f"If I did not have time to read this YouTube video transcript, what are the most important things I absolutely must know. Enlighten me in no more than 200 words. "
    #         f"Always provide your response in the same language as the transcript. In this case it might be in '{language}' language. Here is the transcript itself:\n\n{text}"
    #     )

    #     # Call the OpenAI API
    #     response = openai.ChatCompletion.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "system", "content": "You are a master of extracting pearls of knowledge from YouTube video transcripts. You grasp the very essense and distill it in a consice form for users. You always provide the response in the same language in which the transcript is provided. Your answers are always clear, consise and nicely formatted."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         max_tokens=500,  # Increased token limit to ensure the summary is complete
    #         temperature=0.5
    #     )
    #     summary = response['choices'][0]['message']['content']
    #     tokens_used = response['usage']['total_tokens']
    #     estimated_cost = (tokens_used / 1000) * 0.002  # Adjust based on GPT pricing
    #     word_count = len(summary.split())
    #     return summary, tokens_used, estimated_cost, word_count
    # except Exception as e:
    #     logger.error(f"Summarization failed: {e}")
    #     raise

# Translate the summary into the target language
def translate_summary(summary, src_lang, dest_lang):
    """
    Translates the summary into the target language.

    Args:
        summary (str): The summary to translate.
        src_lang (str): The source language of the summary.
        dest_lang (str): The target language for the translation.

    Returns:
        translated_summary (str): The translated summary.
    """
    try:
        translated_summary = translate_text(summary, src_lang=src_lang, dest_lang=dest_lang)
        if not translated_summary:
            raise Exception("Translation failed.")
        return translated_summary
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

# Handle summarization request
def handle_summarization_request(text, original_language, target_language, num_key_points=3):
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

    try:
        # Summarize the original transcript
        summary, tokens_used, estimated_cost, word_count = summarize_text(text, original_language, num_key_points)

        # Translate the summary if the target language is not the original language
        if target_language != original_language:
            summary = translate_summary(summary, src_lang=original_language, dest_lang=target_language)

        return summary, tokens_used, estimated_cost, word_count, model
    except Exception as e:
        logger.error(f"Failed to handle summarization request: {e}")
        raise