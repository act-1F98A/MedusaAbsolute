import requests
from datetime import datetime


class IntegrityError(Exception):
    """Twitch rejected the request due to integrity check."""
    pass


# Client-ID из yt-dlp — менее агрессивная проверка integrity
CLIENT_ID = "ue6666qo983tsx6so1t0vnawi233wa"
GQL_URL = "https://gql.twitch.tv/gql"

# Persisted query hash для ClipsCards__User (из yt-dlp)
CLIPS_HASH = "90c33f5e6465122fba8f9371e2a97076f9ed06c6fed3788d002ab9eba8f91d88"


def fetch_clips_page(channel_name, cursor=None, limit=20, period="ALL_TIME"):
    """Fetch one page of clips from Twitch GQL API.

    Returns:
        (clips, next_cursor) — clips is list of dicts,
        next_cursor is str or None if no more pages.
    """
    variables = {
        "login": channel_name,
        "limit": limit,
        "criteria": {
            "filter": period,
        },
    }
    if cursor:
        variables["cursor"] = cursor

    payload = [{
        "operationName": "ClipsCards__User",
        "variables": variables,
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": CLIPS_HASH,
            },
        },
    }]

    headers = {
        "Client-ID": CLIENT_ID,
        "Content-Type": "text/plain;charset=UTF-8",
    }

    response = requests.post(GQL_URL, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        data = data[0]

    if "errors" in data:
        errors = data["errors"]
        for err in errors:
            if "integrity" in err.get("message", "").lower():
                raise IntegrityError(err["message"])
        raise RuntimeError(f"Twitch GQL error: {errors}")

    user = (data.get("data") or {}).get("user")
    if not user or not user.get("clips"):
        return [], None

    edges = user["clips"]["edges"]

    clips = []
    last_cursor = None
    for edge in edges:
        node = edge.get("node")
        if not node:
            continue
        last_cursor = edge.get("cursor")

        created_at = node.get("createdAt", "")
        timestamp = None
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp())
            except (ValueError, TypeError):
                pass

        clips.append({
            "title": node.get("title", ""),
            "thumbnail": node.get("thumbnailURL"),
            "video_url": node.get("url", ""),
            "timestamp": timestamp,
            "view_count": node.get("viewCount", 0),
            "duration": node.get("durationSeconds", 0),
        })

    next_cursor = last_cursor if last_cursor and len(clips) == limit else None
    return clips, next_cursor
