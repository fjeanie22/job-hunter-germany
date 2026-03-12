import os, requests, json
from bs4 import BeautifulSoup

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "sent_jobs.json"

# Adzuna — она неплохо видит именно немецкие Büro-вакансии
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

def search_adzuna_local(sent, query, loc):
    """Поиск по немецкой базе Adzuna"""
    print(f"📡 Поиск {query} в {loc}...")
    found = []
    try:
        url = "https://api.adzuna.com/v1/api/jobs/de/search/1"
        params = {
            "app_id": ADZ_ID, 
            "app_key": ADZ_KEY, 
            "results_per_page": 20, 
            "what": query, 
            "where": loc,
            "distance": 30 # Радиус 30 км вокруг Мюльдорфа
        }
        res = requests.get(url, params=params, timeout=15).json()
        for j in res.get("results", []):
            j_id = f"adz-{j.get('id')}"
            if j_id not in sent:
                # Проверяем, что это не Америка (на всякий случай)
                loc_display = j.get('location', {}).get('display_name', '')
                if "USA" in loc_display or "Chicago" in loc_display: continue
                
                msg = (f"📍 <b>{query} (Мюльдорф +30км)</b>\n"
                       f"📝 {j.get('title')}\n"
                       f"🏢 {j.get('company', {}).get('display_name', '---')}\n"
                       f"📍 {loc_display}\n"
                       f"🔗 <a href='{j.get('redirect_url')}'>Link</a>")
                found.append((j_id, msg))
    except: pass
    return found

def search_ovb_real(sent):
    """Прямой заход на OVB Stellen — тут самая 'домашняя' работа"""
    print("📡 Проверка OVB Stellen...")
    found = []
    # Ссылка на категорию Büro в Мюльдорфе
    url = "https://www.ovbstellen.de/jobs-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Ищем все ссылки на вакансии
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/stellenangebot/" in href:
                if not href.startswith('http'): href = "https://www.ovbstellen.de" + href
                title = a.get_text(strip=True)
                if len(title) < 15: continue
                
                j_id = f"ovb-{href}"
                if j_id not in sent:
                    msg = f"🏠 <b>OVB Мюльдорф</b>\n📝 {title}\n🔗 <a href='{href}'>Link</a>"
                    found.append((j_id, msg))
    except: pass
    return found

def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. Реальный офис в Мюльдорфе и рядом
    for q in ["Sachbearbeiter", "Büro", "Buchhaltung"]:
        new_jobs.extend(search_adzuna_local(sent, q, "84453"))
    
    # 2. Прямой поиск по местной газете OVB
    new_jobs.extend(search_ovb_real(sent))
    
    # 3. WordPress (ищем по всей Баварии, так как это специфично)
    new_jobs.extend(search_adzuna_local(sent, "WordPress", "Bayern"))

    if new_jobs:
        for j_id, msg in new_jobs[:15]:
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
    else:
        print("Ничего нового в локальной базе.")

if __name__ == "__main__":
    main()
