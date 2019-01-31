from flask import Flask, request, abort
import requests

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)
import os
from io import BytesIO
import json

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = ""
YOUR_CHANNEL_SECRET = ""

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


url_detect = 'https://japanwest.api.cognitive.microsoft.com/face/v1.0/detect'
url_similar = 'https://japanwest.api.cognitive.microsoft.com/face/v1.0/findsimilars'

headers_detect = {
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': ''
}

headers_similar = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': ''
}

params = {
    'returnFaceId': 'true',  # The default value is true.
    'returnFaceLandmarks': 'false', # The default value is false.
    'returnFaceAttributes': 'age,gender', # age, gender, headPose, smile, facialHair, and glasses.
}

body = {
    "mode": "matchFace"
}

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='顔画像を送信しなさい'))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image = BytesIO(message_content.content)

    r_1 = requests.post(url_detect, headers = headers_detect, params = params, data = open('matsuko.jpg','rb'))
    r_2 = requests.post(url_detect , headers = headers_detect, params = params, data = image)
    faceId = r_1.json()[0]['faceId']
    #line_bot_api.reply_message(event.reply_token,TextSendMessage(text='あなたの年齢は{}'.format(r_2.json()[0])))

    try:
        faceIds = r_2.json()[0]['faceId']
        body['faceId'] = faceId
        body['faceIds'] = [faceIds]
        r_find_similar = requests.post(url_similar, headers = headers_similar, data = json.dumps(body)).json()[0]['confidence']
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='私との類似度は{}'.format(r_find_similar)))

    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='顔が検出できなかったですよ'))


if __name__ == "__main__":
    #app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
