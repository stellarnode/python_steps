# transcript.py
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import os
import logging
from translate import translate_text  # Import the translation function
from config import MODEL_TO_USE  # Import the model selection
from model_params import get_model_params
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

# Normalize language codes (e.g., "en-US" -> "en")
def normalize_language_code(language_code):
    # Split on hyphen and take the first part
    return language_code.split('-')[0]

# Get all available transcripts
def get_all_transcripts(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # print("Available transcripts:\n")
        # print(transcript_list)
        logger.info(f"Transcripts seem to have been received from YouTube.\n")
        if not transcript_list:
            logger.info(f"Or maybe not...\n")
            # try:
            #     logger.info(f"Attempting to get the list with proxy.\n")
            #     transcript_list = YouTubeTranscriptApi.list_transcripts(
            #         video_id,
            #         proxies={
            #             "https": "socks5://127.0.0.1:9050",
            #             "http": "socks5://127.0.0.1:9050",
            #         }
            #     )
            # except Exception as e:
            #     logger.error(f"Failed to fetch transcripts with proxy: {e}")
        else:
            logger.info(f"Transcript list is not empty. Successfully fetched transcripts list for video ID: {video_id}")
        return transcript_list
    except Exception as e:
        logger.error(f"An error occurred while fetching transcripts: {e}")
        return None

# Save transcripts and translate if necessary
async def save_transcripts(transcript_list, base_filename):
    formatter = TextFormatter()
    os.makedirs("transcripts", exist_ok=True)  # Create the transcripts directory if it doesn't exist
    transcripts = []

    model_params = get_model_params(MODEL_TO_USE)
    # Set to True if you require translations of the transcripts.
    # By default, I turned off this feature to avoid unnecessary API calls.
    translation_needed = {"en": True, "ru": False}

    for transcript in transcript_list:
        language_code = transcript.language_code
        is_generated = transcript.is_generated
        normalized_language_code = normalize_language_code(language_code) 
        if normalize_language_code == "en" and not is_generated:
            translation_needed["en"] = False
        if normalize_language_code == "ru" and not is_generated:
            translation_needed["ru"] = False

    for transcript in transcript_list:
        language_code = transcript.language_code
        normalized_language_code = normalize_language_code(language_code)  # Normalize the language code
        language = transcript.language
        is_generated = transcript.is_generated

        logger.info(f"Fetching transcript for language: {language} ({normalized_language_code})")
        

        # Retry logic for fetching transcript
        retry_attempts = 3
        for attempt in range(1, retry_attempts + 1):
            try:
                transcript_data = transcript.fetch()
                logger.info(f"Transcript data from fetch attempt with keys: {transcript_data.keys()}")
                break
            except Exception as e:
                logger.warning(f"Fetch failed for {language} (attempt {attempt}): {e}")
                if attempt < retry_attempts:
                    await asyncio.sleep(1.5)
                else:
                    logger.error(f"Giving up on {language} after {retry_attempts} attempts.")
                    transcript_data = None

        if not transcript_data:
            continue

        try:
            formatted_transcript = formatter.format_transcript(transcript_data)

        # try:
        #     # Fetch the transcript
        #     transcript_data = transcript.fetch()
        #     formatted_transcript = formatter.format_transcript(transcript_data)

            # print(formatted_transcript)
            transcripts.append({
                "base_filename": base_filename,
                "type": "transcript",
                "language": language,
                "normalized_language_code": normalized_language_code,
                "is_generated": is_generated,
                "text": formatted_transcript,
                "filename": f"{base_filename}_transcript_{normalized_language_code}.txt"
            })
        except Exception as e:
            logger.error(f"Failed to fetch transcript from YouTube for {language}: {e}")
            
        try:
            # Save the original transcript
            filename = f"transcripts/{base_filename}_transcript_{normalized_language_code}.txt"
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(formatted_transcript)
                await f.flush()
            logger.info(f"Saved transcript for {language} to {filename}")
        except Exception as e:
            logger.error(f"Failed to save the original transcript for {language}: {e}")

        try:
            # Translate to English if not already in English
            if normalized_language_code != 'en' and translation_needed["en"]:
                translated_text = await translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='en')
                if translated_text:
                    transcripts.append({
                        "base_filename": base_filename,
                        "type": "translation",
                        "language": language,
                        "normalized_language_code": "en",
                        "is_generated": is_generated,
                        "text": translated_text[0],
                        "filename": f"{base_filename}_translation_en.txt"
                    })
                    translated_filename = f"transcripts/{base_filename}_translation_en.txt"
                    async with aiofiles.open(translated_filename, 'w', encoding='utf-8') as f:
                        await f.write(translated_text[0])
                        await f.flush()
                    logger.info(f"Saved English translation to {translated_filename}")

            # Translate to Russian if not already in Russian
            if normalized_language_code != 'ru' and translation_needed["ru"]:
                translated_text = await translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='ru')
                if translated_text:
                    transcripts.append({
                        "base_filename": base_filename,
                        "type": "translation",
                        "language": language,
                        "normalized_language_code": "ru",
                        "is_generated": is_generated,
                        "text": translated_text[0],
                        "filename": f"{base_filename}_translation_ru.txt"
                    })
                    translated_filename = f"transcripts/{base_filename}_translation_ru.txt"
                    async with aiofiles.open(translated_filename, 'w', encoding='utf-8') as f:
                        await f.write(translated_text[0])
                        await f.flush()
                    logger.info(f"Saved Russian translation to {translated_filename}")

        except Exception as e:
            logger.error(f"Failed to translate transcripts: {e}")

    return transcripts