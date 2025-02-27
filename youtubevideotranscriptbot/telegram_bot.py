# telegram_bot.py
import os
import re
import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from database import store_user, store_video, store_transcript_request, get_db_connection, store_summarization_request
from youtube_api import extract_video_id, get_video_details, get_channel_subscribers
from transcript import get_all_transcripts, save_transcripts, normalize_language_code
from summarize import handle_summarization_request
from duration import format_duration  # Import the duration formatting function
import openai

# Set up OpenAI
openai.api_key = OPENAI_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Log to a file
        logging.StreamHandler()          # Log to the console
    ]
)
logger = logging.getLogger(__name__)

# Sanitize filename
def sanitize_filename(filename):
    """
    Sanitize the filename by replacing invalid characters with underscores.
    """
    sanitized = re.sub(r'[\\/*?:"<>| ]', '_', filename)
    sanitized = sanitized.strip('_')
    return sanitized

# Start command
async def start(update: Update, context: CallbackContext):
    logger.info(f"User {update.message.from_user.id} issued the /start command.")
    await update.message.reply_text(
        "Welcome! Send me a YouTube link, and I'll fetch the video details and transcripts for you."
    )

# Help command
async def help_command(update: Update, context: CallbackContext):
    logger.info(f"User {update.message.from_user.id} issued the /help command.")
    await update.message.reply_text(
        "How to use this bot:\n"
        "1. Send a YouTube video link.\n"
        "2. I'll fetch the video details and transcripts.\n"
        "3. I'll send you the transcripts in .txt format."
    )

