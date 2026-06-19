from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.containers import Vertical


class RepoDetail(ModalScreen):
    DEFAULT_CSS = """
    RepoDetail {
        align: center middle;        /* 第六讲：让 #dialog 在屏幕居中 */
    }
    #dialog {
        width: 60;                   /* 对话框固定宽度 */
        height: auto;                /* 高度随内容自适应 */
        max-width: 80%;              /* 窗口太窄时不超过 80% */
        padding: 1 2;                /* 内边距 */
        border: round $primary;      /* 圆角边框 + 主题色 */
        background: $surface;        /* 背景，主题变量 */
    }
    #dialog Label {
        margin-bottom: 1;            /* 每行之间留点空隙 */
        width: 100%;
    }
    #close_modal {
        margin-top: 1;
        width: 100%;                 /* 关闭按钮占满宽度 */
    }
    """
    BINDINGS = [("escape", "dismiss", "关闭")]

    def __init__(self, repo) -> None:
        self.repo = repo
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"仓库：{self.repo['full_name']}")
            yield Label(f"描述：{self.repo['description'] or '无'}")
            yield Label(f"语言：{self.repo['language'] or '未知'}")
            yield Label(f"⭐ Stars：{self.repo['stargazers_count']}")
            yield Label(f"🍴 Forks：{self.repo['forks_count']}")
            yield Label(f"Issues：{self.repo['open_issues_count']}")
            yield Label(f"链接：{self.repo['html_url']}")
            yield Button("关闭", id="close_modal")

    def on_button_pressed(self, e: Button.Pressed):
        self.dismiss()
