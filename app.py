from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import *

import os
import threading
import socket

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

# 定义一个函数，用于处理Socket连接
def socket_listener():
    host = '0.0.0.0'  # 监听所有网络接口
    port = 12345      # 与发送端的端口一致

    # 建立一个 TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"正在监听 {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        print(f"已连接到 {addr}")

        data = conn.recv(1024)
        message = data.decode('utf-8')
        print(f"接收到的消息：{message}")

        # 在这里根据接收到的消息，触发Bot向用户发送消息
        if message == 'trigger_message':
            send_message_to_users('这是自动发送的消息。')

        conn.close()
        print("连接已关闭。")

# 定义一个函数，用于向所有用户发送消息
def send_message_to_users(text):
    for user_id in user_data.keys():
        try:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=text)
            )
            print(f"已向用户 {user_data[user_id]} 发送消息。")
        except LineBotApiError as e:
            print(f"发送消息给用户 {user_id} 时发生错误：{e}")

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
    # 在启动Flask应用之前，启动Socket监听线程
    socket_thread = threading.Thread(target=socket_listener)
    socket_thread.daemon = True  # 设置为守护线程，随主线程退出
    socket_thread.start()

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
