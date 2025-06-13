# telegram_bot.py
import os
import re
import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, MODEL_TO_USE, ENVIRONMENT, AMPLITUDE_API_KEY
from database import store_user, store_video, store_transcript_request, get_db_connection, store_summarization_request, store_user_async, store_video_async, store_transcript_request_async, store_summarization_request_async, get_summary_by_video_language_async, get_existing_transcripts_async, insert_transcript_async
from youtube_api import extract_video_id, get_video_details, get_channel_subscribers
from transcript import get_all_transcripts, save_transcripts, normalize_language_code, test_proxy
from summarize import handle_summarization_request
from duration import format_duration
from analytics import track_event
from utils import sanitize_filename
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

    # Get video details
    video_details = get_video_details(video_id)
    channel_id = video_details['snippet']['channelId']
    subscribers = get_channel_subscribers(channel_id)  # Get number of subscribers
    await store_video_async(video_id, video_details, subscribers)  # Store video details
    transcript_request_id = await store_transcript_request_async(user_id, video_id)  # Store transcript request and get request_id

    # Prepare video details message with improved formatting
    logger.info(f"Here are video details: {video_details}.")
    video_info = (
        f"<b>📺 Title</b>: {video_details['snippet']['title']}\n\n"
        f"<b>🎙️ Channel</b>: {video_details['snippet']['channelTitle']}\n\n"
        f"<b>👥 Subscribers</b>: {int(subscribers):,}\n\n"
        f"<b>👁️ Views</b>: {int(video_details['statistics']['viewCount']):,}\n\n"
        f"<b>👍 Likes</b>: {int(video_details['statistics']['likeCount']):,}\n\n"
        f"<b>💬 Comments</b>: {int(video_details['statistics']['commentCount']):,}\n\n"
        f"<b>⏱️ Duration</b>: {format_duration(video_details['contentDetails']['duration'])}\n\n"  # Add duration
        f"<b>📝 Description</b>: {video_details['snippet']['description']}"
    )

    # Delete the temporary status message
    try:
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_message_id)
    except Exception as e:
        logger.warning(f"Failed to delete the temporary status message: {e}.")

    # Split the message into chunks of 4096 characters
    max_length = 4096
    for i in range(0, len(video_info), max_length):
        chunk = video_info[i:i + max_length]
        await update.message.reply_text(chunk, parse_mode="HTML")  # Use HTML for bold formatting

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
    
    transcript_list = await get_existing_transcripts_async(video_id, normalized_language_code)
 
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
        context.user_data['transcripts'] = transcripts # Store transcript_request_id for later use

        try:
            for transcript in transcripts:
                try:
                    formatted_transcript = transcript.get('text')
                    filename = transcript.get('filename')
                    if not filename:
                        filename = f"{base_filename}_{transcript.get('normalized_language_code')}.txt"
                    language_code = transcript.get('normalized_language_code')
                    logger.info(f"Sending transcript for language: {language_code}")
                    # Use BytesIO for binary mode (recommended for Telegram)
                    file_obj = io.BytesIO(formatted_transcript.encode('utf-8'))
                    file_obj.name = filename  # Telegram uses this as the filename
                    logger.info(f"Sending transcript file: {filename} to user {user_id}.")
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
        
        logger.info(f"Using the following transcript_request_id to find transcript: {transcript_request_id}")

        keyboard = []
        if original_language not in ['en', 'ru']:
            keyboard.append([InlineKeyboardButton("Summarize in original language", callback_data=f"sum&{video_id}&orig&{transcript_request_id}")])
        keyboard.append([InlineKeyboardButton("Summarize in English", callback_data=f"sum&{video_id}&en&{transcript_request_id}")])
        keyboard.append([InlineKeyboardButton("Summarize in Russian", callback_data=f"sum&{video_id}&ru&{transcript_request_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔮 Would you like a summary?", reply_markup=reply_markup)
    
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
    video_id, language, transcript_request_id = query.data.split('&')[1:4]
    logger.info(f"The following language selected for summary: {language}")
    
    base_filename = context.user_data.get('base_filename')
    transcripts = context.user_data.get('transcripts')

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

    if not base_filename:
        logger.error("base_filename not found in user_data.")
        await query.edit_message_text("⚠️ Failed to generate summary. Missing file information.")
        return

    await query.edit_message_text("🧠 Working on summary...")

    summary = await get_summary_by_video_language_async(video_id=video_id, language=language, model=model)

    if summary:
        logger.info(f"Summary already exists for video {video_id} in language {language} and model {model}.")

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
    
    elif transcripts:
        logger.info(f"No existing summary found for video {video_id} in language {language} and model {model}. Proceeding to generate a new summary.")
        logger.info(f"Proceeding with transcript from user context: {transcripts[0].get('filename', 'unknown')}")

        transcript = transcripts[0]

        if transcript:
            original_language = transcript.get('normalized_language_code', 'en')
            text = transcript.get('text')
            logger.info(f"Transcript found in user contextfor original language: {original_language}")
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
                    event_type="handle_summarization_summary_processed_from_user_context",
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
        logger.info(f"No transcripts found in user context. Proceeding to read from file.")

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
                    summary_properties['language'] = original_language
                    logger.info(f"Original language determined as: {original_language}")
            except:
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
            logger.info(f"Looking for transcript file: {transcript_filename}")
            if not os.path.exists(transcript_filename):
                logger.error(f"Transcript file not found: {transcript_filename}")
                raise FileNotFoundError(f"Transcript file not found: {transcript_filename}")

            with open(transcript_filename, 'r', encoding='utf-8') as f:
                transcript = f.read()

            # Handle summarization request
            logger.info(f"Starting summarization request from original '{original_language}' to target '{language}'")
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
                await query.edit_message_text("⚠️ Failed to generate summary. Invalid request ID.")
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

        await query.edit_message_text("⚠️ Failed to generate summary. Please try again later.")
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
    application.add_handler(CallbackQueryHandler(handle_summarization_button))
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is running and polling for updates.")
    application.run_polling()

if __name__ == "__main__":
    main()