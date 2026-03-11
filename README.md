# 局域网聊天室 (TCP Chat APP)

本项目是一个基于 Python 编写的局域网 C/S 架构即时通讯软件。项目初衷为满足嵌入式 Linux 系统下的局域网聊天软件设计需求，核心通信层采用原生 Socket (TCP 协议)，并在应用层自主封装了基于 JSON + 4字节长度头的防粘包协议。图形界面采用 Kivy 框架跨平台构建。

## 🌟 核心功能

* **跨平台互通**：支持 Windows / Linux 终端在同一局域网下无缝连接。
* **高并发支持**：服务端基于多线程 (Threading) 架构，独立处理每一个客户端的读写阻塞。
* **实时在线列表**：动态广播用户上线、下线状态，展示当前活跃用户的昵称与 IP。
* **群聊与私聊**：
  * **群发广播**：一键将消息下发至全体在线用户。
  * **定向私聊**：在 UI 侧边栏点击特定用户，即可建立点对点（逻辑层面的精准路由）私密聊天通道。
* **全局中文支持**：内嵌 `NotoSansCJK-Black.ttc` 字体，彻底解决跨平台图形框架的中文“豆腐块”乱码问题。

## 📂 目录结构

```text
PROJECT_FOR_CHAT/
├── core/                    # 核心网络架构与通信协议层
│   ├── network_client.py    # 客户端 Socket 线程与回调逻辑
│   ├── network_server.py    # 服务端多线程并发与路由分发
│   └── protocol.py          # TCP 粘包/半包处理与 JSON 序列化
├── ui/                      # 图形用户界面 (GUI) 层
│   └── app.py               # 基于 Kivy 与 KV 语言的界面交互
├── utils/                   # 通用工具层
│   └── logger.py            # 标准化控制台日志输出
├── client_main.py           # 客户端启动入口
├── server_main.py           # 服务端启动入口
├── requirements.txt         # 项目第三方依赖清单
└── NotoSansCJK-Black.ttc    # 全局中文字体文件
```

## 🛠️ 环境准备
Python 版本：推荐使用 Python 3.10 或以上版本。

安装依赖：
在终端进入项目根目录，执行以下命令安装 Kivy 图形框架依赖：
```bash
pip install -r requirements.txt
```
## 🚀 部署与运行指南
本项目为标准的 C/S 架构，必须先启动服务端，再启动客户端。

1. 启动服务器 (Server)
在局域网内找一台电脑作为中心服务器，打开终端运行：

```bash
python server_main.py
```

提示：服务器启动后，会在终端打印类似 Server started, listening on 0.0.0.0:8888 的日志。请使用 ifconfig或ip a (Linux) ，或 ipconfig (Windows) 查询并记录这台机器的局域网 IPv4 地址。

2. 启动客户端 (Client)
在同一局域网下的其他电脑（或本机新开一个终端），运行：
```bash
python client_main.py
```
3. 连接与使用
客户端启动后，会弹出图形登录界面。

Server IP：填入刚才查询到的服务器局域网 IP（如果在同一台电脑上自测，可直接填写 127.0.0.1）。

Port：默认 8888。

Username：输入你喜欢的任意昵称。

点击 Connect 进入聊天大厅，左侧选择用户即可切换私聊/群聊模式！