# 代码学习手册 (Code Study Manual)

本手册帮助你从“数据流”的角度理解项目：
- 你在 UI 输入框输入的文本，如何变成 socket 上传输的数据
- 服务端如何路由
- client 收到后如何回到 UI 页面显示
- 日志函数怎么调用、输出在哪里

---

## 1. 总体分层

1. UI 层：`ui/app.py`
- 负责界面、按钮事件、文本显示
- 不直接操作 socket

2. 控制层：`core/client_controller.py`
- 接收 UI 事件
- 调用网络层发送消息
- 接收网络回调后，决定 UI 如何更新

3. 网络层：
- client：`core/network_client.py`
- server：`core/network_server.py`
- 负责 TCP 收发、连接维护、消息路由

4. 协议层：`core/protocol.py`
- 负责消息编码/解码
- 统一格式：`4字节长度头 + JSON`

5. 工具层：`utils/logger.py`
- 提供统一日志 logger

---

## 2. 一条消息的完整流动

### UI -> Server

1. 你点击发送（或回车）
2. `ui/app.py:on_send_pressed()` 读取输入框文本
3. 调用 `core/client_controller.py:send_message(text)`
4. controller 调用 `core/network_client.py:send_message(content, target)`
5. network_client 调用 `core/protocol.py:encode_msg(msg_dict)`
6. `socket.sendall(...)` 发给 server

### Server -> 其他 Client

1. `core/network_server.py:handle_client()` 收到包并 `decode_msg()`
2. 根据消息类型分发：
- 公聊：`broadcast()`
- 私聊：`send_private()`
3. 服务端再次 `encode_msg()` 后 `sendall()` 给目标 client

### Client -> UI

1. `core/network_client.py:receive_loop()` 持续接收并 `decode_msg()`
2. 收到 dict 后触发 controller 回调 `_on_network_message(msg)`
3. controller 在 `_process_network_message(msg)` 中按类型处理
4. 调用 UI API（如 `append_history_line()`、`update_user_list()`）
5. 页面刷新

---

## 3. 逐文件学习（每个文件的重要函数 + 输入来源 + 输出去向）

## 根目录

### `client_main.py`

重要函数：
- `main()`

输入来源：
- 本地环境变量
- 本地字体文件 `NotoSansCJK-Black.ttc`

输出去向：
- 创建 `ChatApp`（UI）
- 创建 `ChatClientController`（控制层）
- 将 controller 注入 app，最后启动 UI 事件循环

说明：
- 该文件只做“组装”，不做业务逻辑。

### `server_main.py`

重要函数：
- `main()`

输入来源：
- 固定 host/port（`0.0.0.0:8888`）

输出去向：
- 创建并启动 `ChatServer`

### `README.md`

- 文档文件，无函数。

### `requirements.txt`

- 依赖清单，无函数。

### `NotoSansCJK-Black.ttc`

- 字体资源，无函数。

---

## `core/` 目录

### `core/__init__.py`

- 包初始化文件，无函数。

### `core/client_controller.py`

角色：
- client 端“业务中枢”，连接 UI 与 socket

重要函数：

1. `login(ip, port, username)`
- 输入来源：`ui/app.py:on_login_pressed()`
- 输出去向：调用 `network_client.connect()`；成功后更新 UI（进入 chat 页、显示系统信息）

2. `logout()`
- 输入来源：UI 点击退出、输入 `end`
- 输出去向：调用 `network_client.disconnect()`，再切换 UI 回登录页

3. `send_message(text)`
- 输入来源：UI 发送事件
- 输出去向：调用 `network_client.send_message(content, target)`

4. `set_target(username)`
- 输入来源：UI 左侧用户按钮点击
- 输出去向：更新当前聊天目标（公聊/私聊）并刷新 UI 标题

5. `_on_network_message(msg)`
- 输入来源：`network_client.receive_loop()` 的回调
- 输出去向：交给 `_process_network_message(msg)`，并调度到 UI 主线程

6. `_process_network_message(msg)`
- 输入来源：`_on_network_message`
- 输出去向：
  - `system/public/private` -> `append_history_line()`
  - `user_list` -> `update_user_list()`

7. `shutdown()`
- 输入来源：`ui/app.py:on_stop()`
- 输出去向：断开网络连接

### `core/network_client.py`

角色：
- client 端 TCP 传输层

重要函数：

1. `connect(host, port, username)`
- 输入来源：controller 登录请求
- 输出去向：
  - 建立 TCP 连接
  - 发登录包（`type=login`）
  - 启动接收线程 `receive_loop`

2. `send_message(content, target=None)`
- 输入来源：controller 发送请求
- 输出去向：
  - 构造消息 dict（公聊/私聊）
  - `encode_msg()` 打包
  - `socket.sendall()` 发给 server

