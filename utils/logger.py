"""
EN: Shared logger factory.
中文: 统一日志工厂。

EN: Logs are printed to terminal (stdout/stderr via StreamHandler),
not to the Kivy UI by default.
中文: 日志默认输出到命令行（StreamHandler），不会直接显示在 Kivy UI。
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """EN: Create/reuse configured logger. 中文: 创建或复用已配置的 logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # EN: StreamHandler writes to terminal.
    # 中文: StreamHandler 会把日志输出到命令行。
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(handler)
    return logger
