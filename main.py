import asyncio

from client.getter import download_episode, get_episodes
from podcli import PodcliApp


async def main():
    # app = PodcliApp()
    # app.run()

    feed_url = "https://feeds.captivate.fm/zeroknowledge/"
    episodes = get_episodes(feed_url)
    print(f"Found {len(episodes)} episodes.")
    print(f"Downloading latest episode.")
    print(f"Episode title: {episodes[0]['title']}")
    await download_episode(episodes[0]["url"], episodes[0]["title"])


if __name__ == "__main__":
    asyncio.run(main())
