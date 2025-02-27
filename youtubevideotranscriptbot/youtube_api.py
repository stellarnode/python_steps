# youtube_api.py
import re
from googleapiclient.discovery import build
from config import API_KEY
import logging

logger = logging.getLogger(__name__)

# Extract video ID from various YouTube link formats
def extract_video_id(url):
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)",  # Standard video links
        r"(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)",              # Shortened links
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/live\/([a-zA-Z0-9_-]+)",     # Live stream links
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)",    # Embedded links
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]+)"         # Deprecated /v/ links
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Get video details using YouTube Data API
def get_video_details(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.videos().list(
        part='snippet,statistics,contentDetails',  # Include contentDetails for duration
        id=video_id
    )
    response = request.execute()
    return response['items'][0]

# Get channel subscribers
def get_channel_subscribers(channel_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.channels().list(
        part='statistics',
        id=channel_id
    )
    response = request.execute()
    if response['items']:
        return response['items'][0]['statistics']['subscriberCount']
    return 'N/A'