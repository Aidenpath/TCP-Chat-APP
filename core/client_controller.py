"""
EN: Application-level controller between the Kivy UI and the socket client.
中文: 连接 Kivy UI 与 socket 客户端的应用层控制器。

EN: This module owns message flow orchestration so that ui/app.py stays focused
on rendering and user interactions only.
中文: 该模块负责消息流编排，让 ui/app.py 只负责界面展示和用户交互。
"""

from __future__ import annotations

from typing import Callable, Protocol

from core.network_client import ChatClient
from utils.logger import get_logger

logger = get_logger("ClientController")


class ChatView(Protocol):
    """EN: UI contract used by the controller. 中文: 控制器使用的 UI 接口约定。"""

    def run_on_ui_thread(self, fn: Callable[[], None]) -> None:
        ...

    def show_login_status(self, text: str, is_error: bool = False) -> None:
        ...

    def switch_to_chat(self) -> None:
        ...

    def switch_to_login(self) -> None:
        ...

    def clear_history(self) -> None:
        ...

    def append_history_line(self, text: str) -> None:
        ...

    def set_chat_mode_public(self) -> None:
        ...

    def set_chat_mode_private(self, username: str) -> None:
        ...

    def update_user_list(self, users: list[dict], current_username: str | None) -> None:
        ...


class ChatClientController:
    """
    EN: Coordinates UI events and network events.
    中文: 协调 UI 事件与网络事件。
    """

    def __init__(self, view: ChatView):
        self.view = view
        self.client = ChatClient(self._on_network_message)
        self.current_target: str | None = None

    def _ui(self, fn: Callable[[], None]) -> None:
        """EN: Schedule UI updates safely. 中文: 将界面更新调度到 UI 主线程。"""
        self.view.run_on_ui_thread(fn)

    def login(self, ip: str, port: str, username: str) -> None:
        """EN: Handle login request from UI. 中文: 处理 UI 发起的登录请求。"""
        ip = ip.strip()
        port = port.strip()
        username = username.strip()

        if not ip or not port or not username:
            self._ui(
                lambda: self.view.show_login_status(
                    "Please fill in IP / Port / Username. 请填写 IP / 端口 / 用户名。",
                    is_error=True,
                )
            )
            return

        if not port.isdigit():
            self._ui(
                lambda: self.view.show_login_status(
                    "Port must be a number. 端口必须是数字。",
                    is_error=True,
                )
            )
            return

        if self.client.connect(ip, port, username):
            logger.info("Login success: %s @ %s:%s", username, ip, port)
            self.current_target = None
            self._ui(lambda: self._on_login_success(ip, port))
        else:
            self._ui(
                lambda: self.view.show_login_status(
                    "Connection failed. 连接失败，请检查服务端是否可达。",
                    is_error=True,
                )
            )

    def _on_login_success(self, ip: str, port: str) -> None:
        self.view.show_login_status("Connected. 已连接。", is_error=False)
        self.view.switch_to_chat()
        self.view.clear_history()
        self.view.set_chat_mode_public()
        self.view.append_history_line(f"[System] Connected to server {ip}:{port}")

    def logout(self) -> None:
        """EN: Handle logout from UI or network. 中文: 处理 UI 或网络触发的退出。"""
        self.client.disconnect()
        self.current_target = None
        self._ui(self._on_logout_ui)

    def _on_logout_ui(self) -> None:
        self.view.switch_to_login()
        self.view.clear_history()
        self.view.set_chat_mode_public()
        self.view.show_login_status("Disconnected. 已断开连接。", is_error=False)

    def send_message(self, text: str) -> None:
        """EN: Convert UI input to socket payload. 中文: 将 UI 输入转换为 socket 消息。"""
        content = text.strip()
        if not content:
            return

        if content.lower() == "end":
            self.logout()
            return

        logger.debug(
            "Flow UI -> Controller -> Socket | user=%s target=%s content=%s",
            self.client.username,
            self.current_target,
            content,
        )
        self.client.send_message(content, self.current_target)

    def set_target(self, username: str | None) -> None:
        """EN: Switch between public/private chat target. 中文: 切换公聊/私聊目标。"""
        if not username or username == "Public" or username == self.client.username:
            self.current_target = None
            self._ui(self.view.set_chat_mode_public)
            return

        self.current_target = username
        self._ui(lambda: self.view.set_chat_mode_private(username))

    def _on_network_message(self, msg: dict) -> None:
        """
        EN: Callback from ChatClient receive thread.
        中文: 来自 ChatClient 接收线程的回调。
        """
        logger.debug("Flow Socket -> Controller | msg=%s", msg)
        self._ui(lambda: self._process_network_message(msg))

    def _process_network_message(self, msg: dict) -> None:
        msg_type = msg.get("type")

        if msg_type == "system":
            self.view.append_history_line(f"[System] {msg.get('content', '')}")
            return

        if msg_type == "public":
            self.view.append_history_line(
                f"[Public] {msg.get('sender', '')}: {msg.get('content', '')}"
            )
            return

        if msg_type == "private":
            self.view.append_history_line(
                f"[Private] {msg.get('sender', '')} -> {msg.get('target', '')}: {msg.get('content', '')}"
            )
            return

        if msg_type == "user_list":
            users = msg.get("users", [])
            online_names = {u.get("username") for u in users}
            if self.current_target and self.current_target not in online_names:
                self.current_target = None
                self.view.set_chat_mode_public()
                self.view.append_history_line(
                    "[System] Private target is offline, switched to Public mode. 私聊对象已离线，已切换到公聊模式。"
                )
            self.view.update_user_list(users, self.client.username)
            return

        logger.warning("Unknown message type from server: %s", msg_type)

    def shutdown(self) -> None:
        """EN: Explicit shutdown hook. 中文: 显式关闭入口。"""
        self.client.disconnect()
