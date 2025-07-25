import json
import time
import base64
import binascii
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Menyiapkan driver Selenium Chrome untuk berjalan di server (headless)."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
    
    # Tidak perlu chromedriver_path jika sudah di-setup oleh GitHub Actions
    driver = webdriver.Chrome(options=options)
    return driver

def get_episode_links(driver, series_url):
    """Mengambil daftar episode dari halaman seri menggunakan Selenium."""
    print(f"Mengambil daftar episode dari: {series_url}")
    try:
        driver.get(series_url)
        # Tunggu sampai list episode muncul (maksimal 20 detik)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".episodelist ul li a"))
        )
        
        # Ambil page source SETELAH javascript selesai loading
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        episodelist_tags = soup.select(".episodelist ul li a")
        if not episodelist_tags:
            print("Gagal menemukan list episode, selector mungkin perlu diupdate.")
            return []

        episodes = [{'title': a.select_one('h4').text.strip(), 'url': a['href']} for a in episodelist_tags]
        episodes.reverse() # Balik urutan biar dari episode 1
        print(f"Ditemukan {len(episodes)} episode.")
        return episodes

    except Exception as e:
        print(f"Error saat mengambil list episode: {e}")
        driver.save_screenshot('debug_screenshot.png')
        return []

def get_video_iframe(driver, episode_url):
    """Mengambil iframe video dari halaman episode."""
    try:
        driver.get(episode_url)
        # Tunggu sampai dropdown server video muncul
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.mirror"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        iframe = soup.select_one('#embed_holder .player-embed iframe, #pembed iframe')
        main_video = iframe['src'] if iframe and iframe.has_attr('src') else None

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
                        continue
        
        return {'main_video': main_video, 'mirrors': mirrors}

    except Exception as e:
        print(f"  > Peringatan: Tidak bisa mengambil video dari {episode_url}. Error: {e}")
        driver.save_screenshot('debug_screenshot.png')
        return {'main_video': None, 'mirrors': []}

# --- Main Logic ---

driver = setup_driver()
full_result = []

try:
    with open('anime_list.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)

    for anime in anime_data['anime_list']:
        print(f"\n{'='*10} Scraping: {anime['title']} {'='*10}")
        episodes = get_episode_links(driver, anime['url'])
        episode_results = []
        
        # Batasi untuk testing (opsional), hapus/komen baris ini untuk scrape semua
        # episodes = episodes[:2] 

        for ep in episodes:
            print(f"   > Processing Episode: {ep['title']}")
            video_data = get_video_iframe(driver, ep['url'])
            episode_results.append({
                'episode_title': ep['title'],
                'episode_url': ep['url'],
                'main_video_iframe': video_data['main_video'],
                'mirror_servers': video_data['mirrors']
            })
            time.sleep(2) # Kasih jeda sopan antar request

        full_result.append({
            'title': anime['title'],
            'url': anime['url'],
            'episodes': episode_results
        })
        time.sleep(3) # Jeda antar ganti judul anime

finally:
    # Penting! Selalu tutup browser setelah selesai
    print("Menutup browser...")
    driver.quit()

print("\nScraping selesai, menyimpan hasil ke 'scraped_result.json'...")
with open('scraped_result.json', 'w', encoding='utf-8') as f:
    json.dump(full_result, f, indent=4, ensure_ascii=False)

print("Berhasil!")
