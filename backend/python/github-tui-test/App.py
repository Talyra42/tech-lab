from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.containers import Vertical
from textual import on
from SearchBar import SearchBar


class MyApp(App):
    TITLE = "Github 仓库浏览器"
    CSS_PATH = "App.tcss"

    BINDINGS = [("q", "quit", "退出"), ("/", "focus('search_bar')", "聚焦搜索框")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main_container"):
            yield SearchBar(id="search_bar")
            yield DataTable(show_header=True, id="res_table")
        yield Footer()

    def on_mount(self):
        tb = self.query_one("#res_table", DataTable)
        tb.add_column("Title")
        tb.add_column("Stars")
        tb.add_column("Forks")
        tb.add_column("Description")
        tb.cursor_type = "row"

    @on(SearchBar.Submitted)
    def handle_search(self, e: SearchBar.Submitted):
        self.notify(e.value)


if __name__ == "__main__":
    MyApp().run()
