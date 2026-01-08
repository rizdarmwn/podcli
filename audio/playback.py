from just_playback import Playback

playback = Playback()


def play(path_to_file: str):
    playback.load_file(path_to_file)
    playback.play()


def reverse(seconds: int):
    playback.seek(playback.curr_pos - seconds)


def advance(seconds: int):
    playback.seek(playback.curr_pos + seconds)


def toggle_play():
    if playback.playing:
        playback.pause()
    elif playback.paused:
        playback.resume()
