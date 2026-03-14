# 局域网聊天室 (TCP Chat APP)

本项目是一个基于 Python 编写的局域网 C/S 架构即时通讯软件。项目初衷为满足嵌入式 Linux 系统下的局域网聊天软件设计需求，核心通信层采用原生 Socket (TCP 协议)，并在应用层自主封装了基于 JSON + 4字节长度头的防粘包协议。图形界面采用 Kivy 框架跨平台构建。

## 核心功能

* **跨平台互通**：支持 Windows / Linux 终端在同一局域网下无缝连接。并可以打包为安卓应用程序。
* **高并发支持**：服务端基于多线程 (Threading) 架构，独立处理每一个客户端的读写阻塞。
* **实时在线列表**：动态广播用户上线、下线状态，展示当前活跃用户的昵称与 IP。
* **群聊与私聊**：
  * **群发广播**：一键将消息下发至全体在线用户。
  * **定向私聊**：在 UI 侧边栏点击特定用户，即可建立点对点（逻辑层面的精准路由）私密聊天通道。
* **全局中文支持**：内嵌 `NotoSansCJK-Black.ttc` 字体，彻底解决跨平台图形框架的中文“豆腐块”乱码问题。


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

## 2. 消息流（Q&A）

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
在局域网内找一台电脑作为中心服务器，打开终端运行：
```bash
python server_main.py
```
提示：服务器启动后，会在终端打印类似 Server started, listening on 0.0.0.0:8888 的日志。请使用 ifconfig或ip a (Linux) ，或 ipconfig (Windows) 查询并记录这台机器的局域网 IPv4 地址。

### 启动客户端
在同一局域网下的其他电脑（或本机新开一个终端），运行：
```bash
python client_main.py
```
客户端启动后，会弹出图形登录界面。

Server IP：填入刚才查询到的服务器局域网 IP（如果在同一台电脑上自测，可直接填写 127.0.0.1）。

Port：默认 8888。

Username：输入你喜欢的任意昵称。

点击 Connect 进入聊天大厅，左侧选择用户即可切换私聊/群聊模式！

## 6. 安卓端打包指南 (Bonus)

本项目基于 Kivy 框架开发，原生支持通过 Buildozer 工具链将客户端打包为独立的安卓 APK 文件。

### 环境准备 (Linux)
由于底层的编译依赖项，强烈建议在 Linux 环境（如 Ubuntu 虚拟机）下进行打包操作。

**避坑指南：Python 版本兼容性**

经测试，Buildozer 目前对部分较新的 Python 版本（如 3.13）存在兼容性问题。强烈推荐使用 Conda 创建一个 **Python 3.11** 的干净虚拟环境进行打包：
> ```bash
> conda create -n kivy_pack python=3.11
> conda activate kivy_pack
> pip install buildozer cython
> ```

### 准备打包文件
Buildozer 默认寻找 `main.py` 作为安卓应用的启动入口。我们需要在项目根目录下，把客户端入口文件复制并重命名：
```bash
cp client_main.py main.py
```

### 初始化与配置 Buildozer
在项目根目录运行初始化命令：

```bash
buildozer init
```
这会生成一个 buildozer.spec 配置文件。请打开它，并修改以下极其关键的几个配置项：

```bash
# 确保包含中文字体文件，否则手机端会显示为乱码豆腐块！
source.include_exts = py,png,jpg,kv,atlas,ttc,ttf


# 声明 Python 和 Kivy 依赖
requirements = python3,kivy

# 开启安卓网络访问权限（极重要：若不开启，点击 Connect 会直接闪退）
android.permissions = INTERNET
```
编译生成 APK
配置完成后，在终端执行以下命令开始打包：

```bash
buildozer android debug
```
注：首次打包会自动下载庞大的 Android SDK 和 NDK 依赖环境，耗时较长（可能需要 15-30 分钟），请保持网络畅通并耐心等待。编译成功后，生成的 APK 文件会保存在项目新增的 bin/ 目录下。

手机端测试与联调
将编译好的 APK 安装到安卓手机上。

局域网直连：确保手机和运行 Server 的电脑连入同一个局域网（同一 WiFi），在 App 登录页填入 Server 的局域网 IPv4 地址即可。

## 7. 深入学习文档

请阅读：`docs/CODE_STUDY_MANUAL.md`

该手册详细列出了每个文件的重要函数、函数输入来源、输出去向，并专门解释 UI -> Socket -> UI 的完整路径。
