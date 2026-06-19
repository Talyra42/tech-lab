from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input
from textual import on


class SearchBar(Widget):
    DEFAULT_CSS = """
    SearchBar {
        height: auto;
    }

    #default_search_id {
        margin-bottom: 1;
        border: tall $accent;
    }

    #default_search_id:focus {
        border: tall $primary;
    }
    """

    class Submitted(Message):
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="请输入关键词...", id="default_search_id")

    @on(Input.Submitted, "#default_search_id")
    def handle_submit(self, e: Input.Submitted):
        self.post_message(self.Submitted(e.value))
        e.stop()
