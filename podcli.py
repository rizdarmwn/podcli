from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, ProgressBar

import audio.playback as pb
from containers.podcast import Podcast


class PodcliApp(App):
    """Textual app to listen to podcasts"""

    CSS_PATH = "css/podcast.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("h", "reverse", "Prev 10s"),
        ("l", "advance", "Next 10s"),
        ("space", "toggle_play", "Play/Pause"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield VerticalScroll(Podcast())

    def action_reverse(self) -> None:
        pb.reverse(-10)
        self.query_one(ProgressBar).advance(-10)

    def action_advance(self) -> None:
        pb.advance(10)
        self.query_one(ProgressBar).advance(10)

    def action_toggle_play(self) -> None:
        pb.toggle_play()
