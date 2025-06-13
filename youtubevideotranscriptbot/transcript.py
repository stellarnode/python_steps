# transcript.py
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api.formatters import TextFormatter
# from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, TooManyRequests
import os
import logging
from translate import translate_text  
from config import MODEL_TO_USE 
from config import PROXY_USERNAME
from config import PROXY_PASSWORD
from model_params import get_model_params
from database import store_transcript_request_async, insert_transcript_async
import aiofiles
import asyncio
import requests
import traceback

logger = logging.getLogger(__name__)

# Normalize language codes (e.g., "en-US" -> "en")
def normalize_language_code(language_code):
    # Split on hyphen and take the first part
    return language_code.split('-')[0]

def test_proxy():
    # Test the proxy directly
    proxy_config = WebshareProxyConfig(
        proxy_username=PROXY_USERNAME,
        proxy_password=PROXY_PASSWORD
    )

    # Get the proxy dict
    logger.info(f"Testing... proxy_config methods: {dir(proxy_config)}")
    proxy_dict = proxy_config.to_requests_dict()

    # Test with a simple request
    try:
        response = requests.get("https://httpbin.org/ip", proxies=proxy_dict, timeout=10)
        logger.info(f"Proxy working! Your IP: {response.json()}")
        return response.json()
    except Exception as e:
        logger.info(f"Proxy failed: {e}")


# Get all available transcripts
def get_all_transcripts(video_id):

    # You can test the proxy like this:
    # try:
    #     test_proxy()
    # except Exception as e:
    #     logger.error(f"Failed to test proxy: {e}")

    if len(PROXY_PASSWORD) > 0 and len(PROXY_USERNAME) > 0:
        logger.info(f"Using proxy configuration. You can fall back to default by removing PROXY_USERNAME and PROXY_PASSWORD from config.")
        ytt_api_proxied = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=PROXY_USERNAME,
                proxy_password=PROXY_PASSWORD,
            )
        )
 
    logger.info(f"[Get Transcript List] Using default YouTubeTranscriptApi without proxy.")
    ytt_api = YouTubeTranscriptApi()

    try:
        # logger.info(f"Available methods for YouTubeTranscriptApi: {dir(YouTubeTranscriptApi)}")
        transcript_list = ytt_api.list(video_id)
        if transcript_list:
            logger.info(f"Transcript list is not empty. Fetched transcripts list for video ID: {video_id}")
        else:
            logger.info(f"Transcript list is empty. No transcripts found without proxy for video ID: {video_id}")
    except Exception as e:
        logger.error(f"Failed to fetch transcript list without proxy for video {video_id}: {e}")
        transcript_list = None

    if not transcript_list and ytt_api_proxied:
        try:
            logger.info(f"[Get Transcript List] Attempting to fetch transcripts with proxy configuration.")
            transcript_list = ytt_api_proxied.list(video_id)
            # logger.info(f"Available methods for TranscriptList: {dir(transcript_list)}")
            # print("Available transcripts:\n")
            # print(transcript_list)
            if not transcript_list:
                logger.info(f"Transcript list is empty. No transcripts found with proxy for video ID: {video_id}")
            else:
                logger.info(f"Transcript list is not empty. Fetched transcripts list with proxy for video ID: {video_id}")
    
        except Exception as e:
            logger.error(f"Unexpected error for video {video_id}: {e}")
            return None

    return transcript_list


