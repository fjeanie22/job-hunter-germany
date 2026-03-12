import os, requests, json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
DB_FILE = "sent_jobs.json"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_jooble(sent, query, loc, radius=0):
    if not JOOBLE_KEY: return []
    print(f"📡 Jooble DE: {query} in {loc}...")
    found = []
    try:
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        # Для Jooble важно писать страну, чтобы он не уходил в США
        data = {"keywords": query, "location": loc, "radius": radius}
        res = requests.post(url, json=data, timeout=15).json()
        
        for j in res.get("jobs", []):
            j_id = f"jo-{j.get('id')}"
            location_name = j.get("location", "").lower()
            
            # СТРОГИЙ ФИЛЬТР: Только если это не США
            if any(us_city in location_name for us_city in ["usa", "ca", "ny", "il", "united states"]):
                continue
                
            if j_id not in sent:
                msg = (f"💼 <b>{query}</b>\n"
                       f"📝 {j.get('title')}\n"
                       f"🏢 {j.get('company', '---')}\n"
                       f"📍 {j.get('location')}\n"
                       f"🔗 <a href='{j.get('link')}'>Link</a>")
                found.append((j_id, msg))
    except Exception as e:
        print(f"Error: {e}")
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. WordPress / Elementor по Баварии
    for q in ["WordPress", "Elementor"]:
        new_jobs.extend(search_jooble(sent, q, "Bayern, DE"))
    
    # 2. Офис / Бухгалтерия по Мюльдорфу + 50км
    office_queries = ["Sachbearbeiter", "Büro", "Buchhaltung", "Finanzen"]
    for q in office_queries:
        new_jobs.extend(search_jooble(sent, q, "84453, DE", radius=50))

    if new_jobs:
        # Отправляем максимум 20 за раз
        for j_id, msg in new_jobs[:20]:
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"Найдено: {len(new_jobs)}")
    else:
        send_tg("🤖 Проверка DE: По твоим запросам в Баварии новых вакансий за последний час не появилось. Дежурю дальше!")

if __name__ == "__main__":
    main()
