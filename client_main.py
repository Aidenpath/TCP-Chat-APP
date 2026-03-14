"""
EN: Client entry point. Wires UI and controller together.
中文: 客户端启动入口。负责组装 UI 与控制器。
"""

from __future__ import annotations

import os

from kivy.core.text import LabelBase

from core.client_controller import ChatClientController
from ui.app import ChatApp


# EN: Replace Kivy default font (Roboto) to avoid missing Chinese glyphs.
# 中文: 替换 Kivy 默认字体（Roboto），避免中文缺字显示为方块。
LabelBase.register(name="Roboto", fn_regular="NotoSansCJK-Black.ttc")


def main() -> None:
    # EN: Use PIL text backend for better CJK compatibility on some systems.
    # 中文: 部分系统下使用 PIL 文本后端可提升中日韩文字兼容性。
    os.environ.setdefault("KIVY_TEXT", "pil")

    app = ChatApp()
    controller = ChatClientController(app)
    app.bind_controller(controller)
    app.run()


if __name__ == "__main__":
    main()
