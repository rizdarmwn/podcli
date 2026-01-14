import asyncio
import pickle

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich import print_json
from rich.console import Console

from podcli import (
    download_episode,
    get_all_channel_data_from_file,
    get_all_episodes,
    get_all_episodes_from_channel_from_file,
    get_channel_data,
    get_episode_data_from_file,
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
                feed_url = await inquirer.text(
                    message="Enter the URL (RSS feeds only):"
                ).execute_async()
                # feed_url = "https://feeds.captivate.fm/zeroknowledge/"
                channel_data = get_channel_data(feed_url)
                latest_episode = get_latest_episode(channel_data["title"], feed_url)
                with console.status(
                    "[bold green]Getting all episodes metadata..."
                ) as status:
                    get_all_episodes(channel_data["title"], channel_data["rss_url"])

                if latest_episode:
                    await download_episode(
                        latest_episode["url"],
                        latest_episode["title"],
                        latest_episode["id"],
                        channel_data["title"],
                    )
                    console.print(
                        "Latest episode download success!", style="bold green"
                    )
                else:
                    console.print(
                        "Error! Cannot download latest episode.", style="bold red"
                    )
            elif choice == "Listen":
                choices = get_all_channel_data_from_file()
                channel_data = await inquirer.fuzzy(
                    message="Which podcast do you want to listen?",
                    choices=["[Go Back]"]
                    + [
                        Choice(value=pickle.loads(v), name=str(key, "utf-8"))
                        for key, v in choices
                    ],
                    vi_mode=True,
                    instruction="[Type to search podcast]",
                ).execute_async()

                if channel_data == "[Go Back]":
                    continue

                episodes = get_all_episodes_from_channel_from_file(
                    channel_data["title"]
                )

                choice = await inquirer.fuzzy(
                    message="Which episode?",
                    choices=["[Go Back]"]
                    + [
                        Choice(
                            value=k,
                            name=f"{v['title']} {'[Downloaded]' if v.get('path') else ''}",
                        )
                        for k, v in episodes.items()
                    ],
                    vi_mode=True,
                    instruction="[Type to search episode]",
                ).execute_async()

                if choice == "[Go Back]":
                    continue

                episode = get_episode_data_from_file(channel_data["title"], choice)
                if "path" in episode:
                    await listen_from_path(episode["path"])
                else:
                    path = await download_episode(
                        episode["url"],
                        episode["title"],
                        episode["id"],
                        channel_data["title"],
                    )
                    await listen_from_path(path)

            else:
                console.print("Goodbye!", style="bold green")
                break


if __name__ == "__main__":
    asyncio.run(main())
    # main()
