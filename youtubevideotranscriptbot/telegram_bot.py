# telegram_bot.py
import os
import re
import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, MODEL_TO_USE, ENVIRONMENT, AMPLITUDE_API_KEY, MAX_TRANSCRIPTS_IN_USER_CONTEXT, MAX_DESCRIPTIONS_IN_USER_CONTEXT
from database import store_user, store_video, store_transcript_request, get_db_connection, store_summarization_request, store_user_async, store_video_async, store_transcript_request_async, store_summarization_request_async, get_summary_by_video_language_async, get_existing_transcripts_async, insert_transcript_async, get_video_by_id_async
from youtube_api import extract_video_id, get_video_details, get_channel_subscribers
from transcript import get_all_transcripts, save_transcripts, test_proxy
from summarize import handle_summarization_request
from duration import format_duration
from analytics import track_event
from utils import sanitize_filename, get_original_language, normalize_language_code, create_emoji_friendly_pdf_with_weasyprint, create_emoji_friendly_pdf_with_weasyprint_async
from languages import languages
import openai
import aiofiles
import io
from amplitude import Amplitude, BaseEvent
import os

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

async def error_handler(update, context):
    logger.error(f"Exception while handling an update: {context.error}")
    if update and update.effective_user:
        user_id = update.effective_user.id
        logger.error(f"User {user_id} may have not received the message. User might have blocked the bot.")
    else:
        logger.error("Exception occurred, but no user info available.")


async def proxy_command(update: Update, context: CallbackContext):
    logger.info(f"User {update.message.from_user.id} issued the /proxy command.")
    proxy = test_proxy()

    if not proxy:
        logger.error("Proxy test failed. No proxy available.")
        proxy = "❌ Undefined. Proxy test might have failed."

    await update.message.reply_text(f"The proxy test returned server IP as: {proxy}.")


# Start command
async def start(update: Update, context: CallbackContext):
    logger.info(f"User {update.message.from_user.id} issued the /start command.")

    user = update.message.from_user
    track_event(
        user_id=user.id,
        event_type="start_command",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "environment": ENVIRONMENT
        }
    )

    await update.message.reply_text(
        "👋 Welcome! Send me a YouTube link, and I'll fetch the video details and transcripts for you. I can also summarize transcripts so that you can get the gist of the video quickly.\n\n"
    )

# Help command
async def help_command(update: Update, context: CallbackContext):
    logger.info(f"User {update.message.from_user.id} issued the /help command.")
    user = update.message.from_user
    track_event(
        user_id=user.id,
        event_type="help_command",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "environment": ENVIRONMENT
        }
    )
    await update.message.reply_text(
        "📌 *How to use this bot:*\n\n"
        "1️⃣ Send or share a YouTube video link.\n"
        "2️⃣ I'll fetch the video details and transcripts.\n"
        "3️⃣ You’ll get the transcript as a downloadable `.txt` file.\n"
        "4️⃣ I can also summarize the video for you.\n\n"
        "💡 Tip: Try it on a TED Talk or documentary to see the magic!\n\n"
        "✍️ Share feedback or report bugs: [click here](https://bit.ly/ytvtbot)",
    parse_mode="Markdown"
    )

