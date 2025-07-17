import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from urllib.parse import urlparse
import re
import unicodedata

# "planing"
# "watching"
# "completed"
# "paused"
# "dropped"


auth_token =""

headers = {
    'Referer': 'https://mikai.me',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0',
    'authorization': f'Bearer {auth_token}'
}

def normalize_name(name):
    # Видаляємо діакритичні символи (наприклад é → e)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    
    # Видаляємо все, що не буква або цифра
    name = re.sub(r'[^a-zA-Z0-9]', '', name)
    
    # Переводимо в нижній регістр
    return name.lower()

def find_first_mikai_url(tile):
    query = quote_plus(tile.get('original_title'))
    search_url = f"https://mikai.me/catalog?name={query}"
    resp = requests.get(search_url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = soup.select('a.card')

    original_norm = normalize_name(tile['original_title'])

    # Перевіримо до 5 карток
    for i, card in enumerate(cards[:5]):
        if not card.has_attr('href'):
            continue
        full_url = "https://mikai.me" + card['href']
        try:
            anime_page = requests.get(full_url, headers=headers)
            anime_page.raise_for_status()
            anime_soup = BeautifulSoup(anime_page.text, 'html.parser')
            h2_tag = anime_soup.select_one('h2.mt-1.text-sm.text-neutral-600')
            if h2_tag:
                page_title = h2_tag.text.strip()
                page_norm = normalize_name(page_title)
                if page_norm == original_norm:
                    return full_url
        except Exception as e:
            print(f"⚠️ Помилка при перевірці картки {i+1}: {e}")
            continue
    return None

def extract_anime_id(url):
    path = urlparse(url).path
    parts = path.strip('/').split('/')
    if len(parts) >= 2 and parts[0] == "anime":
        return int(parts[1].split('-')[0])
    return None


def add_to_list(anime_id, status):
    info_url = f"https://api.mikai.me/v1/anime/{anime_id}/myInfo"
    info_resp = requests.get(info_url, headers=headers)

    payload = { 'animeId': anime_id, 'status': status }
    url = "https://api.mikai.me/v1/user/list"

    while True:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            print(f"✅ Аніме додано до списку зі статусом {status}")
            return resp.json().get("id")
        elif resp.status_code == 423:
            print("⚠️ Статус 423 — заблоковано. Чекаю 5 секунд перед повтором...")
            time.sleep(5)
        else:
            print(f"❌ Помилка додавання до списку: {resp.status_code} {resp.text}")
            return None



def main():
    missing = []
    with open('aband-list.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    for item in items:
        url = find_first_mikai_url(item)
        if url:
            print(f"➡️ Перший результат: {url}")
            anime_id = extract_anime_id(url)
            if not anime_id:
                continue
            else:
                add_to_list(anime_id, "dropped")
        else:
            missing.append(item)
            print(f"❌ Нічого не знайдено. {item}")
            item['status'] = 'Не знайдено'
    with open("missing.json", "a", encoding="utf-8") as f:
        for entry in missing:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
