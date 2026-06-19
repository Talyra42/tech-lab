from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, DataTable
from textual.containers import Vertical


class MyApp(App):
    TITLE = "Github 仓库浏览器"
    CSS_PATH = "App.tcss"

    BINDINGS = [("q", "quit", "退出"), ("/", "focus('search_input')", "聚焦搜索框")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main_container"):
            yield Input(placeholder="请输入仓库名称", id="search_input")
            yield DataTable(show_header=True, id="res_table")
        yield Footer()

    def on_mount(self):
        tb = self.query_one("#res_table", DataTable)
        tb.add_column("Title")
        tb.add_column("Stars")
        tb.add_column("Forks")
        tb.add_column("Description")
        tb.cursor_type = "row"


if __name__ == "__main__":
    MyApp().run()
