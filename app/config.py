
import os


def get_youtube_api_key() -> str | None:
    """
    Read the YouTube API key from environment variables.

    Return None when the key is not configured.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        return None

    return api_key.strip() or None
