# database.py
import mysql.connector.pooling
from mysql.connector import Error
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

# Create a connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="bot_pool",
    pool_size=5,  # Adjust based on your needs
    **DB_CONFIG
)

# Connect to MySQL database using the connection pool
def get_db_connection():
    try:
        conn = db_pool.get_connection()
        logger.info("Connected to the database.")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise

# Store user information
def store_user(user_id, username, first_name, last_name, phone_number=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
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
        conn.commit()
        logger.info(f"Stored user details for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to store user details: {e}")
    finally:
        cursor.close()
        conn.close()

# Store video information
def store_video(video_id, video_details, subscribers):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
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
        conn.commit()
        logger.info(f"Stored video details for video_id: {video_id}")
    except Exception as e:
        logger.error(f"Failed to store video details: {e}")
    finally:
        cursor.close()
        conn.close()

# database.py (store_transcript_request function)
def store_transcript_request(user_id, video_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO transcript_requests (user_id, video_id)
        VALUES (%s, %s)
        """
        cursor.execute(query, (user_id, video_id))
        conn.commit()
        request_id = cursor.lastrowid  # Get the request_id of the newly inserted row
        logger.info(f"Stored transcript request for user_id: {user_id}, video_id: {video_id}, request_id: {request_id}")
        return request_id  # Return the request_id
    except Exception as e:
        logger.error(f"Failed to store transcript request: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

# Store summarization request
def store_summarization_request(user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status):
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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO summarization_requests (
            user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            user_id, video_id, language, transcript_request_id, tokens_used, estimated_cost, word_count, status
        ))
        conn.commit()
        request_id = cursor.lastrowid  # Get the ID of the newly inserted row
        logger.info(f"Stored summarization request for user_id: {user_id}, video_id: {video_id}, request_id: {request_id}")
        return request_id
    except Error as e:
        logger.error(f"Failed to store summarization request: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
