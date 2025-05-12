from flask import Flask, request, abort, jsonify
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent, StickerMessageContent, LocationMessageContent, ImageMessageContent
import requests
import json
import os

app = Flask(__name__)

# === LINE CHANNEL SETTING ===
CHANNEL_ACCESS_TOKEN = 'kIUePmws0G9aM3bZrnm7i5l17oCWaF2u+ECyhR0/vP8SAayHH4+fIrNA43mSOghNO3NTeT6/0Uoto4+7ItvhejRzls4SN8pxkbRKYIqvnKB91s5nhbIrj5hLluY2o+ASKnvFkONoso3I45y3emUslgdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '000c185ac93b503d5980a9709e760422'

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# === Gemini API 設定 ===
GEMINI_API_KEY = 'AIzaSyDG6edtmKlhnlJiKBY-slDeK-i2-HIa7Fs'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# === Azure Text Analytics 設定 ===
AZURE_KEY = '51FkWvHcWLMlag4RPBpGNq9eB8GVOcGydp0W2a7bTQeNVnJ2cIIrJQQJ99BEACYeBjFXJ3w3AAAaACOGO3AP'
AZURE_ENDPOINT = 'https://newyork.cognitiveservices.azure.com/'

# === OpenWeather 設定 ===
WEATHER_API_KEY = '35e6c0357d0c54bdfb1e2083b25510cb'

def get_gemini_reply(user_text):
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": user_text}]}
        ]
    }
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("[Gemini Error]", e)
        return "抱歉，Gemini 回覆失敗，請稍後再試。"

def analyze_sentiment_azure(text):
    url = f"{AZURE_ENDPOINT}text/analytics/v3.1/sentiment"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "documents": [
            {"id": "1", "language": "zh-hant", "text": text}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        sentiment = result['documents'][0]['sentiment']
        return f"這段文字的情緒傾向是：{sentiment}"
    except Exception as e:
        print("[Azure Sentiment Error]", e)
        return "情緒分析失敗，請稍後再試。"

def get_weather(city):
    city_map = {
        "台北": "Taipei",
        "臺北": "Taipei",
        "台中": "Taichung",
        "高雄": "Kaohsiung",
        "新竹": "Hsinchu",
        "台南": "Tainan"
    }
    city_en = city_map.get(city.strip(), city.strip())

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=zh_tw"
    try:
        r = requests.get(url)
        data = r.json()
        if 'weather' in data:
            desc = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"{city} 的天氣是 {desc}，溫度約 {temp}°C"
        else:
            print("[Weather API error]:", data)
            return "查無此城市天氣資料"
    except Exception as e:
        print("[Weather Exception]:", e)
        return "天氣查詢失敗，請稍後再試。"

def save_history(user_id, message):
    filename = f"history_{user_id}.json"
    history = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
    history.append(message)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print("[DEBUG] webhook body:", body)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("[ERROR] webhook error:", e)
        abort(400)
    return 'OK'

@app.route("/history/<user_id>", methods=['GET'])
def get_history(user_id):
    filename = f"history_{user_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route("/history/<user_id>", methods=['DELETE'])
def delete_history(user_id):
    filename = f"history_{user_id}.json"
    if os.path.exists(filename):
        os.remove(filename)
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not found"})

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_text = event.message.text
    user_id = event.source.user_id

    if user_text.startswith("情緒"):
        content = user_text.replace("情緒", "").strip()
        reply_text = analyze_sentiment_azure(content)
    elif user_text.startswith("天氣"):
        city = user_text.replace("天氣", "").strip()
        reply_text = get_weather(city)
    else:
        reply_text = get_gemini_reply(user_text)

    save_history(user_id, {"type": "text", "input": user_text, "output": reply_text})

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker(event):
    user_id = event.source.user_id
    save_history(user_id, {"type": "sticker", "info": "收到貼圖"})
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="收到貼圖！")] 
            )
        )

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    user_id = event.source.user_id
    save_history(user_id, {"type": "image", "info": "收到圖片"})
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="收到圖片啦")] 
            )
        )

@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    user_id = event.source.user_id
    title = event.message.title or "你傳的地點"
    address = event.message.address
    lat = event.message.latitude
    lng = event.message.longitude
    location_info = f"{title} @ {address} ({lat},{lng})"
    save_history(user_id, {"type": "location", "info": location_info})
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"位置收到了！\n{address}")]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render 會設 PORT，沒有就用 5000
    app.run(host="0.0.0.0", port=port)        # 0.0.0.0 表示「接受所有網卡來源」

