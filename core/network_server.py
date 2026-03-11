'''
负责处理用户的上线、下线，保存用户的用户名和 IP，并将消息广播或定向发送 。
'''
import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

logger = get_logger("Server")

class ChatServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        # clients dict format: {username: {"conn": socket, "ip": ip_addr}}
        self.clients = {}
        self.lock = threading.Lock()

    def start(self):
        logger.info(f"Server started, listening on {self.host}:{self.port}, waiting for connections...")
        try:
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Server shut down.")
            self.server_socket.close()

    def handle_client(self, conn, addr):
        username = None
        try:
            # Wait for login message
            login_msg = decode_msg(conn)
            if login_msg and login_msg.get("type") == "login":
                username = login_msg.get("username")
                with self.lock:
                    self.clients[username] = {"conn": conn, "ip": addr[0]}
                logger.info(f"User {username} ({addr[0]}) connected.")
                self.broadcast_user_list()
                # 修改这里：将系统通知改为英文
                self.broadcast({"type": "system", "content": f"User {username} joined the chat."})

            # Loop to handle chat messages
            while True:
                msg = decode_msg(conn)
                if not msg:
                    break  # Client disconnected
                
                # Handle public and private routing
                if msg.get("type") == "public":
                    msg["sender"] = username
                    self.broadcast(msg)
                elif msg.get("type") == "private":
                    msg["sender"] = username
                    self.send_private(msg.get("target"), msg)

        except ConnectionResetError:
            pass
        finally:
            if username:
                self.remove_client(username)

    def broadcast(self, msg_dict):
        """Send message to all users"""
        data = encode_msg(msg_dict)
        with self.lock:
            for user, info in self.clients.items():
                try:
                    info["conn"].sendall(data)
                except Exception:
                    pass

    def send_private(self, target_user, msg_dict):
        """Send direct message to a specific user"""
        data = encode_msg(msg_dict)
        with self.lock:
            if target_user in self.clients:
                try:
                    self.clients[target_user]["conn"].sendall(data)
                    # Send back to sender for local display
                    sender = msg_dict.get("sender")
                    if sender != target_user and sender in self.clients:
                        self.clients[sender]["conn"].sendall(data)
                except Exception as e:
                    logger.error(f"Private message failed: {e}")

    def broadcast_user_list(self):
        """Broadcast online user list"""
        with self.lock:
            users = [{"username": k, "ip": v["ip"]} for k, v in self.clients.items()]
        self.broadcast({"type": "user_list", "users": users})

    def remove_client(self, username):
        """Handle user disconnect"""
        with self.lock:
            if username in self.clients:
                self.clients[username]["conn"].close()
                del self.clients[username]
        logger.info(f"User {username} disconnected.")
        self.broadcast_user_list()
        # 修改这里：将系统通知改为英文
        self.broadcast({"type": "system", "content": f"User {username} left the chat."})