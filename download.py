import requests
from bs4 import BeautifulSoup
import json
import re
import time

cookies = {
    'dle_user_id': '',
    'dle_password': '',
    'cf_clearance': ''
}

def get():
    anime_list = []
    page = 1
    request_count = 0
    #"", "seen", "will", "watch", "poned", "aband"
    for pageName in ["seen", "will", "watch", "poned", "aband"]:
        while True:
            if page == 1:
                url = f"https://anitube.in.ua/mylists/uaDominator/{pageName}/"
            else:
                url = f"https://anitube.in.ua/mylists/uaDominator/{pageName}/page/{page}/"

            response = requests.get(url, cookies=cookies)

            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select("article.story")

            if not articles:
                print(f"[INFO] Сторінка {page} порожня. Зупинка.")
                break

            for article in articles:
                a_tag = article.select_one("h2[itemprop='name'] a")
                if a_tag:
                    translated_title = a_tag.text.strip()
                    link = a_tag["href"].strip()

                    # Витягуємо рік
                    year_tag = article.select_one(".story_infa a[href*='/xfsearch/year/']")
                    year = year_tag.text.strip() if year_tag else ""

                    # Додатковий запит на сторінку аніме, щоб отримати оригінальну назву
                    original_title = ""
                    anime_resp = requests.get(link, cookies=cookies)
                    request_count += 1  # збільшуємо лічильник запитів


                    if anime_resp.status_code == 200:
                        anime_soup = BeautifulSoup(anime_resp.text, "html.parser")
                        strong_tag = anime_soup.find('strong', string='Оригінальна назва:')
                        if strong_tag:
                            next_node = strong_tag.next_sibling
                            if next_node and isinstance(next_node, str) and next_node.strip():
                                original_title = next_node.strip()
                            else:
                                text_node = strong_tag.find_next(text=True)
                                if text_node:
                                    original_title = text_node.strip()

                    status_div = article.select_one(".status-indicator")
                    status = status_div.text.strip() if status_div else ""
                    box = {
                        "original_title": original_title,
                        "translated_title": translated_title,
                        "year": year,
                        "url": link
                    }
                    anime_list.append(box)

                    print(box)
                    
                    if request_count % 2 == 0:
                        time.sleep(3)

            page += 1
        # Зберігаємо у файл
        with open(f"{pageName}-list.json", "w", encoding="utf-8") as f:
            json.dump(anime_list, f, ensure_ascii=False, indent=2)

        print(f"Збережено {len(anime_list)} тайтлів у {pageName}-list.json")

        anime_list = []
        page = 1



def parse():
    with open(".all-list.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    url_to_original = {item["url"]: item["original_title"] for item in all_data}

    for pageName in ["seen", "will", "watch", "poned", "aband"]:
        filename = f"{pageName}-list.json"

        # 4. Завантажуємо дані
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 5. Підміняємо original_title, якщо url є в мапі
        for item in data:
            if item["url"] in url_to_original:
                item["original_title"] = url_to_original[item["url"]]

        # 6. Перезаписуємо файл
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[✔] Оновлено: {filename}")



def main():
    get()
    parse()


if __name__ == "__main__":
    main()