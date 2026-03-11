'''
负责用户交互，包含登录、群聊、私聊界面，显示在线用户和消息历史 。
'''
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from core.network_client import ChatClient

KV = '''
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
        Button:
            text: 'Connect'
            size_hint_y: 0.5
            on_release: app.login()

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
                on_release: app.logout()

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
                    on_text_validate: app.send_msg()
                Button:
                    text: 'Send'
                    size_hint_x: 0.3
                    on_release: app.send_msg()
'''

class LoginScreen(Screen): pass
class ChatScreen(Screen): pass

class ChatApp(App):
    def build(self):
        self.client = ChatClient(self.on_message_received)
        self.current_target = None  
        self.title = 'Chat'
        return Builder.load_string(KV)

    def login(self):
        login_screen = self.root.get_screen('login')
        ip = login_screen.ids.ip_input.text.strip()
        port = login_screen.ids.port_input.text.strip()
        username = login_screen.ids.user_input.text.strip()

        if ip and port and username:
            if self.client.connect(ip, port, username):
                self.root.current = 'chat'
                self.print_history(f"[System] Connected to server {ip}:{port}")
            else:
                self.print_history("[Error] Connection failed. Check IP and server status.")

    def logout(self):
        self.client.disconnect()
        self.root.current = 'login'
        self.root.get_screen('chat').ids.history_label.text = ''

    def send_msg(self):
        chat_screen = self.root.get_screen('chat')
        msg = chat_screen.ids.msg_input.text.strip()
        if msg:
            if msg.lower() == 'end':  
                self.logout()
                return
            self.client.send_message(msg, self.current_target)
            chat_screen.ids.msg_input.text = ''

    def set_target(self, username):
        chat_screen = self.root.get_screen('chat')
        if username == self.client.username or username == "Public":
            self.current_target = None
            chat_screen.ids.chat_target_label.text = 'Mode: Public'
        else:
            self.current_target = username
            chat_screen.ids.chat_target_label.text = f'Mode: Private -> {username}'

    def on_message_received(self, msg):
        Clock.schedule_once(lambda dt: self._process_message(msg))

    def _process_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == "system":
            self.print_history(f"[System] {msg.get('content')}")
        elif msg_type == "public":
            self.print_history(f"[Public] {msg.get('sender')}: {msg.get('content')}")
        elif msg_type == "private":
            self.print_history(f"[Private] {msg.get('sender')} -> {msg.get('target')}: {msg.get('content')}")
        elif msg_type == "user_list":
            self.update_user_list(msg.get("users"))

    def print_history(self, text):
        label = self.root.get_screen('chat').ids.history_label
        label.text += text + "\n"

    def update_user_list(self, users):
        from kivy.uix.button import Button
        layout = self.root.get_screen('chat').ids.user_list_layout
        layout.clear_widgets()
        
        btn_all = Button(text="[Public Chat]")
        btn_all.bind(on_release=lambda x: self.set_target("Public"))
        layout.add_widget(btn_all)

        for u in users:
            name = u['username']
            ip = u['ip']
            display_text = f"{name} (Me)" if name == self.client.username else f"{name}\n{ip}"
            btn = Button(text=display_text, text_size=(None, None), halign='center')
            if name != self.client.username:
                btn.bind(on_release=lambda x, n=name: self.set_target(n))
            layout.add_widget(btn)