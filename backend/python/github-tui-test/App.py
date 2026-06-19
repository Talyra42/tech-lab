from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.containers import Vertical
from textual import on, work
from SearchBar import SearchBar
import httpx

BASE_URL = "https://api.github.com/search/repositories"


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
        self.search_repos(e.value)

    # 专门的搜索方法，通过 work 驱动
    @work(exclusive=True)
    async def search_repos(self, keyword: str):
        # 获取表格 方便后续操作
        tb = self.query_one("#res_table", DataTable)

        try:
            async with httpx.AsyncClient() as client:
                # 获取数据
                response = await client.get(
                    BASE_URL, params={"q": keyword, "per_page": 20}
                )
                res = response.json()["items"]

                # 清空表格
                tb.clear()

                # 放入数据
                for i in res:
                    tb.add_row(
                        i["full_name"],
                        i["stargazers_count"],
                        i["forks_count"],
                        i["description"] or "",
                    )
        except Exception as err:
            self.notify(f"搜索失败：{err}", severity="error")


if __name__ == "__main__":
    MyApp().run()
