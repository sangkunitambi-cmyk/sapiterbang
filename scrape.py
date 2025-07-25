import requests
from bs4 import BeautifulSoup

url = "https://anichin.click/?id=v6udn7o"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

try:
    # Ikuti redirect secara manual
    response = requests.get(url, headers=headers, allow_redirects=True)
    print("Final URL:", response.url)

    # Coba ekstrak iframe OK.ru kalau ada di HTML
    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe")
    iframe_src = iframe["src"] if iframe else "Tidak ditemukan iframe dalam redirect"

    print("OK.ru Embed:", iframe_src)

    # Simpan ke file
    with open("hasil_okru.txt", "w", encoding="utf-8") as f:
        f.write(f"Final URL: {response.url}\n")
        f.write(f"OK.ru Embed: {iframe_src}\n")

except Exception as e:
    print("Terjadi error:", e)