3. `receive_loop()`
- 输入来源：socket 收到的服务器数据
- 输出去向：
  - `decode_msg()` 解包
  - 回调给 controller

4. `disconnect()`
- 输入来源：controller 退出、异常断连
- 输出去向：关闭 socket，停止接收循环

### `core/network_server.py`

角色：
- server 端连接管理 + 消息路由

重要函数：

1. `start()`
- 输入来源：`server_main.py`
- 输出去向：循环 `accept()`，每个 client 启动一个处理线程

2. `handle_client(conn, addr)`
- 输入来源：新连接线程
- 输出去向：
  - 接收登录包并登记在线用户
  - 收到公聊消息则 `broadcast()`
  - 收到私聊消息则 `send_private()`
  - 断线时 `remove_client()`

3. `broadcast(msg_dict)`
- 输入来源：系统消息、公聊消息、用户列表广播
- 输出去向：发给所有在线 client

4. `send_private(target_user, msg_dict)`
- 输入来源：私聊消息
- 输出去向：发给目标用户，并回显给发送者

5. `broadcast_user_list()`
- 输入来源：用户上线/下线
- 输出去向：向所有用户发送 `type=user_list`

6. `remove_client(username)`
- 输入来源：断连处理
- 输出去向：删除用户、广播新用户列表、广播离线系统消息

### `core/protocol.py`

角色：
- 消息编码和解码（防粘包/半包）

重要函数：

1. `encode_msg(msg_dict)`
- 输入来源：network_client / network_server
- 输出去向：返回可直接 sendall 的 bytes

2. `_recv_exact(conn, size)`
- 输入来源：`decode_msg()`
- 输出去向：返回固定长度 bytes，或 `None`

3. `decode_msg(conn)`
- 输入来源：network_client.receive_loop / network_server.handle_client
- 输出去向：返回 dict（上层业务可处理）

---

## `ui/` 目录

### `ui/__init__.py`

- 包初始化文件，无函数。

### `ui/app.py`

角色：
- 纯 UI 视图层（展示 + 事件）

重要函数：

1. `on_login_pressed()`
- 输入来源：登录按钮
- 输出去向：调用 controller.login(...)

2. `on_send_pressed()`
- 输入来源：发送按钮/输入框回车
- 输出去向：调用 controller.send_message(msg)

3. `on_logout_pressed()`
- 输入来源：退出按钮
- 输出去向：调用 controller.logout()

4. `on_user_selected(username)`
- 输入来源：在线用户按钮
- 输出去向：调用 controller.set_target(username)

5. `run_on_ui_thread(fn)`
- 输入来源：controller 的 UI 更新请求
- 输出去向：使用 Kivy `Clock` 在 UI 主线程执行 `fn`

6. `append_history_line(text)`
- 输入来源：controller
- 输出去向：聊天历史 Label 显示

7. `update_user_list(users, current_username)`
- 输入来源：controller（处理 `user_list` 后）
- 输出去向：重绘左侧在线用户按钮列表

8. `show_login_status(text, is_error=False)`
- 输入来源：controller 登录结果
- 输出去向：登录页状态文本显示

9. `switch_to_chat()` / `switch_to_login()`
- 输入来源：controller
- 输出去向：页面切换

10. `set_chat_mode_public()` / `set_chat_mode_private(username)`
- 输入来源：controller
- 输出去向：顶部模式标签显示更新

---

## `utils/` 目录

### `utils/__init__.py`

- 包初始化文件，无函数。

### `utils/logger.py`

重要函数：
- `get_logger(name)`

输入来源：
- 各模块调用（client/server/controller）

输出去向：
- 返回 `logging.Logger` 对象；日志默认输出到命令行

---

## 4. 日志怎么用？日志去哪里？

### 调用方法

```python
from utils.logger import get_logger

logger = get_logger("Demo")
logger.debug("debug")
logger.info("info")
logger.error("error")
```

### 输出位置

- 默认输出到命令行终端（`StreamHandler`）。
- 不会自动显示在 UI 页面。

### 如果你想在 UI 里看到某条信息

不要只写 `logger.info(...)`，还需要在 controller 调用 UI 方法：
- `append_history_line(...)`
- 或其它视图更新 API

---

## 5. 建议你按这个顺序阅读源码

1. `ui/app.py`（先看你操作按钮时触发哪个函数）
2. `core/client_controller.py`（看 UI 事件如何转成网络调用）
3. `core/network_client.py`（看消息如何 encode + send）
4. `core/network_server.py`（看 server 如何路由）
5. `core/protocol.py`（看底层封包解包）
6. `utils/logger.py`（看日志输出机制）

这样你会最容易建立“UI 文本 -> socket 数据 -> UI 显示”的完整心智模型。
