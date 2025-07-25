import json
import requests
from bs4 import BeautifulSoup
import base64
import time
import binascii

def get_episode_links(series_url):
    r = requests.get(series_url)
    soup = BeautifulSoup(r.text, "html.parser")
    episodelist = soup.select(".episodelist ul li a")
    return [{'title': a.select_one('h4').text, 'url': a['href']} for a in episodelist]

def get_video_iframe(episode_url):
    r = requests.get(episode_url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    iframe = soup.select_one('#embed_holder .player-embed iframe')
    main_video = iframe['src'] if iframe else None

    if not main_video:
        print(f"Iframe video utama tidak ditemukan untuk {episode_url}")

    mirrors = []
    for option in soup.select('select.mirror option'):
        if option['value']:
            try:
                decoded = base64.b64decode(option['value']).decode('utf-8')
                iframe_soup = BeautifulSoup(decoded, 'html.parser')
                iframe_tag = iframe_soup.find('iframe')
                if iframe_tag and iframe_tag.get('src'):
                    mirrors.append({
                        'server': option.text.strip(),
                        'iframe': iframe_tag['src']
                    })
            except (binascii.Error, UnicodeDecodeError) as e:
                print(f"Error dekode Base64 untuk server {option.text.strip()}: {e}")
                continue # Lanjutkan ke mirror berikutnya

    return {
        'main_video': main_video,
        'mirrors': mirrors
    }

# --- Import JSON file dengan judul dan link seri ---
with open('anime_list.json', 'r', encoding='utf-8') as f:
    anime_data = json.load(f)

full_result = []

for anime in anime_data['anime_list']:
    print(f"Scraping: {anime['title']}")
    episodes = get_episode_links(anime['url'])
    episode_results = []

    for ep in episodes:
        print(f"   Episode: {ep['title']}")
        video_data = get_video_iframe(ep['url'])
        episode_results.append({
            'episode_title': ep['title'],
            'episode_url': ep['url'],
            'main_video': video_data['main_video'],
            'mirrors': video_data['mirrors']
        })
        time.sleep(1)  # Biar gak kebanyakan request

    full_result.append({
        'title': anime['title'],
        'url': anime['url'],
        'episodes': episode_results
    })

# --- Simpan hasil scraping ke file baru ---
with open('scraped_result.json', 'w', encoding='utf-8') as f:
    json.dump(full_result, f, indent=2, ensure_ascii=False)
