import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Ключи Adzuna
ADZ_ID = "c6e9389e"
ADZ_KEY = "3a20349890d291936c53e0ec3e69188e"

def load_sent():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_adzuna(sent, query, loc):
    print(f"📡 Adzuna: {query} in {loc}...")
    url = "https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = {
        "app_id": ADZ_ID, 
        "app_key": ADZ_KEY, 
        "results_per_page": 15, 
        "what": query, 
        "where": loc,
        "content-type": "application/json"
    }
    found = []
    try:
        res = requests.get(url, params=params, timeout=15).json()
        results = res.get("results", [])
        for j in results:
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                title = j.get("title", "Job")
                link = j.get("redirect_url")
                msg = f"🔍 <b>{query}</b>\n📝 {title}\n📍 {loc}\n🔗 <a href='{link}'>Link</a>"
                found.append((j_id, msg))
    except Exception as e: print(f"Adzuna Error: {e}")
    return found

def search_ovb(sent):
    print("📡 OVB Check...")
    found = []
    # Заходим на общую страницу вакансий Мюльдорфа
    url = "https://www.ovbstellen.de/jobs-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Ищем вообще все ссылки, в которых есть слово "stellenangebot"
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/stellenangebot/" in href:
                if not href.startswith('http'): href = "https://www.ovbstellen.de" + href
                title = a.get_text(strip=True) or "Локальная вакансия"
                if len(title) < 5: continue
                j_id = f"ovb-{href}"
                if j_id not in sent:
                    msg = f"🏠 <b>OVB Local</b>\n📝 {title}\n🔗 <a href='{href}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # ТЕСТ: Ищем максимально широко
    new_jobs.extend(search_adzuna(sent, "WordPress", "Bayern")) # Весь WordPress в Баварии
    new_jobs.extend(search_adzuna(sent, "Sachbearbeiter", "Mühldorf")) # Весь офис в Мюльдорфе
    new_jobs.extend(search_ovb(sent)) # Всё с OVB

    if new_jobs:
        for j_id, msg in new_jobs[:20]: # Берем сразу 20 для теста
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"Sent {len(new_jobs)} jobs")
    else:
        send_tg("🤖 Внимание: Поиск выполнен, но результатов ноль. Проверьте ключевые слова!")

if __name__ == "__main__":
    main()
