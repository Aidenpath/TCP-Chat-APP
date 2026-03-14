"""
EN: Length-prefixed JSON protocol utilities.
中文: 基于长度头的 JSON 协议工具。

EN: Packet format = [4-byte big-endian length][JSON bytes].
中文: 数据包格式 = [4 字节大端长度头][JSON 字节数据]。
"""

from __future__ import annotations

import json
import struct


def encode_msg(msg_dict: dict) -> bytes:
    """EN: Dict -> bytes packet. 中文: 字典 -> 字节数据包。"""
    json_bytes = json.dumps(msg_dict, ensure_ascii=False).encode("utf-8")
    header = struct.pack(">I", len(json_bytes))
    return header + json_bytes


def _recv_exact(conn, size: int) -> bytes | None:
    """
    EN: Read exactly `size` bytes from socket.
    中文: 从 socket 精确读取 `size` 个字节。
    """
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data


def decode_msg(conn) -> dict | None:
    """EN: bytes packet -> dict. 中文: 字节数据包 -> 字典。"""
    try:
        header = _recv_exact(conn, 4)
        if header is None:
            return None

        msg_len = struct.unpack(">I", header)[0]
        body = _recv_exact(conn, msg_len)
        if body is None:
            return None

        return json.loads(body.decode("utf-8"))
    except Exception:
        return None
