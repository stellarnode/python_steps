# duration.py
import isodate
import logging

logger = logging.getLogger(__name__)

# Convert ISO 8601 duration to a human-readable format
def format_duration(duration_iso):
    try:
        # Parse the ISO 8601 duration
        duration = isodate.parse_duration(duration_iso)
        
        # Extract hours, minutes, and seconds
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # Format the duration
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except Exception as e:
        logger.error(f"Failed to parse duration: {e}")
        return "N/A"