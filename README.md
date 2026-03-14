# 局域网聊天室 (TCP Chat APP)

这是一个基于 Python + Kivy + Socket(TCP) 的局域网聊天室项目。

当前版本重点做了**模块化重构**：
- UI (`ui/app.py`) 只负责界面展示与用户交互事件
- 消息编排 (`core/client_controller.py`) 负责 UI 和网络之间的转换
- 网络传输 (`core/network_client.py`, `core/network_server.py`) 只负责 socket 通信与路由
- 协议层 (`core/protocol.py`) 只负责消息打包/解包

## 1. 当前目录结构

```text
TCP-Chat-APP/
├── core/
│   ├── __init__.py
│   ├── client_controller.py   # 客户端控制器：UI <-> Socket 消息流编排
│   ├── network_client.py      # 客户端 TCP 收发
│   ├── network_server.py      # 服务端 TCP 收发与消息路由
│   └── protocol.py            # 4字节长度头 + JSON 协议
├── docs/
│   └── CODE_STUDY_MANUAL.md   # 代码学习手册（逐文件/逐函数输入输出）
├── ui/
│   ├── __init__.py
│   └── app.py                 # 纯 UI 层（不直接操作 socket）
├── utils/
│   ├── __init__.py
│   └── logger.py              # 日志工厂
├── client_main.py             # 客户端入口（组装 UI + Controller）
├── server_main.py             # 服务端入口
├── requirements.txt
└── NotoSansCJK-Black.ttc
```

## 2. 消息流（问答）

### A. 在 UI 输入框敲字后，为什么会变成 socket 数据？

1. UI 输入框触发 `ui/app.py` 的 `on_send_pressed()`
2. `on_send_pressed()` 调用 `core/client_controller.py` 的 `send_message(text)`
3. `send_message()` 调用 `core/network_client.py` 的 `send_message(content, target)`
4. `network_client.send_message()` 调用 `core/protocol.py` 的 `encode_msg(dict)`
5. `encode_msg()` 把字典转成 `JSON bytes + 4字节长度头`
6. 最终通过 `socket.sendall(...)` 发往服务端

### B. 服务端收到后做了什么？

1. `core/network_server.py` 的 `handle_client()` 使用 `decode_msg()` 解包
2. 按 `type` 进行路由：
- `public` -> `broadcast()` 发给所有在线用户
- `private` -> `send_private()` 发给目标用户，并回显给发送者
3. 发送前统一再 `encode_msg()` 打包

### C. client 收到 socket 数据后，为什么会显示到 UI？

1. `core/network_client.py` 的 `receive_loop()` 持续 `decode_msg()`
2. 解包后的字典通过回调交给 `core/client_controller.py` 的 `_on_network_message(msg)`
3. controller 根据 `type` 决定 UI 行为：
- `public/private/system` -> 追加到聊天历史
- `user_list` -> 更新左侧在线用户列表
4. controller 调用 `ui/app.py` 暴露的 View API（如 `append_history_line()`、`update_user_list()`）
5. UI 层更新页面

## 3. 日志如何调用？输出到哪里？

### 调用方式

```python
from utils.logger import get_logger

logger = get_logger("MyModule")
logger.debug("debug message")
logger.info("info message")
logger.error("error message")
```

### 输出位置

日志默认通过 `logging.StreamHandler` 输出到**命令行终端**，不会自动显示在 UI 页面。

如果你想把某些信息显示在 UI，请在 controller 中调用 `append_history_line()` 一类 UI 方法，而不是只打日志。

## 4. 中英双语注释

本项目的核心代码文件已经增加中英双语注释（EN + 中文），便于对照学习。

## 5. 运行方式

### 环境准备

```bash
pip install -r requirements.txt
```

### 启动服务端

```bash
python server_main.py
```

### 启动客户端

```bash
python client_main.py
```

## 6. 深入学习文档

请阅读：`docs/CODE_STUDY_MANUAL.md`

该手册详细列出了每个文件的重要函数、函数输入来源、输出去向，并专门解释 UI -> Socket -> UI 的完整路径。
