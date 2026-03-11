'''
负责将消息打包为 [4字节长度头] + [JSON数据] 的格式，
解决 TCP 粘包/半包问题的工业标准做法，替代脆弱的单字符头标签 。
'''
import json
import struct

def encode_msg(msg_dict: dict) -> bytes:
    """将字典序列化为JSON，并加上4字节的长度头"""
    json_bytes = json.dumps(msg_dict, ensure_ascii=False).encode('utf-8')
    # 采用网络字节序(大端)打包长度
    header = struct.pack('>I', len(json_bytes))
    return header + json_bytes

def decode_msg(conn) -> dict | None:
    """从Socket连接中安全读取一个完整的JSON消息，具有中断性质"""
    try:
        # 1. 读取4字节长度头
        header = conn.recv(4) # 中断
        if not header or len(header) < 4:
            return None
        msg_len = struct.unpack('>I', header)[0]
        
        # 2. 根据长度读取消息体
        data = b''
        while len(data) < msg_len:
            packet = conn.recv(msg_len - len(data))
            if not packet:
                return None
            data += packet
        return json.loads(data.decode('utf-8'))
    except Exception:
        return None