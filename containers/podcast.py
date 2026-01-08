from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Button, ProgressBar


class Podcast(HorizontalGroup):
    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Pause", id="pause", variant="warning")
        yield ProgressBar(id="pbar", show_eta=True, show_percentage=False, total=100)