# Handle YouTube links
async def handle_youtube_link(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    is_bot = user.is_bot
    is_premium = user.is_premium
    user_language_code = user.language_code
    phone_number = None  # Telegram does not provide phone number directly

    logger.info(f"User {user_id} sent a YouTube link.")

    # Extract video ID
    video_url = update.message.text
    video_id = extract_video_id(video_url)

    track_event(
        user_id=user.id,
        event_type="handle_youtube_link_start",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_url": video_url,
            "video_id": video_id,
            "environment": ENVIRONMENT
        }
    )

    # Store user details
    await store_user_async(user_id, username, first_name, last_name, phone_number, user_language_code, is_bot, is_premium)

    if not video_id:
        logger.warning(f"Invalid YouTube link sent by user {user_id}.")
        track_event(
            user_id=user.id,
            event_type="handle_youtube_link_invalid_link",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_url": video_url,
                "video_id": video_id,
                "environment": ENVIRONMENT
            }
        )
        await update.message.reply_text("❌ Invalid YouTube link. Please try again.")
        return

    # await update.message.reply_text("Preparing transcripts...")
    # Send the temporary status message and store the message ID
    status_message = await update.message.reply_text("🔍 Retrieving video details...")
    status_message_id = status_message.message_id

    track_event(
        user_id=user.id,
        event_type="handle_youtube_link_retrieving_video_details_start",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_url": video_url,
            "video_id": video_id,
            "environment": ENVIRONMENT
        }
    )

    transcripts = []
    # Get video details
    video_details = get_video_details(video_id)
    channel_id = video_details.get('snippet', {}).get('channelId')
    subscribers = get_channel_subscribers(channel_id)  # Get number of subscribers
    await store_video_async(video_id, video_details, subscribers)  # Store video details
    transcript_request_id = await store_transcript_request_async(user_id, video_id)  # Store transcript request and get request_id

    snippet = video_details.get('snippet', {})
    statistics = video_details.get('statistics', {})
    content_details = video_details.get('contentDetails', {})

    # Prepare video details message with improved formatting
    logger.info(f"Here are video details: {video_details}.")
    video_info = (
        f"<b>📺 Title</b>: {snippet.get('title', 'N/A')}\n\n"
        f"<b>🎙️ Channel</b>: {snippet.get('channelTitle', 'N/A')}\n\n"
        f"<b>👥 Subscribers</b>: {int(subscribers):,}\n\n"
        f"<b>👁️ Views</b>: {int(statistics.get('viewCount', 0)):,}\n\n"
        f"<b>👍 Likes</b>: {int(statistics.get('likeCount', 0)):,}\n\n"
        f"<b>💬 Comments</b>: {int(statistics.get('commentCount', 0)):,}\n\n"
        f"<b>⏱️ Duration</b>: {format_duration(content_details.get('duration', 'PT0S'))}\n"  # Add duration
    )

    video_info_full_description = (
        f"<b>📺 Title</b>: {snippet.get('title', 'N/A')}\n\n"
        f"<b>🎙️ Channel</b>: {snippet.get('channelTitle', 'N/A')}\n\n"
        f"<b>👥 Subscribers</b>: {int(subscribers):,}\n\n"
        f"<b>👁️ Views</b>: {int(statistics.get('viewCount', 0)):,}\n\n"
        f"<b>👍 Likes</b>: {int(statistics.get('likeCount', 0)):,}\n\n"
        f"<b>💬 Comments</b>: {int(statistics.get('commentCount', 0)):,}\n\n"
        f"<b>⏱️ Duration</b>: {format_duration(content_details.get('duration', 'PT0S'))}\n\n"  # Add duration
        f"<b>📝 Description</b>: {snippet.get('description', 'N/A')}"
    )

    # Delete the temporary status message
    try:
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_message_id)
    except Exception as e:
        logger.warning(f"Failed to delete the temporary status message: {e}.")

    video_info_event_properties = {
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_url": video_url,
            "video_id": video_id,
            "environment": ENVIRONMENT
        }


    video_descriptions_in_context = context.user_data.get('video_descriptions', {})
    video_info_message_id = None

    if snippet.get('description', 'N/A') != 'N/A':
        # Store the full description in user context
        video_descriptions_in_context.update({video_id: {"video_info_full_description": video_info_full_description, 
                                                        "video_info_event_properties": video_info_event_properties,
                                                        "video_info_message_id": video_info_message_id}})
        context.user_data['video_descriptions'] = video_descriptions_in_context
        logger.info(f"Stored video description for video {video_id} in user context. Current count: {len(context.user_data.get('video_descriptions', {}))}")

        keyboard = []
        keyboard.append([InlineKeyboardButton(f"Show full description", callback_data=f"desc&{video_id}&{video_info_message_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(video_info, parse_mode="HTML", reply_markup=reply_markup)

    else:
        video_info_message = await update.message.reply_text(video_info, parse_mode="HTML")
        video_info_message_id = video_info_message.message_id

    track_event(
        user_id=user.id,
        event_type="handle_youtube_link_video_details_sent",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_url": video_url,
            "video_id": video_id,
            "environment": ENVIRONMENT
        }
    )


    # await update.message.reply_text("Preparing transcripts...")
    # Send the temporary status message and store the message ID
    status_message = await update.message.reply_text("📚 Preparing transcripts...")
    status_message_id = status_message.message_id

    track_event(
        user_id=user.id,
        event_type="handle_youtube_link_preparing_transcripts_start",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_url": video_url,
            "video_id": video_id,
            "environment": ENVIRONMENT
        }
    )

    # Include channel name in the file name (truncated to 60 characters)
    channel_name = video_details['snippet']['channelTitle'][:60]
    # Include video title in the file name (truncated to 140 characters)
    video_title = video_details['snippet']['title'][:140]
    # Sanitize the base filename
    base_filename = sanitize_filename(f"{channel_name}_{video_title}")
    context.user_data['base_filename'] = base_filename  # Store base_filename for later use

    # Get existing transcripts
    language_code = video_details['snippet'].get('defaultAudioLanguage', 'en')  # Default to 'en' if not available
    normalized_language_code = normalize_language_code(language_code)  # Normalize the language code

    logger.info(f"Using language code: {language_code} to find potentially existing transcripts.")
    
    transcript_list = await get_existing_transcripts_async(video_id)
 
    if transcript_list:
        logger.info(f"Found existing transcripts for video {video_id}.")
        logger.info(f"Number of existing transcripts found: {len(transcript_list)}")
        transcripts = transcript_list

        track_event(
            user_id=user.id,
            event_type="handle_youtube_link_transcripts_found_in_db",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_url": video_url,
                "video_id": video_id,
                "transcript_count": len(transcript_list),
                "language": normalized_language_code,
                "environment": ENVIRONMENT
            }
        )
    else:
        logger.info(f"No existing transcripts found for video {video_id}. Proceeding to fetch new transcripts.")
        # Get and save transcripts
        transcript_list = get_all_transcripts(video_id)

        if transcript_list:
            logger.info(f"Proceeding to saving transcripts for video: {video_title} from channel: {channel_name}")

            transcript_properties = {
                'video_id': video_id,
                'video_title': video_details['snippet']['title'],
                'channel_name': video_details['snippet']['channelTitle'],
                'channel_id': channel_id,
                'duration': format_duration(video_details['contentDetails']['duration']),
                'video_url': video_url,
                'user_id': user_id,
                'language_code': language_code,
                'normalized_language_code': normalize_language_code(language_code),
                'is_generated': True,
                'text': '',
                'filename': f"{base_filename}_transcript_{normalize_language_code(language_code)}.txt",
                'base_filename': base_filename,
                'type': 'transcript',
                'summary': '',
                'word_count': 0,
                'tokens_used': 0,
                'estimated_cost': 0.0,
                'model': MODEL_TO_USE,
                'user_language_code': user_language_code
            }

            logger.info(f"Initial transcript properties: {transcript_properties}")
            # Save original transcripts
            transcripts = await save_transcripts(transcript_list, base_filename, transcript_properties=transcript_properties)
            logger.info(f"Transcripts list returned from save_transcripts with length: {len(transcripts)}")

            if transcripts:
                track_event(
                    user_id=user.id,
                    event_type="handle_youtube_link_transcripts_saved",
                    event_properties={
                        "username": user.username,
                        "is_bot": user.is_bot,
                        "language_code": user.language_code,
                        "is_premium": user.is_premium,
                        "video_url": video_url,
                        "video_id": video_id,
                        "transcript_count": len(transcripts),
                        "language": normalized_language_code,
                        "environment": ENVIRONMENT
                    }
                )

    if transcripts:
        context.user_data['video_id'] = video_id  # Store video_id_id for later use

        transcripts_in_context = []
        transcripts_in_context = context.user_data.get('transcripts', [])
        logger.info(f"Current transcripts in user context: {len(transcripts_in_context)}")

        if transcripts_in_context and len(transcripts_in_context) > 0 and len(transcripts_in_context) < MAX_TRANSCRIPTS_IN_USER_CONTEXT:
            logger.info(f"Appending new transcripts to user context. Current count: {len(transcripts_in_context)}")
            transcripts_in_context.extend(transcripts)
            logger.info(f"New transcripts count in user context: {len(transcripts_in_context)}")  # Extend the existing list with new transcripts
            context.user_data['transcripts'] = transcripts_in_context
        else:
            logger.info(f"Clearing transcripts in user context and storing from scratch. New count: {len(transcripts)}")
            context.user_data['transcripts'] = transcripts # Store transcript_request_id for later use

        original_language = get_original_language(snippet, transcripts)
        logger.info(f"Original language determined as: {original_language}")

        try:
            for transcript in transcripts:
                try:
                    logger.info(f"Type of transcript object: {type(transcript)}")
                    language_code = transcript.get('normalized_language_code')

                    if not language_code in [original_language, 'en', 'ru']:
                        logger.info(f"Skipping sending transcript for language: {language_code}")
                        continue

                    formatted_transcript = transcript.get('text')
                    filename = transcript.get('filename')
                    if not filename:
                        filename = f"{base_filename}_{transcript.get('normalized_language_code')}.txt"
                    
                    logger.info(f"Sending transcript for language: {language_code}")

                    try: 
                        pdf_file = await create_emoji_friendly_pdf_with_weasyprint_async(f"{video_info}\n\n{formatted_transcript}")
                        pdf_filename = filename[:-3] + "pdf"  # Set the filename for the PDF
                        logger.info(f"Sending PDF transcript file: {pdf_filename} to user {user_id}.")

                        msg = await context.bot.send_document(
                            chat_id=update.message.chat_id,
                            document=InputFile(pdf_file, filename=pdf_filename),
                            caption=f"{pdf_filename}"
                        )
                    except Exception as e:
                        # Use BytesIO for binary mode (recommended for Telegram)
                        file_obj = io.BytesIO(formatted_transcript.encode('utf-8'))
                        file_obj.name = filename  # Telegram uses this as the filename
                        logger.error(f"Failed to send PDF transcript file {pdf_filename}: {e}")
                        logger.info(f"Sending TXT transcript file: {filename} to user {user_id}.")
                        msg = await update.message.reply_document(document=InputFile(file_obj), caption=f"{filename}")

                    track_event(
                        user_id=user.id,
                        event_type="handle_youtube_link_transcript_sent",
                        event_properties={
                            "username": user.username,
                            "is_bot": user.is_bot,
                            "language_code": user.language_code,
                            "is_premium": user.is_premium,
                            "video_url": video_url,
                            "video_id": video_id,
                            "transcript_count": len(list(transcript_list)),
                            "language": normalized_language_code,
                            "environment": ENVIRONMENT
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to send transcript for {transcript['language']}: {e}")
            logger.info(f"Transcripts seems to be sent to user {user_id} for video {video_id}.")  
        except Exception as e:
            logger.error(f"Failed to send transcripts for video {video_id} to user {user_id}: {e}")
    
        # Send transcript files to the user
        # transcript_folder = "transcripts"
        # logger.info(f"Looking for transcript files in: {transcript_folder}")
        # for filename in os.listdir(transcript_folder):
        #     if filename.startswith(base_filename):
        #         file_path = os.path.join(transcript_folder, filename)
        #         logger.info(f"Found transcript file: {file_path}")
        #         try:
        #             with open(file_path, 'rb') as f:
        #                 await update.message.reply_document(document=InputFile(f), caption=f"Transcript: {filename}")
        #             logger.info(f"Sent transcript file: {filename} to user {user_id}.")
        #         except Exception as e:
        #             logger.error(f"Failed to send transcript file {filename}: {e}")
        # logger.info(f"Transcripts sent to user {user_id} for video {video_id}.")

        # Delete the temporary status message
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_message_id)
        except Exception as e:
            logger.warning(f"Failed to delete the temporary status message: {e}.")

        # Show summarization buttons
        if not original_language:
            original_language = get_original_language(snippet, transcripts)

        # try:
        #     logger.info(f"Video snippet object at this point: {snippet}")
        #     logger.info("Attempting to determine the original language of the video.")
        #     original_language = snippet.get("defaultAudioLanguage")
        #     if original_language:
        #         logger.info(f"Original audio language determined as: {original_language}")
        #         original_language = normalize_language_code(original_language)
        #     else:
        #         original_language = snippet.get("defaultLanguage")
        #         if original_language:
        #             original_language = normalize_language_code(original_language)
        #             logger.warning(f"Original video language determined as: {original_language}")
        #         elif transcripts:
        #             # Find first object with name='Alice'
        #             t = next((t for t in transcripts if t.get('is_generated') == True and t.get('type') == 'transcript'), None)
        #             original_language = t.get('normalized_language_code') if t else None
        #             if original_language:
        #                 logger.warning(f"Original video language determined as: {original_language}")
        #                 original_language = normalize_language_code(original_language)
        #             else:
        #                 raise ValueError("No auto-generated transcript found to determine the original language.")
        #         else:
        #             raise ValueError("No language code found in video details snippet.")
        # except Exception as e:
        #     logger.error(f"Error determining the original language: {e}") # Get the language code of the first transcript
        #     logger.warning(f"Original language could not be determined. Falling back to first random or English: {original_language}")
        #     original_language = next(iter(transcripts)).get('language_code', 'en') 
        #     logger.info(f"Original language determined as: {original_language}")
        # try:
        #     original_language = normalize_language_code(original_language)
        # except:
        #     pass
        
        logger.info(f"Using the following transcript_request_id to find transcript: {transcript_request_id}")

        original_language_name = languages.get(original_language, {}).get('name', 'original language')

        keyboard = []
        if original_language not in ['en', 'ru']:
            keyboard.append([InlineKeyboardButton(f"Summarize in {original_language_name}", callback_data=f"sum&{video_id}&orig&{transcript_request_id}&{original_language}")])
        keyboard.append([InlineKeyboardButton(f"Summarize in English", callback_data=f"sum&{video_id}&en&{transcript_request_id}&{original_language}")])
        keyboard.append([InlineKeyboardButton(f"Summarize in Russian", callback_data=f"sum&{video_id}&ru&{transcript_request_id}&{original_language}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔮 <b>Would you like a summary?</b>", parse_mode="HTML", reply_markup=reply_markup)

        track_event(
            user_id=user.id,
            event_type="handle_youtube_link_summarization_buttons_displayed",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_url": video_url,
                "video_id": video_id,
                "environment": ENVIRONMENT
            }
        )
    
    else:
        logger.warning(f"No transcripts retrieved for video {video_id}.")
        # logger.warning(f"YouTube API returned a non-empty transcript list.")

        try:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_message_id)
        except Exception as e:
            logger.warning(f"Failed to delete the temporary status message: {e}.")

        msg = await update.message.reply_text("❌ No transcripts available. Try again in a few minutes or use a different link. YouTube might be blocking access to this video.")

        track_event(
            user_id=user.id,
            event_type="handle_youtube_link_transcript_not_available",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_url": video_url,
                "video_id": video_id,
                "language": normalized_language_code,
                "environment": ENVIRONMENT
            }
        )

    # else:
    #     logger.warning(f"No transcripts retrieved for video {video_id}.")
    #     logger.warning(f"YouTube API returned a non-empty transcript list.")

    #     try:
    #         await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_message_id)
    #     except Exception as e:
    #         logger.warning(f"Failed to delete the temporary status message: {e}.")

    #     await update.message.reply_text("❌ No transcripts available. Try again in a few minutes or use a different link. YouTube might be blocking access to this video.")


