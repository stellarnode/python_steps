# analytics.py
import logging
from config import AMPLITUDE_API_KEY
from amplitude import Amplitude, BaseEvent, Identify, EventOptions

logger = logging.getLogger(__name__)

api_key = AMPLITUDE_API_KEY
amplitude = Amplitude(api_key)
# Events queued in memory will flush when number of events exceed upload threshold
# Default value is 200
amplitude.configuration.flush_queue_size = 20


def track_event(user_id, event_type, event_properties=None):
    """
    Sends an event to Amplitude.

    :param user_id: Telegram user ID (int)
    :param event_type: Name of the event (e.g. 'start_command')
    :param event_properties: Optional dict of event metadata
    """

    if event_properties:
        try:
            user_properties={
                "username": event_properties.get("username", ""),
                "is_bot": event_properties.get("is_bot", False),
                "language_code": event_properties.get("language_code", ""),
                "is_premium": event_properties.get("is_premium", False),
                "environment": event_properties.get("environment", "production")
            }
            identify_user(user_id, user_properties, event_properties=event_properties)
        except Exception as e:
            logger.error(f"[Amplitude] Identify failed: {e}")

    event = BaseEvent(
        user_id=str(user_id),
        event_type=event_type,
        event_properties=event_properties or {},
        user_properties=event_properties or {}
    )

    try:
        amplitude.track(event)
        logger.info(f"[Amplitude] Event tracked: {event_type} for user {user_id}")
    except Exception as e:
        logger.error(f"[Amplitude] Tracking failed: {e}")


def identify_user(user_id, user_properties, event_properties=None):
    identity = Identify()
    identity.set("user_id", str(user_id))
    identity.set("username", user_properties.get("username", ""))
    identity.set("is_bot", user_properties.get("is_bot", False))
    identity.set("language_code", user_properties.get("language_code", ""))
    identity.set("is_premium", user_properties.get("is_premium", False))
    identity.set("environment", user_properties.get("environment", "production"))

    if event_properties:
        for key, value in event_properties.items():
            if key == "video_url" or key == "video_id":
                video_url = value.strip().lower()
                identity.append("video_url", video_url)

    try:
        event_options = EventOptions(user_id=str(user_id))
        amplitude.identify(identity, event_options=event_options)
        logger.info(f"[Amplitude] EventOptions type: {type(event_options)}. And here is the object itself: {event_options}")
        logger.info(f"[Amplitude] User identified: {user_id} with properties {user_properties}")
    except Exception as e:
        logger.error(f"[Amplitude] Identify failed: {e}")