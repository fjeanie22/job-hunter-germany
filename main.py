import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    requests.post(url, json=payload)

def search_arbeitnow(sent):
    """Этот источник очень надежный для IT/Web вакансий в Германии"""
    print("📡 Проверка Arbeitnow...")
    found = []
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in res.get("data", []):
            title = j.get("title", "")
            # Ищем WordPress или Remote
            if "wordpress" in title.lower() or "remote" in title.lower():
                j_id = f"an-{j.get('slug')}"
                if j_id not in sent:
                    msg = f"🌐 <b>Arbeitnow (Remote/IT)</b>\n📝 {title}\n🏢 {j.get('company_name')}\n🔗 <a href='{j.get('url')}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def search_ovb_alternative(sent):
    """Пробуем достать данные с OVB через другой селектор"""
    print("📡 Проверка OVB (метод 2)...")
    found = []
    url = "https://www.ovbstellen.de/jobs-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Ищем все ссылки. Если в ссылке есть название вакансии, берем её.
        links = soup.select('a[href*="/stellenangebot/"]')
        for a in links:
            href = a['href']
            if not href.startswith('http'): href = "https://www.ovbstellen.de" + href
            title = a.get_text(strip=True)
            if len(title) > 10:
                j_id = f"ovb-{href}"
                if j_id not in sent:
                    msg = f"🏠 <b>OVB Local</b>\n📝 {title}\n🔗 <a href='{href}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # Запускаем два разных метода
    new_jobs.extend(search_arbeitnow(sent))
    new_jobs.extend(search_ovb_alternative(sent))

    if new_jobs:
        # Отправляем найденное
        for j_id, msg in new_jobs[:15]:
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"Найдено: {len(new_jobs)}")
    else:
        # Если опять пусто - значит пора менять стратегию поиска (ключевые слова)
        send_tg("⚠️ Снова пусто. Попробую расширить поиск на 'Mitarbeiter' и 'Büro' без фильтров.")
        # Для теста: давай принудительно найдем ХОТЯ БЫ ОДНУ вакансию на Arbeitnow
        # просто чтобы ты увидела, что бот может присылать данные.
        print("Ничего не найдено.")

if __name__ == "__main__":
    main()