# Handle summarization button clicks
async def handle_summarization_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = query.from_user.id
    logger.info(f"Query data with video_id, language, transcript_request_id: {query.data}")
    video_id, language, transcript_request_id, original_language = query.data.split('&')[1:5]
    logger.info(f"The following language selected for summary: {language}")
    logger.info(f"The following language passed to summarization request as original: {original_language}")   
    
    model = MODEL_TO_USE  # Use the model specified in the config

    summary_properties = {
        "user_id": user_id,
        "video_id": video_id,
        "language": language,
        "transcript_request_id": transcript_request_id,
        "tokens_used": 0,
        "estimated_cost": 0.0,
        "word_count": 0,
        "status": "failed",
        "model": model,
        "summary": ""
    }

    track_event(
        user_id=user.id,
        event_type="handle_summarization_summary_requested",
        event_properties={
            "username": user.username,
            "is_bot": user.is_bot,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "video_id": video_id,
            "summary_language": language,
            "environment": ENVIRONMENT
        }
    )

    # if not base_filename:
    #     logger.error("base_filename not found in user_data.")
    #     await query.edit_message_text("⚠️ Failed to generate summary. Missing file information.")
    #     return

    await query.edit_message_text("🧠 Working on summary...")

    summary = await get_summary_by_video_language_async(video_id=video_id, language=language, model=model)

    if summary:
        logger.info(f"Summary already exists in DB for video {video_id} in language {language} and model {model}.")

        track_event(
            user_id=user.id,
            event_type="handle_summarization_existing_summary_found",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_id": video_id,
                "summary_language": language,
                "environment": ENVIRONMENT
            }
        )
        # Split the summary into chunks of 4096 characters
        max_length = 4096
        for i in range(0, len(summary), max_length):
            chunk = summary[i:i + max_length]
            await query.edit_message_text(chunk, parse_mode="Markdown")

        track_event(
            user_id=user.id,
            event_type="handle_summarization_existing_summary_sent",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_id": video_id,
                "summary_language": language,
                "environment": ENVIRONMENT
            }
        )
        return
    

    # base_filename = context.user_data.get('base_filename')
    base_filename = 'unknown'
    transcripts = context.user_data.get('transcripts', [])
    logger.info(f"Summary requested for video id: {video_id}.")
    logger.info(f"Total number of transcripts found in user context: {len(transcripts)}")

    if transcripts and len(transcripts) > 0:
        logger.info(f"The first trascript in user context has video id: {transcripts[0].get('video_id', 'unknown')} and filename {transcripts[0].get('filename', 'unknown')}")

    transcript = None

    for t in transcripts:
        if t.get('video_id') == video_id and t.get('type') == 'transcript' and t.get('normalized_language_code') == original_language:
            logger.info(f"Found matching transcript for video {video_id} in user context.")
            transcript = t
            base_filename = t.get('base_filename')
            break
    
    if not transcript:
        logger.info(f"No matching transcript found for video {video_id} in user context.")
        transcripts = None

    if not transcripts:
        logger.info(f"No transcripts found in user context for video {video_id}. Attempting to fetch from DB.")

        try:
            transcripts = await get_existing_transcripts_async(video_id)
        except Exception as e:
            logger.error(f"Failed to fetch existing transcripts from DB for video {video_id}: {e}")
            transcripts = None

        if transcripts:
            logger.info(f"Found existing transcripts in DB for video {video_id}.")
            logger.info(f"Number of existing transcripts found: {len(transcripts)}")

            for t in transcripts:
                if t.get('is_generated') == True and t.get('type') == 'transcript' and t.get('normalized_language_code') == original_language:
                    logger.info(f"Found matching transcript for video {video_id} in DB.")
                    transcript = t
                    base_filename = t.get('base_filename')
                    break
            
            if not transcript:
                logger.info(f"No matching transcript found for video {video_id} in DB.")
                transcripts = None


    if transcripts:
        logger.info(f"No existing summary found in DB for video {video_id} in language {language} and model {model}. Proceeding to generate a new summary.")
        
        if transcript:
            logger.info(f"Proceeding with summary for transcript from user context or DB with video id: {transcript.get('video_id')}.")
            if not original_language:
                original_language = transcript.get('normalized_language_code', 'en')
            text = transcript.get('text')
            logger.info(f"Transcript found in user context for original language: {original_language}")
            # Handle summarization request
            logger.info(f"Starting summarization request from original '{original_language}' to target '{language}'")
            logger.info(f"Text length to summarize is {len(text.split())} words.")
            try:
                summary, tokens_used, estimated_cost, word_count, model = await handle_summarization_request(
                    text=text,
                    original_language=original_language,
                    summary_properties=summary_properties,
                    model=model,
                    target_language=language,
                    num_key_points=3
                )  

                track_event(
                    user_id=user.id,
                    event_type="handle_summarization_summary_processed_from_user_context_or_db",
                    event_properties={
                        "username": user.username,
                        "is_bot": user.is_bot,
                        "language_code": user.language_code,
                        "is_premium": user.is_premium,
                        "video_id": video_id,
                        "summary_language": language,
                        "tokens_used": tokens_used,
                        "estimated_cost": estimated_cost,
                        "word_count": word_count,
                        "model": model,
                        "environment": ENVIRONMENT
                    }
                )
            except Exception as e:
                logger.error(f"Failed to produce summary from data in user context: {e}")

        else:
            logger.error(f"No transcript found in user context or DB for video {video_id}. Failed to generate summary.")


    else:
        logger.info(f"No transcripts found in user context or DB for {video_id}. Proceeding to read from file on disk.")

        try:
            # Ensure transcript_request_id is an integer
            transcript_request_id = int(transcript_request_id)

            # Fetch the original transcript file
            transcript_folder = "transcripts"
            
            try:

                logger.info("Fetching video details to get the base_filename and determine original language.")
                # Get video details
                video_details = get_video_details(video_id)
                # Include channel name in the file name (truncated to 60 characters)
                channel_name = video_details['snippet']['channelTitle'][:60]
                # Include video title in the file name (truncated to 140 characters)
                video_title = video_details['snippet']['title'][:140]
                # Sanitize the base filename
                base_filename = sanitize_filename(f"{channel_name}_{video_title}")

                if not original_language:
                    original_language = normalize_language_code(video_details['snippet']["defaultAudioLanguage"])
                if original_language:
                    summary_properties['language'] = original_language
                    logger.info(f"Original language determined as: {original_language}")
            except:
                if not original_language:
                    original_language = next(iter(get_all_transcripts(video_id))).language_code  # Get the original language code
                summary_properties['language'] = original_language
                logger.warning(f"Original language could not be determined. Falling back to first random: {original_language}")

            try:
                original_language = normalize_language_code(original_language)
                summary_properties['language'] = original_language
            except:
                pass

            transcript_filename = f"{transcript_folder}/{base_filename}_transcript_{original_language}.txt"

            # If no transcript found in user context, read from file
            logger.info(f"Looking for transcript file on disk: {transcript_filename}")
            if not os.path.exists(transcript_filename):
                logger.error(f"Transcript file not found on disk: {transcript_filename}")
                raise FileNotFoundError(f"Transcript file not found on disk: {transcript_filename}")

            with open(transcript_filename, 'r', encoding='utf-8') as f:
                transcript = f.read()

            # Handle summarization request
            logger.info(f"Starting summarization request with file on disk from original '{original_language}' to target '{language}'")
            try:
                summary, tokens_used, estimated_cost, word_count, model = await handle_summarization_request(
                    text=transcript,
                    original_language=original_language,
                    target_language=language,
                    summary_properties=summary_properties,
                    model=model,
                    num_key_points=3
                )

                track_event(
                    user_id=user.id,
                    event_type="handle_summarization_summary_processed_from_file",
                    event_properties={
                        "username": user.username,
                        "is_bot": user.is_bot,
                        "language_code": user.language_code,
                        "is_premium": user.is_premium,
                        "video_id": video_id,
                        "summary_language": language,
                        "tokens_used": tokens_used,
                        "estimated_cost": estimated_cost,
                        "word_count": word_count,
                        "model": model,
                        "environment": ENVIRONMENT
                    }
                )

            except ValueError as e:
                logger.error(f"Invalid transcript_request_id: {transcript_request_id}. Error: {e}")
                await query.edit_message_text("⚠️ Failed to generate summary. Please try again.")
            except FileNotFoundError as e:
                logger.error(f"Transcript file not found: {e}")
                await query.edit_message_text("⚠️ Failed to generate summary. Transcript file not found.")
            except Exception as e:
                logger.error(f"Failed to produce summary from file stored on disk: {e}")
                await query.edit_message_text("⚠️ Failed to generate summary. Something went wrong.")

        except Exception as e:
            logger.error(f"Failed to summarize video {video_id} for user {user_id}: {e}")
            await store_summarization_request_async(
                user_id=user_id,
                video_id=video_id,
                language=language,
                transcript_request_id=transcript_request_id,
                tokens_used=0,
                estimated_cost=0.0,
                word_count=0,
                status="failed",
                model=model
            )
            msg = await query.edit_message_text("⚠️ Failed to generate summary. Please try again later.")

            track_event(
                user_id=user.id,
                event_type="handle_summarization_summary_failed",
                event_properties={
                    "username": user.username,
                    "is_bot": user.is_bot,
                    "language_code": user.language_code,
                    "is_premium": user.is_premium,
                    "video_id": video_id,
                    "summary_language": language,
                    "model": model,
                    "environment": ENVIRONMENT
                }
            )

    if summary:
        # Format the summary with Markdown
        if language == "ru":
            formatted_summary = f"📝 *Краткое содержание:*\n\n{summary}"
        elif language == "en":
            formatted_summary = f"📝 *Summary:*\n\n{summary}"
        else:
            formatted_summary = f"📝 *Summary in Original Language:*\n\n{summary}"

        # Send the summary (if sending the whole text as one piece)
        # await query.edit_message_text(formatted_summary, parse_mode="Markdown")

        # Split the formatted summary into chunks of 4096 characters
        max_length = 4096
        for i in range(0, len(formatted_summary), max_length):
            chunk = formatted_summary[i:i + max_length]
            # await query.message.reply_text(chunk, parse_mode="Markdown")
            await query.edit_message_text(chunk, parse_mode="Markdown")

        logger.info(f"Summary sent to user {user_id} for video {video_id} in language {language}.")

        track_event(
            user_id=user.id,
            event_type="handle_summarization_summary_sent",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_id": video_id,
                "summary_language": language,
                "tokens_used": tokens_used,
                "estimated_cost": estimated_cost,
                "word_count": word_count,
                "model": model,
                "environment": ENVIRONMENT
            }
        )
    else:
        logger.error(f"Failed to generate summary for video {video_id} in language {language}.")

        track_event(
            user_id=user.id,
            event_type="handle_summarization_failed",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_id": video_id,
                "summary_language": language,
                "model": model,
                "environment": ENVIRONMENT
            }
        )

        msg = await query.edit_message_text("⚠️ Failed to generate summary. Please try again later.")
        return