# Handle YouTube links
async def handle_youtube_link(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    phone_number = None  # Telegram does not provide phone number directly

    logger.info(f"User {user_id} sent a YouTube link.")

    # Store user details
    store_user(user_id, username, first_name, last_name, phone_number)

    # Extract video ID
    video_url = update.message.text
    video_id = extract_video_id(video_url)

    if not video_id:
        logger.warning(f"Invalid YouTube link sent by user {user_id}.")
        await update.message.reply_text("Invalid YouTube link. Please try again.")
        return

    # Get video details
    video_details = get_video_details(video_id)
    channel_id = video_details['snippet']['channelId']
    subscribers = get_channel_subscribers(channel_id)  # Get number of subscribers
    store_video(video_id, video_details, subscribers)  # Store video details
    transcript_request_id = store_transcript_request(user_id, video_id)  # Store transcript request and get request_id

    # Prepare video details message with improved formatting
    logger.info(f"Here are video details: {video_details}.")
    video_info = (
        f"<b>Title</b>: {video_details['snippet']['title']}\n\n"
        f"<b>Channel</b>: {video_details['snippet']['channelTitle']}\n\n"
        f"<b>Subscribers</b>: {subscribers}\n\n"
        f"<b>Views</b>: {video_details['statistics']['viewCount']}\n\n"
        f"<b>Likes</b>: {video_details['statistics']['likeCount']}\n\n"
        f"<b>Comments</b>: {video_details['statistics']['commentCount']}\n\n"
        f"<b>Duration</b>: {format_duration(video_details['contentDetails']['duration'])}\n\n"  # Add duration
        f"<b>Description</b>: {video_details['snippet']['description']}"
    )

    # Split the message into chunks of 4096 characters
    max_length = 4096
    for i in range(0, len(video_info), max_length):
        chunk = video_info[i:i + max_length]
        await update.message.reply_text(chunk, parse_mode="HTML")  # Use HTML for bold formatting

    # Get and save transcripts
    transcript_list = get_all_transcripts(video_id)
    if transcript_list:
        # Include channel name in the file name (truncated to 60 characters)
        channel_name = video_details['snippet']['channelTitle'][:60]
        # Include video title in the file name (truncated to 140 characters)
        video_title = video_details['snippet']['title'][:140]

        # Sanitize the base filename
        base_filename = sanitize_filename(f"{channel_name}_{video_title}")
        context.user_data['base_filename'] = base_filename  # Store base_filename for later use
        logger.info(f"Saving transcripts for video: {video_title} from channel: {channel_name}")

        # Save original transcripts
        save_transcripts(transcript_list, base_filename)

        # Send transcript files to the user
        transcript_folder = "transcripts"
        logger.info(f"Looking for transcript files in: {transcript_folder}")
        for filename in os.listdir(transcript_folder):
            if filename.startswith(base_filename):
                file_path = os.path.join(transcript_folder, filename)
                logger.info(f"Found transcript file: {file_path}")
                try:
                    with open(file_path, 'rb') as f:
                        await update.message.reply_document(document=InputFile(f), caption=f"Transcript: {filename}")
                    logger.info(f"Sent transcript file: {filename} to user {user_id}.")
                except Exception as e:
                    logger.error(f"Failed to send transcript file {filename}: {e}")
        logger.info(f"Transcripts sent to user {user_id} for video {video_id}.")

        # Show summarization buttons
        
        try:
            original_language = normalize_language_code(video_details['snippet']["defaultAudioLanguage"])
            if original_language:
                logger.info(f"Original language determined as: {original_language}")
        except:
            original_language = next(iter(transcript_list)).language_code  # Get the language code of the first transcript
            logger.warning(f"Original language could not be determined. Falling back to first random: {original_language}")


        try:
            original_language = normalize_language_code(original_language)
        except:
            pass
        
        keyboard = []
        if original_language not in ['en', 'ru']:
            keyboard.append([InlineKeyboardButton("Summarize in Original Language", callback_data=f"sum_{video_id}_orig_{transcript_request_id}")])
        keyboard.append([InlineKeyboardButton("Summarize in English", callback_data=f"sum_{video_id}_en_{transcript_request_id}")])
        keyboard.append([InlineKeyboardButton("Summarize in Russian", callback_data=f"sum_{video_id}_ru_{transcript_request_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Would you like a summary?", reply_markup=reply_markup)
    else:
        logger.warning(f"No transcripts available for video {video_id}.")
        await update.message.reply_text("No transcripts available for this video.")

# Handle summarization button clicks
async def handle_summarization_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    video_id, language, transcript_request_id = query.data.split('_')[1:4]
    logger.info(f"The folloing language selected for summary: {language}")
    base_filename = context.user_data.get('base_filename')  # Retrieve base_filename

    if not base_filename:
        logger.error("base_filename not found in user_data.")
        await query.edit_message_text("Failed to generate summary. Missing file information.")
        return

    try:
        # Ensure transcript_request_id is an integer
        transcript_request_id = int(transcript_request_id)

        # Fetch the original transcript file
        transcript_folder = "transcripts"
        
        try:
            # Get video details
            video_details = get_video_details(video_id)
            original_language = normalize_language_code(video_details['snippet']["defaultAudioLanguage"])
            if original_language:
                logger.info(f"Original language determined as: {original_language}")
        except:
            original_language = next(iter(get_all_transcripts(video_id))).language_code  # Get the original language code
            logger.warning(f"Original language could not be determined. Falling back to first random: {original_language}")

        try:
            original_language = normalize_language_code(original_language)
        except:
            pass
        transcript_filename = f"{transcript_folder}/{base_filename}_transcript_{original_language}.txt"

        logger.info(f"Looking for transcript file: {transcript_filename}")
        if not os.path.exists(transcript_filename):
            logger.error(f"Transcript file not found: {transcript_filename}")
            raise FileNotFoundError(f"Transcript file not found: {transcript_filename}")

        with open(transcript_filename, 'r', encoding='utf-8') as f:
            transcript = f.read()

        # Handle summarization request
        logger.info(f"Starting summarization request from original '{original_language}' to target '{language}'")
        summary, tokens_used, estimated_cost, word_count = handle_summarization_request(
            text=transcript,
            original_language=original_language,
            target_language=language,
            num_key_points=3
        )

        # Log the summarization request in the database
        store_summarization_request(
            user_id=user_id,
            video_id=video_id,
            language=language,
            transcript_request_id=transcript_request_id,
            tokens_used=tokens_used,
            estimated_cost=estimated_cost,
            word_count=word_count,
            status="completed"
        )

        # Format the summary with Markdown
        if language == "ru":
            formatted_summary = f"*Краткое содержание:*\n\n{summary}"
        elif language == "en":
            formatted_summary = f"*Summary:*\n\n{summary}"
        else:
            formatted_summary = f"*Summary in Original Language:*\n\n{summary}"

        # Send the summary
        await query.edit_message_text(formatted_summary, parse_mode="Markdown")
    except ValueError as e:
        logger.error(f"Invalid transcript_request_id: {transcript_request_id}. Error: {e}")
        await query.edit_message_text("Failed to generate summary. Invalid request ID.")
    except FileNotFoundError as e:
        logger.error(f"Transcript file not found: {e}")
        await query.edit_message_text("Failed to generate summary. Transcript file not found.")
    except Exception as e:
        logger.error(f"Failed to summarize video {video_id} for user {user_id}: {e}")
        # Log the failed summarization request in the database
        store_summarization_request(
            user_id=user_id,
            video_id=video_id,
            language=language,
            transcript_request_id=transcript_request_id,
            tokens_used=0,
            estimated_cost=0.0,
            word_count=0,
            status="failed"
        )
        await query.edit_message_text("Failed to generate summary. Please try again later.")

# Main function to start the bot
def main():
    logger.info("Starting the bot...")
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))
    application.add_handler(CallbackQueryHandler(handle_summarization_button))

    # Start the bot
    logger.info("Bot is running and polling for updates.")
    application.run_polling()

if __name__ == "__main__":
    main()