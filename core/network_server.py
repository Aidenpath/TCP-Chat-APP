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
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 使用TCP协议
        self.server_socket.bind((self.host, self.port)) # 绑定地址和端口
        self.server_socket.listen(10) # 最大接受的等待连接数
        # clients dict format: {username: {"conn": socket, "ip": ip_addr}}
        self.clients = {}
        self.lock = threading.Lock()
    
    # 初始化监听Socket，用于TCP连接
    def start(self):
        logger.info(f"Server started, listening on {self.host}:{self.port}, waiting for connections...")
        try:
            while True:
                conn, addr = self.server_socket.accept() # TCP握手协议，成功后返回（新的用于传输数据的socket，连接的IP），原本的socket用于监听
                # 为该数据传输socket建立守护线程（守护线程：当主线程退出时，Python 会强制杀死所有守护线程，程序立刻结束（意味着当server被终止时所有client将失去连接）；否则，主线程必须的确认所有非守护线程结束后才能退出）
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Server shut down.")
            self.server_socket.close()
    # 处理来自客户端的请求与信息
    def handle_client(self, conn, addr):
        username = None
        try:
            # Wait for login message
            login_msg = decode_msg(conn) # 解码来自client的信息
            if login_msg and login_msg.get("type") == "login":
                username = login_msg.get("username")
                # 获取互斥锁，从而存储登入的client
                with self.lock: 
                    self.clients[username] = {"conn": conn, "ip": addr[0]}
                logger.info(f"User {username} ({addr[0]}) connected.")
                '''下面的广播信息将被处理，作为UI页面上不同位置的显示'''
                # 广播当前在线用户
                self.broadcast_user_list()
                # 修改这里：将系统通知改为英文
                self.broadcast({"type": "system", "content": f"User {username} joined the chat."})

            # 循环处理
            while True:
                msg = decode_msg(conn)
                if not msg:
                    break  # 客户端无消息
                
                # 处理公共消息和私人消息
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
        """公共消息广播：发送给所有用户"""
        data = encode_msg(msg_dict)
        with self.lock:
            # 遍历每个用户并发送信息，sendall是python内置的循环发送函数
            for user, info in self.clients.items(): 
                try:
                    info["conn"].sendall(data)
                except Exception:
                    pass

    def send_private(self, target_user, msg_dict):
        """私发消息"""
        data = encode_msg(msg_dict)
        # 获取互斥锁
        with self.lock:
            if target_user in self.clients:
                try:
                    # 只针对target客户
                    self.clients[target_user]["conn"].sendall(data)
                    # 同时让发送者在本地也能看到自己发送的消息（也就是对发送者这个用户进行一次信息发送），由于这个逻辑在if中，保证了信息是在发送过去后才回显
                    sender = msg_dict.get("sender")
                    if sender != target_user and sender in self.clients:
                        self.clients[sender]["conn"].sendall(data)
                except Exception as e:
                    logger.error(f"Private message failed: {e}")

    def broadcast_user_list(self):
        """广播在线用户"""
        with self.lock:
            users = [{"username": k, "ip": v["ip"]} for k, v in self.clients.items()]
        self.broadcast({"type": "user_list", "users": users})

    def remove_client(self, username):
        """处理离线用户"""
        with self.lock:
            if username in self.clients:
                self.clients[username]["conn"].close()
                del self.clients[username]
        logger.info(f"User {username} disconnected.")
        self.broadcast_user_list()
        # 修改这里：将系统通知改为英文
        self.broadcast({"type": "system", "content": f"User {username} left the chat."})