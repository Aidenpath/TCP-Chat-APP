"""
EN: Multi-client chat server based on TCP sockets.
中文: 基于 TCP socket 的多客户端聊天服务端。

EN: Responsibilities:
- accept clients
- keep online user table
- route public/private messages
- broadcast user list updates

中文: 核心职责：
- 接收客户端连接
- 维护在线用户表
- 路由公聊/私聊消息
- 广播在线用户列表变化
"""

from __future__ import annotations

import socket
import threading

from core.protocol import decode_msg, encode_msg
from utils.logger import get_logger

logger = get_logger("Server")


class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)

        # EN: {username: {"conn": socket, "ip": ip_addr}}
        # 中文: 在线用户字典，键为用户名，值为连接和 IP。
        self.clients: dict[str, dict] = {}
        self.lock = threading.Lock()

    def start(self) -> None:
        """EN: Start accept loop. 中文: 启动连接接收循环。"""
        logger.info("Server started at %s:%s", self.host, self.port)

        try:
            while True:
                conn, addr = self.server_socket.accept()
                logger.info("New TCP connection from %s:%s", addr[0], addr[1])
                threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True,
                ).start()
        except KeyboardInterrupt:
            logger.info("Server stopped by keyboard interrupt / 键盘中断关闭服务")
        finally:
            self.server_socket.close()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        """
        EN: Handle one client lifecycle.
        中文: 处理单个客户端完整生命周期。
        """
        username = None
        registered = False

        try:
            login_msg = decode_msg(conn)
            if not login_msg or login_msg.get("type") != "login":
                logger.warning("Invalid login packet from %s", addr[0])
                return

            username = (login_msg.get("username") or "").strip()
            if not username:
                logger.warning("Empty username from %s", addr[0])
                return

            with self.lock:
                if username in self.clients:
                    logger.warning("Duplicate username rejected: %s", username)
                    conn.sendall(
                        encode_msg(
                            {
                                "type": "system",
                                "content": f"Username '{username}' already exists. 用户名已存在。",
                            }
                        )
                    )
                    return

                self.clients[username] = {"conn": conn, "ip": addr[0]}
                registered = True

            logger.info("User online / 用户上线: %s (%s)", username, addr[0])
            self.broadcast_user_list()
            self.broadcast(
                {
                    "type": "system",
                    "content": f"User {username} joined the chat.",
                }
            )

            while True:
                msg = decode_msg(conn)
                if not msg:
                    break

                msg_type = msg.get("type")
                if msg_type == "public":
                    msg["sender"] = username
                    logger.debug("Flow Client -> Server -> All | msg=%s", msg)
                    self.broadcast(msg)
                elif msg_type == "private":
                    msg["sender"] = username
                    logger.debug("Flow Client -> Server -> Target | msg=%s", msg)
                    self.send_private(msg.get("target"), msg)
                else:
                    logger.warning("Unknown message type from %s: %s", username, msg_type)

        except ConnectionResetError:
            logger.info("Client connection reset: %s", username or addr[0])
        except Exception as exc:
            logger.error("handle_client error for %s: %s", username or addr[0], exc)
        finally:
            if registered and username:
                self.remove_client(username)
            else:
                try:
                    conn.close()
                except OSError:
                    pass

    def _send_to_user(self, username: str, data: bytes) -> bool:
        """EN: Send encoded bytes to a user. 中文: 向指定用户发送编码后的字节数据。"""
        with self.lock:
            info = self.clients.get(username)

        if not info:
            return False

        try:
            info["conn"].sendall(data)
            return True
        except Exception:
            return False

    def broadcast(self, msg_dict: dict) -> None:
        """EN: Broadcast message to all users. 中文: 向所有在线用户广播消息。"""
        data = encode_msg(msg_dict)
        with self.lock:
            user_list = list(self.clients.keys())

        for user in user_list:
            self._send_to_user(user, data)

    def send_private(self, target_user: str | None, msg_dict: dict) -> None:
        """
        EN: Send private message to target, then echo to sender.
        中文: 私聊消息先发给目标，再回显给发送者。
        """
        sender = msg_dict.get("sender")
        if not target_user:
            return

        data = encode_msg(msg_dict)
        target_ok = self._send_to_user(target_user, data)

        # EN: Sender sees their own private message in UI as well.
        # 中文: 让发送者也能在 UI 看到自己发出的私聊。
        if sender and sender != target_user:
            self._send_to_user(sender, data)

        if not target_ok and sender:
            self._send_to_user(
                sender,
                encode_msg(
                    {
                        "type": "system",
                        "content": f"User '{target_user}' is offline. 用户不在线。",
                    }
                ),
            )

    def broadcast_user_list(self) -> None:
        """EN: Broadcast current online users. 中文: 广播当前在线用户列表。"""
        with self.lock:
            users = [{"username": k, "ip": v["ip"]} for k, v in self.clients.items()]

        logger.debug("Broadcast user list / 广播在线列表: %s", users)
        self.broadcast({"type": "user_list", "users": users})

    def remove_client(self, username: str) -> None:
        """EN: Remove offline user and notify everyone. 中文: 移除离线用户并通知所有人。"""
        with self.lock:
            info = self.clients.pop(username, None)

        if info:
            try:
                info["conn"].close()
            except OSError:
                pass

            logger.info("User offline / 用户下线: %s", username)
            self.broadcast_user_list()
            self.broadcast(
                {
                    "type": "system",
                    "content": f"User {username} left the chat.",
                }
            )
