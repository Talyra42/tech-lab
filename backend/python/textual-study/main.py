from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button


class SettingsScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "返回")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("这里是设置")
        yield Button("返回", id="back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        # 关掉自己，回到上一个屏幕
        self.app.pop_screen()
