# summarize.py
import openai
import logging
from translate import translate_text  # Import the translation function
from config import OPENAI_API_KEY

# Set up OpenAI
openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

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
        # Define the prompt for summarization
        prompt = (
            f"If I did not have time to read this YouTube video transcript, what are the most important things I absolutely must know. Enlighten me in no more than 200 words. "
            f"Always provide your response in the same language as the transcript. In this case it might be in '{language}' language. Here is the transcript itself:\n\n{text}"
        )

        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a master of extracting pearls of knowledge from YouTube video transcripts. You grasp the very essense and distill it in a consice form for users. You always provide the response in the same language in which the transcript is provided. Your answers are always clear, consise and nicely formatted."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Increased token limit to ensure the summary is complete
            temperature=0.5
        )
        summary = response['choices'][0]['message']['content']
        tokens_used = response['usage']['total_tokens']
        estimated_cost = (tokens_used / 1000) * 0.002  # Adjust based on GPT pricing
        word_count = len(summary.split())
        return summary, tokens_used, estimated_cost, word_count
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise

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

        return summary, tokens_used, estimated_cost, word_count
    except Exception as e:
        logger.error(f"Failed to handle summarization request: {e}")
        raise