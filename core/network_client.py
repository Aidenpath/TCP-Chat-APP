"""
EN: Socket client for chat communication.
中文: 聊天通信使用的 socket 客户端。

EN: This module handles TCP connect/send/receive and pushes decoded messages
upward through a callback.
中文: 本模块负责 TCP 连接/发送/接收，并通过回调把解码后的消息上抛。
"""

from __future__ import annotations

import socket
import threading
from typing import Callable

from core.protocol import decode_msg, encode_msg
from utils.logger import get_logger

logger = get_logger("Client")


class ChatClient:
    """EN: Low-level client transport. 中文: 底层客户端传输层。"""

    def __init__(self, callback: Callable[[dict], None]):
        self.socket: socket.socket | None = None
        self.username: str | None = None
        self.callback = callback
        self.running = False

    def connect(self, host: str, port: str | int, username: str) -> bool:
        """EN: Connect and send login packet. 中文: 建立连接并发送登录包。"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((host, int(port)))
            self.username = username
            self.running = True

            login_packet = {"type": "login", "username": username}
            self.socket.sendall(encode_msg(login_packet))
            logger.info("Connected to %s:%s as %s", host, port, username)
            logger.debug("Flow Controller -> Socket | packet=%s", login_packet)

            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as exc:
            logger.error("Connection failed / 连接失败: %s", exc)
            self.disconnect()
            return False

    def receive_loop(self) -> None:
        """EN: Receive server messages continuously. 中文: 持续接收服务端消息。"""
        unexpected_disconnect = False

        while self.running and self.socket:
            try:
                msg = decode_msg(self.socket)
                if msg is None:
                    # EN: None means peer closed or decode failed.
                    # 中文: None 表示对端关闭或解码失败。
                    unexpected_disconnect = self.running
                    break

                logger.debug("Flow Socket -> Controller | msg=%s", msg)
                self.callback(msg)
            except Exception as exc:
                if self.running:
                    logger.error("Receive loop error / 接收循环异常: %s", exc)
                    unexpected_disconnect = True
                break

        self.disconnect()
        if unexpected_disconnect:
            self.callback(
                {
                    "type": "system",
                    "content": "Disconnected from server. 与服务端断开连接。",
                }
            )

    def send_message(self, content: str, target: str | None = None) -> None:
        """
        EN: Send public/private chat message.
        中文: 发送公聊/私聊消息。
        """
        if not self.socket or not self.running:
            return

        msg_type = "private" if target else "public"
        msg = {"type": msg_type, "content": content}
        if target:
            msg["target"] = target

        try:
            self.socket.sendall(encode_msg(msg))
            logger.debug("Flow Controller -> Socket | msg=%s", msg)
        except Exception as exc:
            logger.error("Send failed / 发送失败: %s", exc)

    def disconnect(self) -> None:
        """EN: Close socket safely. 中文: 安全关闭 socket 连接。"""
        self.running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None
