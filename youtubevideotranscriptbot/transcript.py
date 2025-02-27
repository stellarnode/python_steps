# transcript.py
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import os
import logging
from translate import translate_text  # Import the translation function

logger = logging.getLogger(__name__)

# Normalize language codes (e.g., "en-US" -> "en")
def normalize_language_code(language_code):
    # Split on hyphen and take the first part
    return language_code.split('-')[0]

# Get all available transcripts
def get_all_transcripts(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        logger.info(f"Transcripts received from YouTube.\n")
        return transcript_list
    except Exception as e:
        logger.error(f"An error occurred while fetching transcripts: {e}")
        return None

# Save transcripts and translate if necessary
def save_transcripts(transcript_list, base_filename):
    formatter = TextFormatter()
    os.makedirs("transcripts", exist_ok=True)  # Create the transcripts directory if it doesn't exist

    translation_needed = {"en": True, "ru": True}

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
        
        try:
            # Fetch the transcript
            transcript_data = transcript.fetch()
            formatted_transcript = formatter.format_transcript(transcript_data)
            # print(formatted_transcript)
            
            # Save the original transcript
            filename = f"transcripts/{base_filename}_transcript_{normalized_language_code}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            logger.info(f"Saved transcript for {language} to {filename}")

            # Translate to English if not already in English
            if normalized_language_code != 'en' and translation_needed["en"]:
                translated_text = translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='en')
                if translated_text:
                    translated_filename = f"transcripts/{base_filename}_translation_en.txt"
                    with open(translated_filename, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                    logger.info(f"Saved English translation to {translated_filename}")

            # Translate to Russian if not already in Russian
            if normalized_language_code != 'ru' and translation_needed["ru"]:
                translated_text = translate_text(formatted_transcript, src_lang=normalized_language_code, dest_lang='ru')
                if translated_text:
                    translated_filename = f"transcripts/{base_filename}_translation_ru.txt"
                    with open(translated_filename, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                    logger.info(f"Saved Russian translation to {translated_filename}")

        except Exception as e:
            logger.error(f"Failed to fetch transcript for {language}: {e}")