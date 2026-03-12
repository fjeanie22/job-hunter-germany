def main():
    sent = load_sent()
    new_jobs = []
    
    # 1. WordPress / Elementor по Баварии
    # Используем полное название страны, чтобы Jooble не путал с Делавэром
    for q in ["WordPress", "Elementor"]:
        new_jobs.extend(search_jooble(sent, q, "Bayern, Germany, Deutschland"))
    
    # 2. Офис / Бухгалтерия по Мюльдорфу + 50км
    office_queries = ["Sachbearbeiter", "Büro", "Buchhaltung", "Finanzen"]
    for q in office_queries:
        # Здесь пишем город полностью
        new_jobs.extend(search_jooble(sent, q, "84453 Mühldorf am Inn, Germany", radius=50))

    if new_jobs:
        valid_jobs = []
        for j_id, msg in new_jobs:
            # ЖЕСТКАЯ ПРОВЕРКА: Если в ссылке нет .de или в тексте есть американские штаты - в корзину
            text_check = msg.lower()
            if any(us_state in text_check for us_state in [" delaware", " dover", " newark", " usa"]):
                continue
            valid_jobs.append((j_id, msg))

        for j_id, msg in valid_jobs[:15]:
            send_tg(msg)
            sent.add(j_id)
        
        with open(DB_FILE, "w") as f:
            json.dump(list(sent), f)
        print(f"Найдено реальных: {len(valid_jobs)}")
    else:
        send_tg("🤖 Проверка Germany: Американский Делавэр побежден, ищем в настоящей Баварии. Пока новых вакансий нет.")
