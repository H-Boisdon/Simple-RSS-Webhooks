from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

try:
    pass
except Exception:
    pass


def get_channel_logo(channel_id):
    """
    Scrapes the YouTube channel page to find the real profile picture.
    """
    if not channel_id:
        return "https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo.png"

    url = f"https://www.youtube.com/channel/{channel_id}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")

            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]

    except Exception as e:
        print(f"Error scraping logo: {e}")

    return "https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo.png"


def format_views(view_count):
    """Formats large numbers to YouTube style (e.g., 1.2K, 1.5M)."""
    try:
        num = int(view_count)
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    except (ValueError, TypeError):
        return "N/A"


def extract_youtube_data(entry):
    """
    Extracts every possible piece of data from a YouTube RSS feed entry
    using modern feedparser logic.
    """
    video_id = entry.get("yt_videoid", entry.get("id", "").split(":")[-1])
    channel_id = entry.get("yt_channelid", "")
    channel_url = (
        f"https://www.youtube.com/channel/{channel_id}"
        if channel_id
        else entry.get("author_detail", {}).get("href", "")
    )
    description = entry.get("media_description")
    summary = ""  # get_free_summary(video_id)
    media_stats = entry.get("media_statistics", {})
    star_rating = entry.get("media_starrating", {})
    views = media_stats.get("views", "0")
    likes = star_rating.get("count", "0")
    thumb_maxres = ""
    thumb_hq = ""
    if video_id:
        thumb_maxres = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        thumb_hq = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    else:
        thumbnails = entry.get("media_thumbnail", [])
        if thumbnails:
            thumb_hq = thumbnails[0].get("url", "")
            thumb_maxres = thumb_hq

    # --- 6. CONSTRUCT FINAL DICT ---
    return {
        # Core Identity
        "video_id": video_id,
        "title": entry.get("title", "Unknown Title"),
        "url": entry.get("link", ""),
        "published": entry.get("published", ""),  # String timestamp (ISO-like)
        "updated": entry.get("updated", ""),  # When the RSS entry was last modified
        # Channel Info (Useful for Footer/Author field in Embed)
        "channel_name": entry.get("author", "Unknown Channel"),
        "channel_id": channel_id,
        "channel_url": channel_url,
        "channel_icon_url": get_channel_logo(channel_id),
        # Content
        "description": description,
        "summary": summary,
        # Visuals
        "thumbnail_maxres": thumb_maxres,  # Use this for "image" -> "url"
        "thumbnail_hq": thumb_hq,  # Use this for "thumbnail" -> "url" fallback
        # Metrics (Likely to be 0 for new notifications)
        "views": views,
        "likes": likes,
    }


def create_discord_payload(video_data):
    """
    Converts extracted YouTube data into a clean, summary-focused Discord Embed.
    """
    video_summary = video_data.get("summary", "No summary available.")
    current_time_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "username": "YouTube Notifications",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/512px-YouTube_full-color_icon_%282017%29.svg.png",
        "embeds": [
            {
                "title": video_data.get("title"),
                "url": video_data.get("url"),
                "description": f"{video_summary}",
                "color": 0xFF0000,
                "timestamp": current_time_iso,
                "image": {"url": video_data.get("thumbnail_maxres")},
                "author": {
                    "name": video_data.get("channel_name"),
                    "url": video_data.get("channel_url"),
                    "icon_url": video_data.get("channel_icon_url"),
                },
                "fields": [
                    {
                        "name": "Views",
                        "value": format_views(video_data.get("views")),
                        "inline": True,
                    },
                    {
                        "name": "Likes 👍",
                        "value": format_views(video_data.get("likes")),
                        "inline": True,
                    },
                ],
                "footer": {
                    "text": "YouTube Playlist Monitor",
                },
            }
        ],
    }

    return payload
