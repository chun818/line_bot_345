from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import *

import os

# 如果在本地运行，加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# 从环境变量中获取您的Channel Secret和Access Token
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 用于存储用户ID和名称的字典
user_data = {}

# 设定Webhook路由
@app.route("/callback", methods=['POST'])
def callback():
    # 获取请求的签名
    signature = request.headers['X-Line-Signature']

    # 获取请求的内容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 验证签名并处理请求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 处理文本消息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id  # 获取用户ID
    user_message = event.message.text  # 获取用户发送的消息

    # 获取用户的显示名称
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except LineBotApiError:
        # 如果无法获取用户资料，使用默认名称
        display_name = '用户'

    # 存储用户ID和名称
    user_data[user_id] = display_name

    # 自定义回复逻辑，可以针对不同用户ID或名称进行个性化回复
    if user_message == '你好':
        reply = f'{display_name}，你好！有什么我可以帮助您的吗？'
    else:
        reply = f'{display_name}，您说了：{user_message}'

    # 发送回复
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
