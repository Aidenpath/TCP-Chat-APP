"""
EN: Kivy view layer for login/chat screens.
中文: 登录/聊天界面的 Kivy 视图层。

EN: This module intentionally avoids direct socket operations.
中文: 该模块刻意不直接进行 socket 网络操作。
"""

from __future__ import annotations

from typing import Callable

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager

KV = """
ScreenManager:
    LoginScreen:
    ChatScreen:

<LoginScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            text: 'LAN Chat System'
            font_size: '24sp'
        TextInput:
            id: ip_input
            hint_text: 'Server IP (e.g. 192.168.x.x or 127.0.0.1)'
            multiline: False
        TextInput:
            id: port_input
            text: '8888'
            multiline: False
        TextInput:
            id: user_input
            hint_text: 'Enter Username'
            multiline: False
        Label:
            id: login_status_label
            text: ''
            color: 1, 0.4, 0.4, 1
            size_hint_y: 0.5
        Button:
            text: 'Connect'
            size_hint_y: 0.5
            on_release: app.on_login_pressed()

<ChatScreen>:
    name: 'chat'
    BoxLayout:
        orientation: 'horizontal'
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.3
            Label:
                text: 'Online Users'
                size_hint_y: 0.1
                color: 0.5, 0.8, 1, 1
            ScrollView:
                GridLayout:
                    id: user_list_layout
                    cols: 1
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: '40dp'
            Button:
                text: 'Exit (end)'
                size_hint_y: 0.1
                on_release: app.on_logout_pressed()

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.7
            Label:
                id: chat_target_label
                text: 'Mode: Public (Click user to private chat)'
                size_hint_y: 0.1
                color: 0.8, 1, 0.5, 1
            ScrollView:
                Label:
                    id: history_label
                    text: ''
                    size_hint_y: None
                    height: self.texture_size[1]
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'top'
                    padding: 10, 10
            BoxLayout:
                size_hint_y: 0.15
                TextInput:
                    id: msg_input
                    hint_text: 'Type a message...'
                    multiline: False
                    on_text_validate: app.on_send_pressed()
                Button:
                    text: 'Send'
                    size_hint_x: 0.3
                    on_release: app.on_send_pressed()
"""


class LoginScreen(Screen):
    pass


class ChatScreen(Screen):
    pass


class ChatApp(App):
    """
    EN: Pure UI app. External controller drives network actions.
    中文: 纯 UI 应用。网络行为由外部控制器驱动。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controller = None

    def bind_controller(self, controller) -> None:
        """EN: Inject controller dependency. 中文: 注入控制器依赖。"""
        self.controller = controller

    def build(self) -> ScreenManager:
        self.title = "Chat"
        return Builder.load_string(KV)

    def on_stop(self) -> None:
        """EN: Disconnect safely when app exits. 中文: 程序退出时安全断开连接。"""
        if self.controller:
            self.controller.shutdown()

    def run_on_ui_thread(self, fn: Callable[[], None]) -> None:
        """EN: UI thread scheduler for controller callbacks. 中文: 控制器回调的 UI 线程调度器。"""
        Clock.schedule_once(lambda _dt: fn())

    # ---------- UI event handlers (UI -> Controller) ----------
    # ---------- UI 事件处理器（UI -> 控制器） ----------

    def on_login_pressed(self) -> None:
        if not self.controller:
            self.show_login_status("Controller is not ready. 控制器尚未就绪。", is_error=True)
            return

        login_screen = self.root.get_screen("login")
        self.controller.login(
            ip=login_screen.ids.ip_input.text,
            port=login_screen.ids.port_input.text,
            username=login_screen.ids.user_input.text,
        )

    def on_send_pressed(self) -> None:
        if not self.controller:
            return

        chat_screen = self.root.get_screen("chat")
        msg = chat_screen.ids.msg_input.text
        self.controller.send_message(msg)
        chat_screen.ids.msg_input.text = ""

    def on_logout_pressed(self) -> None:
        if self.controller:
            self.controller.logout()

    def on_user_selected(self, username: str) -> None:
        if self.controller:
            self.controller.set_target(username)

    # ---------- View API (Controller -> UI) ----------
    # ---------- 视图接口（控制器 -> UI） ----------

    def show_login_status(self, text: str, is_error: bool = False) -> None:
        label = self.root.get_screen("login").ids.login_status_label
        label.text = text
        label.color = (1, 0.4, 0.4, 1) if is_error else (0.4, 1, 0.6, 1)

    def switch_to_chat(self) -> None:
        self.root.current = "chat"

    def switch_to_login(self) -> None:
        self.root.current = "login"

    def clear_history(self) -> None:
        self.root.get_screen("chat").ids.history_label.text = ""

    def append_history_line(self, text: str) -> None:
        label = self.root.get_screen("chat").ids.history_label
        label.text += text + "\n"

    def set_chat_mode_public(self) -> None:
        chat_screen = self.root.get_screen("chat")
        chat_screen.ids.chat_target_label.text = "Mode: Public"

    def set_chat_mode_private(self, username: str) -> None:
        chat_screen = self.root.get_screen("chat")
        chat_screen.ids.chat_target_label.text = f"Mode: Private -> {username}"

    def update_user_list(self, users: list[dict], current_username: str | None) -> None:
        from kivy.uix.button import Button

        layout = self.root.get_screen("chat").ids.user_list_layout
        layout.clear_widgets()

        btn_all = Button(text="[Public Chat]")
        btn_all.bind(on_release=lambda _x: self.on_user_selected("Public"))
        layout.add_widget(btn_all)

        for user in users:
            name = user.get("username", "")
            ip = user.get("ip", "")
            display_text = f"{name} (Me)" if name == current_username else f"{name}\n{ip}"
            btn = Button(text=display_text, text_size=(None, None), halign="center")
            if name != current_username:
                btn.bind(on_release=lambda _x, n=name: self.on_user_selected(n))
            layout.add_widget(btn)
