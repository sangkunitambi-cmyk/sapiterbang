import requests
import concurrent.futures

# Baca daftar proxy dari file
try:
    with open('proxies.txt', 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("[ERROR] File 'proxies.txt' tidak ditemukan. Pastikan file ada di repository.")
    proxies = []

def check_proxy(proxy):
    """Fungsi untuk mengetes satu proxy dengan request biasa."""
    try:
        proxy_dict = {'http': proxy, 'https': proxy}
        # Coba request ke website yang ringan dengan timeout singkat
        response = requests.get('https://api.ipify.org?format=json', proxies=proxy_dict, timeout=15)
        response.raise_for_status() # Cek error HTTP
        # Jika berhasil, cetak pesan sukses
        print(f"[HIDUP] {proxy} -> IP Publik: {response.json()['ip']}")
        return proxy
    except Exception:
        # Jika gagal, tidak perlu cetak apa-apa agar log bersih
        return None

if not proxies:
    print("File proxies.txt kosong atau tidak ditemukan.")
else:
    # Gunakan ThreadPoolExecutor untuk mengetes banyak proxy secara bersamaan
    print(f"--- Mulai Mengetes {len(proxies)} Proxy ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_proxy, proxies)
    
    # Kumpulkan semua proxy yang hidup
    live_proxies = [proxy for proxy in results if proxy]

    print(f"\n--- Tes Selesai. Ditemukan {len(live_proxies)} proxy yang hidup. ---")

    # Simpan hasilnya ke file baru, bahkan jika kosong
    with open('live_proxies.txt', 'w') as f:
        if live_proxies:
            for proxy in live_proxies:
                f.write(f"{proxy}\n")
            print("Daftar proxy yang hidup disimpan di 'live_proxies.txt'")
        else:
            print("Tidak ada proxy yang hidup. File 'live_proxies.txt' akan kosong.")
