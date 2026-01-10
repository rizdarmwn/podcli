from pathlib import Path
from time import sleep

import feedparser
import httpx
import just_playback
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

pb = just_playback.Playback()
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def listen_from_path(path):
    with Progress(
        TextColumn("{task.fields[icon]}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        if not pb.active:
            pb.load_file(path)
            pb.play()
        else:
            pb.resume()
        duration = pb.duration
        task_id = progress.add_task("Playing", total=duration, icon="▶")
        while pb.active:
            if pb.playing:
                current_icon = "▶"
                current_pos = pb.curr_pos
                progress.update(task_id, completed=current_pos, icon=current_icon)
            sleep(0.1)

            if pb.paused:
                current_icon = "Ⅱ"
                pass


def get_podcast_rss_from_itunes(query: str) -> str | None:
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "podcast", "limit": 5}
    response = httpx.get(url, params=params)
    try:
        json_response = response.json()
        if json_response["resultCount"] > 0:
            return json_response["results"][0]["feedUrl"]
    except Exception:
        return response.text
    return None


def get_channel_data(rss_url: str):
    d = feedparser.parse(rss_url)

    return {
        "title": d.feed.title,
        "link": d.feed.link,
        "description": d.feed.description,
    }


def get_latest_episode(rss_url: str):
    d = feedparser.parse(rss_url)
    latest_episode = d.entries[0]

    if latest_episode.enclosures[0].type == "audio/mpeg":
        episode = {
            "title": latest_episode.title,
            "url": latest_episode.enclosures[0].href,
            "date": latest_episode.published,
            "duration": latest_episode.enclosures[0].length,
            "link": latest_episode.link,
            "description": latest_episode.description,
            "id": latest_episode.id,
        }
        return episode
    return None


def get_all_episodes(rss_url):
    d = feedparser.parse(rss_url)
    episodes = []

    for entry in d.entries:
        if hasattr(entry, "enclosures") and len(entry.enclosures) > 0:
            mp3_url = entry.enclosures[0].href
            episodes.append(
                {
                    "title": entry.title,
                    "url": mp3_url,
                    "date": entry.published,
                    "duration": entry.enclosures[0].length,
                    "link": entry.link,
                    "description": entry.description,
                    "id": entry.id,
                }
            )
    return episodes


async def download_episode(url: str, title: str, channel_name: str):
    filename = (
        "".join(c for c in title if c.isalnum() or c in (" ", "_")).rstrip() + ".mp3"
    )
    save_path = DOWNLOAD_DIR / channel_name / filename
    save_path.parent.mkdir(exist_ok=True)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        "eta",
        TimeRemainingColumn(),
    ) as progress:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                task_id = progress.add_task(
                    f"Downloading {title[:20]}...", total=total_size
                )
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))