# Handle show full video description button
async def handle_show_full_video_description_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = query.from_user.id
    logger.info(f"Query data for full video details request: {query.data}")
    video_id, video_info_message_id = query.data.split('&')[1:3]
    logger.info(f"Full video details requested for video: {video_id}")

    user_context_data = context.user_data.get('video_descriptions', {})
    video_info_user_context_data = user_context_data.get(video_id, {})
    video_info_full_description = video_info_user_context_data.get('video_info_full_description', '')

    video_info_event_properties = video_info_user_context_data.get('video_info_event_properties', {})
    if not video_info_message_id:
        video_info_message_id = video_info_user_context_data.get('video_info_message_id', None)
    
    if video_info_full_description:
        logger.info(f"Full video description found in user context for video {video_id}.")

    video_info_short = ""
    video_details = {}

    if not video_info_full_description:
        logger.error(f"No full video description found in user context for video {video_id}.")
        logger.info(f"Attempting to fetch video details from DB for video {video_id}.")

        video_details = await get_video_by_id_async(video_id)

        if not video_details:
            logger.error(f"Video details not found in DB for video {video_id}.")

            if video_info_event_properties:
                track_event(
                    user_id=user_id,
                    event_type="handle_youtube_link_video_details_full_description_failed",
                    event_properties=video_info_event_properties
                )
            else:
                track_event(
                    user_id=user_id,
                    event_type="handle_youtube_link_video_details_full_description_failed",
                    event_properties={
                        "username": user.username,
                        "is_bot": user.is_bot,
                        "language_code": user.language_code,
                        "is_premium": user.is_premium,
                        "video_id": video_id,
                        "environment": ENVIRONMENT
                    }
                )
            try:
                user_context_data.pop(video_id)
                if len(user_context_data) > 0:
                    context.user_data['video_descriptions'] = user_context_data
            except Exception as e:
                logger.error(f"Failed to remove video description from user context: {e}")

        logger.info(f"Video details fetched from DB for video {video_id}: {str(video_details)[:300]}.")

        video_info_short = (
            f"<b>📺 Title</b>: {video_details.get('video_title', 'N/A')}\n\n"
            f"<b>🎙️ Channel</b>: {video_details.get('channel_name', 'N/A')}\n\n"
            f"<b>👥 Subscribers</b>: {int(video_details.get('subscribers', 0)):,}\n\n"
            f"<b>👁️ Views</b>: {int(video_details.get('view_count', 0)):,}\n\n"
            f"<b>👍 Likes</b>: {int(video_details.get('like_count', 0)):,}\n\n"
            f"<b>💬 Comments</b>: {int(video_details.get('comment_count', 0)):,}\n\n"
            f"<b>⏱️ Duration</b>: {format_duration(video_details.get('duration', 'PT0S'))}\n\n" 
        )

        video_info_full_description = (
            f"<b>📺 Title</b>: {video_details.get('video_title', 'N/A')}\n\n"
            f"<b>🎙️ Channel</b>: {video_details.get('channel_name', 'N/A')}\n\n"
            f"<b>👥 Subscribers</b>: {int(video_details.get('subscribers', 0)):,}\n\n"
            f"<b>👁️ Views</b>: {int(video_details.get('view_count', 0)):,}\n\n"
            f"<b>👍 Likes</b>: {int(video_details.get('like_count', 0)):,}\n\n"
            f"<b>💬 Comments</b>: {int(video_details.get('comment_count', 0)):,}\n\n"
            f"<b>⏱️ Duration</b>: {format_duration(video_details.get('duration', 'PT0S'))}\n\n" 
            f"<b>📝 Description</b>: {video_details.get('description', 'N/A')}"
        )
    

    if len(video_info_full_description) < 4096:

        await query.edit_message_text(video_info_full_description, parse_mode="HTML")
        logger.info(f"Full video description sent to user {user_id} for video {video_id}.")

    else:

        if not video_info_short:
            video_info_short = video_info_full_description.split("<b>📝 Description</b>:")[0]

        try:
            pdf_file = await create_emoji_friendly_pdf_with_weasyprint_async(video_info_full_description)
            # pdf_file = convert_to_pdf_xhtml2pdf("Example text for testing")
            if video_details:
                logger.info(f"Video details for video {video_id} and PDF file name: {str(video_details)[:300]}.")
                filename = f"{video_details.get('video_title', 'Full')}_video_details_{str(video_details.get('video_id')) if video_details and 'video_id' in video_details else str(video_id)}.pdf"
            else:
                logger.info(f"No video details for video {video_id} and PDF file name.")
                filename = f"Video_Details_for_video_{str(video_id)}.pdf"
            # await query.message.reply_document(document=InputFile(pdf_file, filename=filename), caption="📄 Full description as PDF")

            edited_msg = await query.edit_message_text(f"{video_info_short}───────\nThis video description is too long to fit one Telegram message. See the PDF in a separate message below with the full text 👇", parse_mode="HTML")
            # Send PDF and make sure it's directly following the edited message
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(pdf_file, filename=filename),
                caption=f"📄 Full description for the video above 👆",
                reply_to_message_id=edited_msg.message_id  # Ensures order
            )

            logger.info(f"Sent PDF description to user {user_id} for video {str(video_id)}.")
                                       
        except Exception as e:
            logger.error(f"Failed to send full video description in PDF for video {video_id} to user {user_id}: {e}")
            logger.info(f"Sending full video description in chunks for video {video_id}.")

            await query.edit_message_text(f"{video_info_short}───────\nThis video description is too long to fit in one Telegram message. See the messages below for the full text 👇", parse_mode="HTML")
            
            follow_up_message = "Here’s the full description for this video 👆 It’s too long for one Telegram message, so I split it into several parts.\n\n───────\n\n"
            max_length = 4096 - len(follow_up_message) - 2  # Adjust max_length to account for the follow-up message
            for idx, i in enumerate(range(0, len(video_info_full_description), max_length)):
                chunk = video_info_full_description[i:i + max_length]
                if idx == 0:
                    await query.message.reply_text(f"{follow_up_message}{chunk}", parse_mode="HTML", reply_to_message_id=query.message.message_id)
                else:
                    await query.message.reply_text(chunk, parse_mode="HTML")
            logger.info(f"Full video description sent to user {user_id} for video {video_id}.")

    if video_info_event_properties:
        track_event(
            user_id=user_id,
            event_type="handle_youtube_link_video_details_full_description_sent",
            event_properties=video_info_event_properties
        )   
    else:
        track_event(
            user_id=user_id,
            event_type="handle_youtube_link_video_details_full_description_sent",
            event_properties={
                "username": user.username,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "video_id": video_id,
                "environment": ENVIRONMENT
            }
        )

    try:
        logger.info(f"Current video descriptions in user context: {len(context.user_data.get('video_descriptions', {}))}")
        user_context_data.pop(video_id)
        if len(user_context_data) > 0:
            context.user_data['video_descriptions'] = user_context_data
        logger.info(f"New video descriptions len in user context: {len(context.user_data.get('video_descriptions', {}))}")

        if len(context.user_data.get('video_descriptions', {})) > MAX_DESCRIPTIONS_IN_USER_CONTEXT:
            user_context_data = context.user_data.get('video_descriptions', {})
            first_key = next(iter(user_context_data))
            user_context_data.pop(video_id)
            context.user_data['video_descriptions'] = user_context_data
            logger.info(f"Removed first video_description from user context. Now len is: {len(context.user_data.get('video_descriptions', {}))}.")
    except Exception as e:
        logger.error(f"Failed to remove video description from user context: {e}")
        logger.info(f"Now video_descriptions object len in user context: {len(context.user_data.get('video_descriptions', {}))}")

    return


# Main function to start the bot
def main():
    logger.info("Starting the bot...")
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("proxy", proxy_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))
    application.add_handler(CallbackQueryHandler(handle_show_full_video_description_button, pattern="^desc&"))
    application.add_handler(CallbackQueryHandler(handle_summarization_button, pattern="^sum&"))
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is running and polling for updates.")
    application.run_polling()

if __name__ == "__main__":
    main()