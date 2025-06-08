# database.py
import mysql.connector.pooling
from mysql.connector import Error
from config import DB_CONFIG
from config import MODEL_TO_USE
import logging
import asyncio
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Create a connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="bot_pool",
    pool_size=20,  # Adjust based on your needs
    **DB_CONFIG
)

# Connect to MySQL database using the connection pool
def get_db_connection():
    try:
        conn = db_pool.get_connection()
        logger.info("Acquired DB connection from pool.")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise

@contextmanager
def db_cursor():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Store user information
def store_user(user_id, username, first_name, last_name, phone_number=None, user_language_code=None, is_bot=None, is_premium=None):
    try:
        with db_cursor() as cursor:
            query = """
            INSERT INTO users (user_id, username, first_name, last_name, phone_number, language_code, is_bot, is_premium)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            first_name = VALUES(first_name),
            last_name = VALUES(last_name),
            phone_number = VALUES(phone_number),
            language_code = VALUES(language_code),
            is_bot = VALUES(is_bot),
            is_premium = VALUES(is_premium)
            """
            logger.info(f"Executing query: {query} with user_id={user_id}, username={username}, first_name={first_name}, last_name={last_name}, phone_number={phone_number}, language_code={user_language_code}, is_bot={is_bot}, is_premium={is_premium}")
            cursor.execute(query, (user_id, username, first_name, last_name, phone_number, user_language_code, is_bot, is_premium))
            logger.info(f"Stored user details for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to store user details: {e}")

async def store_user_async(user_id, username, first_name, last_name, phone_number=None, user_language_code=None, is_bot=None, is_premium=None):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, store_user, user_id, username, first_name, last_name, phone_number, user_language_code, is_bot, is_premium)

# Store video information
def store_video(video_id, video_details, subscribers):
    try:
        with db_cursor() as cursor:
            query = """
            INSERT INTO videos (video_id, video_title, channel_name, subscribers, view_count, like_count, comment_count, description, video_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            video_title = VALUES(video_title),
            channel_name = VALUES(channel_name),
            subscribers = VALUES(subscribers),
            view_count = VALUES(view_count),
            like_count = VALUES(like_count),
            comment_count = VALUES(comment_count),
            description = VALUES(description),
            video_link = VALUES(video_link)
            """
            logger.info(f"Executing query: {query} with video_id={video_id}, video_details={video_details}, subscribers={subscribers}")
            cursor.execute(query, (
                video_id,
                video_details['snippet']['title'],
                video_details['snippet']['channelTitle'],
                subscribers,
                video_details['statistics'].get('viewCount', 'N/A'),
                video_details['statistics'].get('likeCount', 'N/A'),
                video_details['statistics'].get('commentCount', 'N/A'),
                video_details['snippet'].get('description', ''),
                f"https://www.youtube.com/watch?v={video_id}"
            ))
            logger.info(f"Stored video details for video_id: {video_id}")
    except Exception as e:
        logger.error(f"Failed to store video details: {e}")
 
async def store_video_async(video_id, video_details, subscribers):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, store_video, video_id, video_details, subscribers)


# database.py (store_transcript_request function)
def store_transcript_request(user_id, video_id):
    try:
        with db_cursor() as cursor:
            query = """
            INSERT INTO transcript_requests (user_id, video_id)
            VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, video_id))
            request_id = cursor.lastrowid  # Get the request_id of the newly inserted row
            logger.info(f"Stored transcript request for user_id: {user_id}, video_id: {video_id}, request_id: {request_id}")
            return request_id  # Return the request_id
    except Exception as e:
        logger.error(f"Failed to store transcript request: {e}")
        raise

async def store_transcript_request_async(user_id, video_id):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, store_transcript_request, user_id, video_id)


# Store summarization request
def store_summarization_request(user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status, model, summary):
    """
    Stores a summarization request in the database.

    Args:
        user_id (int): ID of the user who made the request.
        video_id (str): ID of the video being summarized.
        language (str): Target language for the summary.
        transcript_request_id (int): ID of the associated transcript request.
        tokens_used (int): Number of tokens used for the OpenAI API call.
        estimated_cost (float): Estimated cost of the OpenAI API call.
        word_count (int): Word count of the summary.
        status (str): Status of the request (e.g., 'completed', 'failed').

    Returns:
        request_id (int): ID of the newly inserted summarization request.
    """

    try:
        with db_cursor() as cursor:
            query = """
            INSERT INTO summarization_requests (
                user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status, model, summary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status, model, summary
            ))
            request_id = cursor.lastrowid  # Get the ID of the newly inserted row
            logger.info(f"Stored summarization request for user_id: {user_id}, video_id: {video_id}, request_id: {request_id}")
            return request_id
    except Error as e:
        logger.error(f"Failed to store summarization request: {e}")
        raise

