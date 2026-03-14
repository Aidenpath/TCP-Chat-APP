"""
EN: Server entry point.
中文: 服务端启动入口。
"""

from __future__ import annotations

from core.network_server import ChatServer


def main() -> None:
    print("正在启动服务端... / Starting server...")
    # EN: Bind 0.0.0.0 so LAN devices can connect.
    # 中文: 绑定 0.0.0.0，允许局域网内设备连接。
    server = ChatServer(host="0.0.0.0", port=8888)
    server.start()


if __name__ == "__main__":
    main()
