from pathlib import Path

import feedparser
import httpx

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_podcast_rss_from_itunes(query: str) -> str | None:
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


def get_episodes(feed_url):
    feed = feedparser.parse(feed_url)
    episodes = []
    print(feed.entries)

    for entry in feed.entries:
        # Each entry usually has one 'enclosure' containing the audio link
        if hasattr(entry, "enclosures") and len(entry.enclosures) > 0:
            mp3_url = entry.enclosures[0].href
            episodes.append(
                {"title": entry.title, "url": mp3_url, "date": entry.published}
            )
    return episodes


async def download_episode(url, title):
    # Sanitize title for filename
    filename = (
        "".join(c for c in title if c.isalnum() or c in (" ", "_")).rstrip() + ".mp3"
    )
    save_path = DOWNLOAD_DIR / filename
    save_path.parent.mkdir(exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(save_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    return save_path