# Save transcripts and translate if necessary
async def save_transcripts(transcript_list, base_filename, transcript_properties=None):
    
    if len(PROXY_PASSWORD) > 0 and len(PROXY_USERNAME) > 0:
        logger.info(f"Using proxy configuration. You can fall back to default by removing PROXY_USERNAME and PROXY_PASSWORD from config.")
        ytt_api_proxied = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=PROXY_USERNAME,
                proxy_password=PROXY_PASSWORD,
            )
        )
  
    logger.info(f"Creating default YouTubeTranscriptApi without proxy.")
    ytt_api = YouTubeTranscriptApi()
    
    formatter = TextFormatter()
    os.makedirs("transcripts", exist_ok=True)  # Create the transcripts directory if it doesn't exist
    transcripts = []

    model_params = get_model_params(MODEL_TO_USE)
    # Set to True if you require translations of the transcripts.
    # By default, I turned off this feature to avoid unnecessary API calls.
    translation_needed = {"en": True, "ru": False}

    logger.info(f"Checking if there is an English version of the transcript already.")
    try:
        en_transcript = transcript_list.find_transcript(['en'])
    except Exception as e:
        logger.warning(f"English transcript not found in transcript list or there was an error: {e}")
        en_transcript = None

    if en_transcript:
        translation_needed["en"] = False

    for transcript in transcript_list:
        language_code = transcript.language_code
        is_generated = transcript.is_generated
        language = transcript.language
        normalized_language_code = normalize_language_code(language_code) 
        if normalize_language_code == "en" and not is_generated:
            translation_needed["en"] = False
        if normalize_language_code == "ru" and not is_generated:
            translation_needed["ru"] = False

    # for transcript in transcript_list:
    #     language_code = transcript.language_code
    #     normalized_language_code = normalize_language_code(language_code)  # Normalize the language code
    #     language = transcript.language
    #     is_generated = transcript.is_generated

        original_audio_language = transcript_properties.get('normalized_language_code', '')
        transcript_data = None

        # if original_audio_language != normalized_language_code or normalized_language_code != 'en':
        #     logger.info(f"Transcript retrieval for language {normalized_language_code} skipped since nor original audio or 'en'. Original audio is: {original_audio_language}.")
        #     continue

        logger.info(f"Fetching transcript for language: {language} ({normalized_language_code})")
        logger.info(f"[Get Single Transcript] Attempting to fetch with(out) proxy")
        
        try:
            # transcript_data = transcript.fetch()
            transcript_data = ytt_api_proxied.fetch(transcript_properties.get('video_id'), languages=[language_code])
            logger.info(f"Transcript data from fetch attempt: {str(transcript_data)[:500]}")
        except Exception as e:
            logger.warning(f"Fetch without proxy failed for {language}: {e}")
            transcript_data = None

        if not transcript_data and ytt_api_proxied:
            await asyncio.sleep(1.5)
            logger.info(f"[Get Single Transcript] Attempting to fetch with proxy")
            # Retry logic for fetching transcript
            retry_attempts = 3
            for attempt in range(1, retry_attempts + 1):
                try:
                    transcript_data = ytt_api_proxied.fetch(transcript_properties.get('video_id'), languages=[language_code]) # ytt_api.fetch(transcript.video_id)
                    logger.info(f"Transcript data from fetch attempt: {str(transcript_data)[:500]}")
                    break
                except Exception as e:
                    logger.warning(f"Fetch failed for {language} (attempt {attempt}): {e}")
                    # logger.warning("Proxy failed error type:", type(e).__name__)
                    # logger.warning("Full traceback:\n")
                    # logger.warning(traceback.print_exc())
                    if attempt < retry_attempts:
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"Giving up on {language} after {retry_attempts} attempts.")
                        transcript_data = None

        if not transcript_data:
            continue

        try:
            formatted_transcript = formatter.format_transcript(transcript_data)

            if not transcript_properties:
                transcript_properties = {
                "base_filename": base_filename,
                "type": "transcript",
                "language_code": language_code,
                "normalized_language_code": normalized_language_code,
                "is_generated": is_generated,
                "text": formatted_transcript,
                "filename": f"{base_filename}_transcript_{normalized_language_code}.txt"
            }
            else:
                transcript_properties.update({
                    "language_code": language_code,
                    "normalized_language_code": normalized_language_code,
                    "is_generated": is_generated,
                    "text": formatted_transcript,
                    "filename": f"{base_filename}_transcript_{normalized_language_code}.txt",
                    "base_filename": base_filename,
                    "type": "transcript",
                    "word_count": len(formatted_transcript.split())
                })

            transcripts.append(transcript_properties)

            try:
                await insert_transcript_async(transcript_properties)
            except Exception as e:
                logger.error(f"Failed to insert original transcript info into DB: {e}")

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
            logger.error(f"Failed to save the original transcript for {language} to disk: {e}")

        try:

            user_language_code = transcript_properties.get('user_language_code', '')
            logger.info(f"User language code determined as: {user_language_code}")
            logger.info(f"Transcript normalized language code: {normalized_language_code}")

            if user_language_code == normalized_language_code:
                translation_needed["en"] = False

            # Translate to English if not already in English
            if normalized_language_code != 'en' and translation_needed["en"]:
                translated_text, tokens_used, estimated_cost, word_count = await translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='en')
                if translated_text:

                    if not transcript_properties:
                        transcript_properties = {
                        "base_filename": base_filename,
                        "type": "translation",
                        "language_code": "en",
                        "normalized_language_code": "en",
                        "is_generated": is_generated,
                        "text": translated_text,
                        "filename": f"{base_filename}_translation_en.txt"
                    }
                    else:
                        transcript_properties = transcript_properties.copy()
                        transcript_properties.update({
                            "language_code": "en",
                            "normalized_language_code": "en",
                            "is_generated": is_generated,
                            "text": translated_text,
                            "filename": f"{base_filename}_translation_en.txt",
                            "base_filename": base_filename,
                            "type": "translation",
                            "word_count": len(translated_text.split())
                        })

                    transcripts.append(transcript_properties)

                    try:
                        await insert_transcript_async(transcript_properties)
                    except Exception as e:
                        logger.error(f"Failed to insert transcript info for 'en' translation into DB: {e}")

                    translated_filename = f"transcripts/{base_filename}_translation_en.txt"
                    async with aiofiles.open(translated_filename, 'w', encoding='utf-8') as f:
                        await f.write(translated_text[0])
                        await f.flush()
                    logger.info(f"Saved English translation to {translated_filename}")

            # Translate to Russian if not already in Russian
            if normalized_language_code != 'ru' and translation_needed["ru"]:
                translated_text, tokens_used, estimated_cost, word_count = await translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='ru')
                if translated_text:
                    
                    if not transcript_properties:
                        transcript_properties = {
                        "base_filename": base_filename,
                        "type": "translation",
                        "language_code": "ru",
                        "normalized_language_code": "ru",
                        "is_generated": is_generated,
                        "text": translated_text,
                        "filename": f"{base_filename}_translation_ru.txt"
                    }
                    else:
                        transcript_properties = transcript_properties.copy()
                        transcript_properties.update({
                            "language_code": "ru",
                            "normalized_language_code": "ru",
                            "is_generated": is_generated,
                            "text": translated_text,
                            "filename": f"{base_filename}_translation_ru.txt",
                            "base_filename": base_filename,
                            "type": "translation",
                            "word_count": len(translated_text.split())
                        })

                    transcripts.append(transcript_properties)    

                    try:
                        await insert_transcript_async(transcript_properties)
                    except Exception as e:
                        logger.error(f"Failed to insert transcript info for 'ru' translation into DB: {e}")
                    
                    translated_filename = f"transcripts/{base_filename}_translation_ru.txt"
                    async with aiofiles.open(translated_filename, 'w', encoding='utf-8') as f:
                        await f.write(translated_text[0])
                        await f.flush()
                    logger.info(f"Saved Russian translation to {translated_filename}")

        except Exception as e:
            logger.error(f"Failed to translate transcripts and store translations: {e}")

    return transcripts