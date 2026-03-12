import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

ADZ_ID = "c6e9389e"
ADZ_KEY = "3a20349890d291936c53e0ec3e69188e"

# Оставляем самые верные слова для теста
OFFICE_QUERIES = ["Sachbearbeiter", "Büro", "Buchhaltung"]
WEB_QUERIES = ["WordPress", "Elementor"]

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_adzuna(sent, query, loc, dist):
    url = f"https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = {"app_id": ADZ_ID, "app_key": ADZ_KEY, "results_per_page": 3, "what": query, "where": loc, "distance": dist}
    found = []
    try:
        res = requests.get(url, params=params, timeout=10).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                msg = f"📌 <b>{query}</b> (Adzuna)\n🏢 {j.get('company', {}).get('display_name')}\n📍 {j.get('location', {}).get('display_name')}\n🔗 <a href='{j.get('redirect_url')}'>Link</a>"
                found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    all_found_messages = []
    
    # ТЕСТОВЫЙ ЗАПУСК: Ищем по Мюльдорфу и Баварии
    print("Запуск проверки...")
    
    # Офис
    for q in OFFICE_QUERIES:
        results = search_adzuna(sent, q, "Mühldorf am Inn", 50)
        all_found_messages.extend(results)
        
    # Web
    for q in WEB_QUERIES:
        results = search_adzuna(sent, q, "Bayern", 0)
        all_found_messages.extend(results)

    # Отправляем результаты
    if not all_found_messages:
        # Если совсем ничего нового, давай хоть поприветствуем, чтобы проверить связь
        send_tg("🤖 Бот проверил вакансии: новых пока нет. Ищу дальше каждые 2 часа!")
    else:
        for j_id, msg in all_found_messages[:10]: # Не больше 10 за раз
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)

    print(f"Найдено новых: {len(all_found_messages)}")

if __name__ == "__main__":
    main()
