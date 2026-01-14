import asyncio

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich import print_json
from rich.console import Console

from podcli import (
    download_episode,
    get_all_episodes,
    get_channel_data,
    get_latest_episode,
    listen_from_path,
)


async def main():
    console = Console()
    while True:
        choice = await inquirer.select(
            message="Do you want listen or add more to your library?",
            choices=["Listen", "Add", "Exit"],
            default="Listen",
        ).execute_async()
        if choice:
            if choice == "Add":
                feed_url = await inquirer.text(message="Enter the URL:").execute_async()
                # feed_url = "https://feeds.captivate.fm/zeroknowledge/"
                channel_data = get_channel_data(feed_url)
                latest_episode = get_latest_episode(feed_url)
                if latest_episode:
                    await download_episode(
                        latest_episode["url"],
                        latest_episode["title"],
                        channel_data["title"],
                    )
                    console.print("Download success!", style="bold green")
                else:
                    console.print(
                        "Error! Cannot download latest episode.", style="bold red"
                    )
            elif choice == "Listen":
                console.print("WIP")
                await listen_from_path(
                    "downloads/Zero Knowledge/Year in Review ZK Podcast in 2025  Beyond.mp3"
                )
            else:
                console.print("Goodbye!", style="bold green")
                break


if __name__ == "__main__":
    asyncio.run(main())
    # main()
