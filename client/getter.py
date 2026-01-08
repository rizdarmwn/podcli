from pathlib import Path

import feedparser
import httpx

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_podcast_rss(query: str) -> str | None:
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "podcast", "limit": 5}
    response = httpx.get(url, params=params)
    try:
        json_response = response.json()
        if json_response["resultCount"] > 0:
            return json_response["results"][0]["feedUrl"]
    except Exception:
        print(response.text)
    return None


def get_latest_episode_mp3(rss_url: str) -> list[feedparser.FeedParserDict] | None:
    feed = feedparser.parse(rss_url)
    latest_episode = feed.entries[0]

    for link in latest_episode.enclosures:
        if link.type == "audio/mpeg":
            return link.href
    return None


def download_podcast(url: str, filename: str) -> Path:
    target_path = DOWNLOAD_DIR / filename

    with httpx.stream("GET", url, follow_redirects=True) as response:
        # Raise an error for bad status codes (404, 500, etc.)
        response.raise_for_status()

        with open(target_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)

    return target_path
