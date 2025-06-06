# analytics.py
import logging
from config import AMPLITUDE_API_KEY
from amplitude import Amplitude, BaseEvent

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

    event = BaseEvent(
        user_id=str(user_id),
        event_type=event_type,
        event_properties=event_properties or {}
    )

    try:
        amplitude.track(event)
        logger.info(f"[Amplitude] Event tracked: {event_type} for user {user_id}")
    except Exception as e:
        logger.error(f"[Amplitude] Tracking failed: {e}")
