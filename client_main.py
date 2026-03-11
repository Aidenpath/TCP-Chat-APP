from ui.app import ChatApp
import os

# === 新增以下这三行代码 ===
from kivy.core.text import LabelBase
# 强制将 Kivy 的默认字体 (Roboto) 替换为你的中文字体
LabelBase.register(name='Roboto', fn_regular='NotoSansCJK-Black.ttc')

if __name__ == '__main__':
    # 解决部分系统下 Kivy 中文显示方块的问题 (需确保系统有中文字体，此处以通用设置为例)
    os.environ['KIVY_TEXT'] = 'pil'
    ChatApp().run()