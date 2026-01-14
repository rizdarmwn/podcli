import asyncio
import dbm
import pickle
from pathlib import Path

import feedparser
import httpx
import just_playback
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import PromptSession
from rich import print_json
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressBar,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from utils import format_time

pb = just_playback.Playback()
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_player_ui():
    current_pos = pb.curr_pos
    duration = pb.duration
    icon = "▶" if pb.playing else "Ⅱ"

    time_display = f"{format_time(current_pos)}/{format_time(duration)}"

    bar = ProgressBar(total=duration, completed=current_pos)

    return Panel(
        Group(
            f"{icon} Playing",
            "",
            Columns([bar, f"[bold white]{time_display}[/bold white]"], expand=False),
        ),
        title="Podcast Player",
        border_style="cyan",
    )


async def listen_from_path(path):
    if not pb.active:
        pb.load_file(str(path))
        pb.play()

    kb = KeyBindings()

    @kb.add("space")
    def _(event):
        if pb.playing:
            pb.pause()
        else:
            pb.resume()

    @kb.add("q")
    def _(event):
        pb.stop()
        event.app.exit()

    @kb.add("right")
    def _(event):
        pb.seek(pb.curr_pos + 30)

    @kb.add("left")
    def _(event):
        pb.seek(pb.curr_pos - 30)

    session = PromptSession(key_bindings=kb)

    async def update_ui(live_display):
        while pb.active:
            live_display.update(get_player_ui())
            await asyncio.sleep(0.1)

    print(
        "Press [Space] to Pause, [Q] to Quit, [Right Arrow] to skip +30s, [Left Arrow] to reverse -30s"
    )
    with Live(get_player_ui(), refresh_per_second=10) as live:
        ui_task = asyncio.create_task(update_ui(live))
        try:
            await session.prompt_async(message="")
        finally:
            ui_task.cancel()
            pb.stop()


def get_channel_data(rss_url: str):
    d = feedparser.parse(rss_url)
    data = {
        "title": d.feed.title,
        "link": d.feed.link,
        "description": d.feed.description,
        "rss_url": rss_url,
    }
    save_channel_data_to_file(data)
    return data


def get_all_channel_data_from_file():
    db = dbm.open("channeldb", "r")
    return db.items()


def get_channel_data_from_file(key):
    db = dbm.open("channeldb", "r")
    return pickle.loads(db[key])


def get_episode_data_from_file(channel_title, key):
    db = dbm.open("episodedb", "r")
    episodes = pickle.loads(db[channel_title])
    return episodes[key]


def get_all_episodes_from_channel_from_file(channel_title):
    db = dbm.open("episodedb", "r")
    episodes = pickle.loads(db[channel_title])
    return dict(
        sorted(episodes.items(), key=lambda x: x[1]["date_parsed"], reverse=True)
    )


def save_channel_data_to_file(data):
    db = dbm.open("channeldb", "c")
    db[data["title"]] = pickle.dumps(data)
    db.close()


def save_episode_data_to_file(key, data):
    db = dbm.open("episodedb", "c")
    if key in db:
        episodes = pickle.loads(db[key])
        if data["id"] not in episodes:
            db[key] = pickle.dumps({**episodes, data["id"]: data})
    else:
        db[key] = pickle.dumps({data["id"]: data})
    db.close()


def update_episode_path_to_file(key, episode_id, path):
    db = dbm.open("episodedb", "c")
    data = pickle.loads(db[key])
    data[episode_id]["path"] = path
    db[key] = pickle.dumps(data)
    db.close()


def get_latest_episode(channel_name: str, rss_url: str):
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
            "date_parsed": latest_episode.published_parsed,
        }
        save_episode_data_to_file(channel_name, episode)
        return episode
    return None


def get_all_episodes(channel_name, rss_url):
    d = feedparser.parse(rss_url)
    episodes = []

    for entry in d.entries:
        if hasattr(entry, "enclosures") and len(entry.enclosures) > 0:
            mp3_url = entry.enclosures[0].href
            episode = {
                "title": entry.title,
                "url": mp3_url,
                "date": entry.published,
                "duration": entry.enclosures[0].length,
                "link": entry.link,
                "description": entry.description,
                "id": entry.id,
                "date_parsed": entry.published_parsed,
            }
            episodes.append(episode)
            save_episode_data_to_file(channel_name, episode)
    return episodes


async def download_episode(url: str, title: str, id: str, channel_name: str):
    filename = id + ".mp3"
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

    update_episode_path_to_file(channel_name, id, save_path)
    return save_path
