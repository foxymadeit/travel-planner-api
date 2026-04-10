"""Client for the Art Institute of Chicago public API."""
from typing import Any, Dict, Optional

import httpx

BASE_URL = "https://api.artic.edu/api/v1"
FIELDS = "id,title,artist_display,thumbnail,image_id"


async def get_artwork(artwork_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single artwork by its numeric ID.

    Returns the raw data object from the API, or None when the artwork
    does not exist (HTTP 404).  Raises httpx.HTTPStatusError for unexpected
    server errors and httpx.RequestError for network failures.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BASE_URL}/artworks/{artwork_id}",
            params={"fields": FIELDS},
        )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json().get("data")


def extract_place_info(artwork: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Pull the fields we store locally out of an artwork response object."""
    thumbnail_url: Optional[str] = None

    if image_id := artwork.get("image_id"):
        thumbnail_url = (
            f"https://www.artic.edu/iiif/2/{image_id}/full/200,/0/default.jpg"
        )
    elif thumb := artwork.get("thumbnail"):
        thumbnail_url = thumb.get("lqip")

    return {
        "title": artwork.get("title") or "Untitled",
        "artist": artwork.get("artist_display"),
        "thumbnail_url": thumbnail_url,
    }
