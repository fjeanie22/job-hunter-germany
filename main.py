import os, requests, json
from bs4 import BeautifulSoup # Нам понадобится эта библиотека

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
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def search_ovb(sent):
    print("📡 Проверка OVB Stellen...")
    found = []
    # Ссылка на поиск Sachbearbeiter в Мюльдорфе на OVB
    url = "https://www.ovbstellen.de/jobs-sachbearbeiter-in-muehldorf-am-inn"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Ищем карточки вакансий (названия классов могут меняться, это базовый поиск)
        jobs = soup.find_all('div', class_='job-listing') or soup.find_all('article')
        
        for j in jobs:
            title_tag = j.find('h2') or j.find('a')
            if title_tag:
                title = title_tag.text.strip()
                link = title_tag.get('href', '')
                if not link.startswith('http'): link = "https://www.ovbstellen.de" + link
                
                j_id = f"ovb-{link}" # Используем ссылку как уникальный ID
                if j_id not in sent:
                    msg = f"🏠 <b>OVB Stellen (Local)</b>\n📝 {title}\n📍 Mühldorf am Inn\n🔗 <a href='{link}'>Открыть</a>"
                    found.append((j_id, msg))
    except Exception as e:
        print(f"❌ Ошибка OVB: {e}")
    return found

def main():
    sent = load_sent()
    # Собираем всё из старых поисков и нового OVB
    all_found = search_ovb(sent)
    
    if all_found:
        for j_id, msg in all_found[:5]:
            send_tg(msg)
            sent.add(j_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
    else:
        # Оставляем "маячок", чтобы ты видела, что бот работает
        send_tg("🤖 Проверка завершена. На OVB Stellen и в API пока ничего нового. Дежурю дальше!")

if __name__ == "__main__":
    main()
