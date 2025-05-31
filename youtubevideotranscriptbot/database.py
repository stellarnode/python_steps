# database.py
import mysql.connector.pooling
from mysql.connector import Error
from config import DB_CONFIG
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
def store_user(user_id, username, first_name, last_name, phone_number=None):
    try:
        with db_cursor() as cursor:
            query = """
            INSERT INTO users (user_id, username, first_name, last_name, phone_number)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            first_name = VALUES(first_name),
            last_name = VALUES(last_name),
            phone_number = VALUES(phone_number)
            """
            logger.info(f"Executing query: {query} with user_id={user_id}, username={username}, first_name={first_name}, last_name={last_name}, phone_number={phone_number}")
            cursor.execute(query, (user_id, username, first_name, last_name, phone_number))
            logger.info(f"Stored user details for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to store user details: {e}")

async def store_user_async(user_id, username, first_name, last_name, phone_number=None):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, store_user, user_id, username, first_name, last_name, phone_number)

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