async def store_summarization_request_async(user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status, model, summary):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, store_summarization_request, user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status, model, summary)

def get_summary_by_video_language(video_id, language, model=MODEL_TO_USE):
    """
    Retrieves the summary from summarization_requests table for a given video_id, language, and status 'completed'.
    Returns the summary string if found, otherwise None.
    """
    try:
        with db_cursor() as cursor:
            query = """
            SELECT summary FROM summarization_requests
            WHERE video_id = %s AND language = %s AND model = %s AND status = 'completed' 
            ORDER BY id DESC LIMIT 1
            """
            cursor.execute(query, (video_id, language, model))
            result = cursor.fetchone()
            if result:
                logger.info(f"Summary fetched for video_id={video_id}, language={language}")
                return result[0]
            else:
                logger.info(f"Summary NOT found for video_id={video_id}, language={language}")
                return None
    except Exception as e:
        logger.error(f"Failed to fetch summary for video_id={video_id}, language={language}: {e}")
        return None
    
async def get_summary_by_video_language_async(video_id, language, model=MODEL_TO_USE):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_summary_by_video_language, video_id, language, model)

def insert_transcript(transcript_properties):
    """
    Inserts a transcript record into the transcripts table.
    """
    try:
        video_id = transcript_properties.get('video_id')
        video_title = transcript_properties.get('video_title')
        channel_name = transcript_properties.get('channel_name')
        channel_id = transcript_properties.get('channel_id')
        duration = transcript_properties.get('duration')
        video_url = transcript_properties.get('video_url')
        user_id = transcript_properties.get('user_id')
        language_code = transcript_properties.get('language_code')
        normalized_language_code = transcript_properties.get('normalized_language_code')
        is_generated = transcript_properties.get('is_generated', True)
        text = transcript_properties.get('text', '')
        filename = transcript_properties.get('filename', '')
        base_filename = transcript_properties.get('base_filename', '')
        type = transcript_properties.get('type', 'transcript')
        summary = transcript_properties.get('summary', '')
        word_count = transcript_properties.get('word_count', 0)
        tokens_used = transcript_properties.get('tokens_used', 0)
        estimated_cost = transcript_properties.get('estimated_cost', 0.0)
        model = transcript_properties.get('model', MODEL_TO_USE)

        with db_cursor() as cursor:
            query = """
            INSERT INTO transcripts (
                video_id, video_title, channel_name, channel_id, duration, video_url, 
                user_id, language_code, normalized_language_code,
                is_generated, text, filename, base_filename, type, summary, word_count,
                tokens_used, estimated_cost, model
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                video_id, video_title, channel_name, channel_id, duration, video_url, 
                user_id, language_code, normalized_language_code,
                is_generated, text, filename, base_filename, type, summary, word_count,
                tokens_used, estimated_cost, model
            ))
            logger.info(f"Inserted transcript for video_id={video_id}, user_id={user_id}, language_code={language_code}")
    except Exception as e:
        logger.error(f"Failed to insert transcript: {e}")
        raise

async def insert_transcript_async(transcript_properties):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        insert_transcript,transcript_properties
    )

def get_existing_transcripts(video_id, normalized_language_code=None):
    """
    Retrieves all transcripts from the transcripts table for a given video_id and optional language_code.
    Returns a list of transcript dicts (can be empty if none found).
    """
    try:
        with db_cursor() as cursor:
            if normalized_language_code:
                query = """
                SELECT video_id, video_title, channel_name, channel_id, duration, video_url, 
                    user_id, language_code, normalized_language_code,
                    is_generated, text, filename, base_filename, type, summary, word_count,
                    tokens_used, estimated_cost, model
                FROM transcripts
                WHERE video_id = %s AND (normalized_language_code = %s OR normalized_language_code = 'en' OR normalized_language_code = 'ru')
                ORDER BY id DESC
                """
                cursor.execute(query, (video_id, normalized_language_code))
            else:
                query = """
                SELECT video_id, video_title, channel_name, channel_id, duration, video_url, 
                    user_id, language_code, normalized_language_code,
                    is_generated, text, filename, base_filename, type, summary, word_count,
                    tokens_used, estimated_cost, model
                FROM transcripts
                WHERE video_id = %s
                ORDER BY id DESC
                """
                cursor.execute(query, (video_id,))

            rows = cursor.fetchall()
            keys = ["video_id", "video_title", "channel_name", "channel_id", "duration", "video_url", 
                    "user_id", "language_code", "normalized_language_code",
                    "is_generated", "text", "filename", "base_filename", "type", "summary", "word_count",
                    "tokens_used", "estimated_cost", "model"]
            return [dict(zip(keys, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch transcripts for video_id={video_id}, language_code={normalized_language_code}: {e}")
        return []

async def get_existing_transcripts_async(video_id, normalized_language_code=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_existing_transcripts, video_id, normalized_language_code)