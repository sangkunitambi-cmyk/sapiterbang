import cloudscraper
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def scrape_anichin_list(url, output_dir="scraping_results"):
    # Pastikan folder hasil ada
    os.makedirs(output_dir, exist_ok=True)

    print(f"Scraping: {url}")
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)

    # Debug: Simpan HTML mentah buat cek hasil
    html_path = os.path.join(output_dir, "debug.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    if response.status_code != 200:
        print(f"Gagal akses halaman: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    anime_links = []

    # Selector: cari semua link ke seri anime
    for a in soup.select('a[href*="/seri/"]'):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if href and title:
            # Buat URL absolut
            full_url = href
            if not full_url.startswith("http"):
                full_url = os.path.join(url, href.lstrip("/"))
            anime_links.append({
                "title": title,
                "url": full_url
            })

    print(f"Total anime ditemukan: {len(anime_links)}")

    result = {
        "source_url": url,
        "scraped_at": datetime.now().isoformat(),
        "total_found": len(anime_links),
        "anime_list": anime_links
    }

    # Simpan hasil ke file JSON
    output_file = os.path.join(output_dir, "hasil.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Hasil tersimpan di: {output_file}")

if __name__ == "__main__":
    # Ganti ke halaman list mode Anichin yang kamu mau scrape
    base_url = "https://anichin.cafe/seri/list-mode/"
    scrape_anichin_list(base_url)
