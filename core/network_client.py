import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

logger = get_logger("Client")

class ChatClient:
    def __init__(self, callback):
        self.socket = None
        self.username = None
        self.callback = callback  # 用于将接收到的消息回调给UI主线程
        self.running = False

    def connect(self, host, port, username):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, int(port)))
            self.username = username
            self.running = True
            
            # 发送登录包 [cite: 19]
            login_packet = {"type": "login", "username": username}
            self.socket.sendall(encode_msg(login_packet))
            
            # 开启接收线程
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def receive_loop(self):
        while self.running:
            try:
                msg = decode_msg(self.socket)
                if msg:
                    self.callback(msg)
                else:
                    break
            except Exception:
                break
        self.disconnect()
        self.callback({"type": "system", "content": "unlink from server!!"})

    def send_message(self, content, target=None):
        if not self.socket or not self.running:
            return
        # 根据有无 target 区分公聊/私聊 [cite: 18]
        msg_type = "private" if target else "public"
        msg = {"type": msg_type, "content": content}
        if target:
            msg["target"] = target
        try:
            self.socket.sendall(encode_msg(msg))
        except Exception as e:
            logger.error(f"发送失败: {e}")

    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None