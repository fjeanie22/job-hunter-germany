import requests
import os
from parser_indeed import search_indeed

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, data=data)


jobs = search_indeed("wordpress", "Bayern")

for job in jobs:

    message = f"""
💻 <b>{job['title']}</b>

🏢 {job['company']}

🔗 {job['link']}
"""

    send_message(message)
