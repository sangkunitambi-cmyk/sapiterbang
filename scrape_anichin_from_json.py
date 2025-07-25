import json
import requests
from bs4 import BeautifulSoup
import base64
import time
import binascii

# PENTING: Tambahkan Headers untuk menyamar sebagai browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://anichin.cafe/' # Referer juga kadang dicek
}

def get_soup(url):
    """Fungsi helper yang lebih tangguh untuk request HTML."""
    try:
        # Tambahkan headers dan timeout di sini
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()  # Ini akan error jika status code bukan 2xx
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error saat request ke {url}: {e}")
        return None

def get_episode_links(series_url):
    print(f"Mengambil daftar episode dari: {series_url}")
    soup = get_soup(series_url)
    if not soup:
        return []

    # Selector lu udah bener
    episodelist_tags = soup.select(".episodelist ul li a")
    if not episodelist_tags:
        print("Gagal menemukan list episode, mungkin selector perlu diupdate.")
        return []

    episodes = [{'title': a.select_one('h4').text.strip(), 'url': a['href']} for a in episodelist_tags]
    
    # BALIK URUTAN listnya biar dari episode 1, 2, 3, ...
    episodes.reverse()
    
    print(f"Ditemukan {len(episodes)} episode.")
    return episodes

def get_video_iframe(episode_url):
    soup = get_soup(episode_url)
    if not soup:
        return {'main_video': None, 'mirrors': []}

    # Bagian ini gw biarin, karena logika lu udah bener buat ambil iframe utama
    iframe = soup.select_one('#embed_holder .player-embed iframe, #pembed iframe')
    main_video = iframe['src'] if iframe and iframe.has_attr('src') else None

    # Logika mirror lu juga udah pas banget!
    mirrors = []
    mirror_select = soup.find('select', class_='mirror')
    if mirror_select:
        for option in mirror_select.find_all('option'):
            encoded_value = option.get('value')
            if encoded_value:
                try:
                    decoded = base64.b64decode(encoded_value).decode('utf-8')
                    iframe_soup = BeautifulSoup(decoded, 'html.parser')
                    iframe_tag = iframe_soup.find('iframe')
                    if iframe_tag and iframe_tag.get('src'):
                        mirrors.append({
                            'server': option.text.strip(),
                            'iframe': iframe_tag['src']
                        })
                except (binascii.Error, UnicodeDecodeError):
                    # Error handling ini udah bagus, kita keep
                    # print(f"Gagal decode base64 untuk server {option.text.strip()}")
                    continue
    
    if not main_video and not mirrors:
        print(f"  > Peringatan: Tidak ada video (utama/mirror) yang ditemukan di {episode_url}")

    return {
        'main_video': main_video,
        'mirrors': mirrors
    }

# --- Main Logic (tidak banyak berubah) ---

try:
    with open('anime_list.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
except FileNotFoundError:
    print("Error: File 'anime_list.json' tidak ditemukan. Pastikan file ada di folder yang sama.")
    exit()

full_result = []

for anime in anime_data['anime_list']:
    print(f"\n{'='*10} Scraping: {anime['title']} {'='*10}")
    episodes = get_episode_links(anime['url'])
    episode_results = []
    
    # Batasi untuk testing, hapus/komen baris ini untuk scrape semua
    # episodes = episodes[:3] 

    for ep in episodes:
        print(f"   > Processing Episode: {ep['title']}")
        video_data = get_video_iframe(ep['url'])
        episode_results.append({
            'episode_title': ep['title'],
            'episode_url': ep['url'],
            'main_video_iframe': video_data['main_video'],
            'mirror_servers': video_data['mirrors']
        })
        # Jeda antar request episode, ini udah bagus
        time.sleep(1)

    full_result.append({
        'title': anime['title'],
        'url': anime['url'],
        'episodes': episode_results
    })
    # Jeda antar ganti anime
    print("Selesai scrape satu judul, jeda 3 detik sebelum lanjut...")
    time.sleep(3)

print("\nScraping selesai, menyimpan hasil ke 'scraped_result.json'...")
with open('scraped_result.json', 'w', encoding='utf-8') as f:
    json.dump(full_result, f, indent=4, ensure_ascii=False)

print("Berhasil!")
