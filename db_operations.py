import dbm
import pickle

import feedparser


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
