import requests

TOKEN = "BOT_TOKEN"
CHAT_ID = "CHAT_ID"

message = "🚀 Job Hunter запущен!"

url = f"https://api.telegram.org/bot8693778242:AAG6Hpo0gVF8_3weVcGg3yhg9tn4vLe28LU/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": message
}

requests.post(url, data=data)
