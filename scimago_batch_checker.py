import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

def search_scimago(journal_name):
    """
    Mencari jurnal di Scimago dan mengekstrak kuartil terbarunya serta area subjek.

    Args:
        journal_name (str): Nama jurnal yang akan dicari.

    Returns:
        dict: Sebuah dictionary yang berisi judul jurnal, kuartil, kategori, dan tautan SJR.
              Mengembalikan nilai 'Not Found' jika jurnal tidak dapat ditemukan.
    """
    # --- Header untuk meniru kunjungan browser asli ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # --- Membangun URL pencarian ---
    search_url = f"https://www.scimagojr.com/journalsearch.php?q={journal_name.replace(' ', '+')}&tip=sid&clean=0"
    
    print(f"Mencari: '{journal_name}'...")

    try:
        # --- Permintaan pertama: Dapatkan halaman hasil pencarian ---
        response = requests.get(search_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Temukan tautan hasil pencarian pertama ---
        search_results_div = soup.find('div', class_='search_results')
        if not search_results_div:
            print("  -> Tidak ditemukan kontainer hasil pencarian.")
            return {"title": "Not Found", "quartile": "Not Found", "categories": "Not Found", "link": "N/A"}

        first_result = search_results_div.find('a')
        if not first_result or not first_result.get('href'):
            print(f"  -> Tidak dapat menemukan tautan langsung untuk '{journal_name}'.")
            return {"title": "Not Found", "quartile": "Not Found", "categories": "Not Found", "link": "N/A"}

        journal_page_url = "https://www.scimagojr.com/" + first_result['href']
        found_title = first_result.text.strip()
        print(f"  -> Ditemukan '{found_title}'. Mengambil detail...")

        # --- Permintaan kedua: Pergi ke halaman spesifik jurnal ---
        time.sleep(random.uniform(1, 3)) # Jeda sopan
        journal_response = requests.get(journal_page_url, headers=headers, timeout=20)
        journal_response.raise_for_status()
        
        journal_soup = BeautifulSoup(journal_response.content, 'html.parser')

        # --- Temukan informasi kuartil ---
        quartile_value = "Not Found"
        quartile_table = journal_soup.find('div', class_='quartiles')
        if quartile_table:
            all_quartiles = quartile_table.find_all('div', class_='quartile')
            if all_quartiles:
                last_quartile_div = all_quartiles[-1]
                year_span = last_quartile_div.find('span', class_='year')
                q_span = last_quartile_div.find('span', class_='quartile')
                if year_span and q_span:
                    quartile_value = f"{q_span.text.strip()} ({year_span.text.strip()})"
                    print(f"  -> Berhasil! Kuartil adalah {quartile_value}")
        
        # --- Temukan informasi Subject Area and Category ---
        categories_str = "Not Found"
        subject_div = journal_soup.find('div', class_='table_area')
        if subject_div:
            categories_list = []
            # Temukan semua baris di dalam tabel kategori
            rows = subject_div.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2: # Pastikan ada kolom area dan kategori
                    area = cols[0].text.strip()
                    category = cols[1].text.strip()
                    categories_list.append(f"{area}: {category}")
            
            if categories_list:
                categories_str = '; '.join(categories_list)
                print(f"  -> Ditemukan {len(categories_list)} kategori.")
        
        return {"title": found_title, "quartile": quartile_value, "categories": categories_str, "link": journal_page_url}

    except requests.exceptions.RequestException as e:
        print(f"  -> Terjadi kesalahan: {e}")
        return {"title": "Error", "quartile": "Error", "categories": "Error", "link": "Error"}


def main():
    """
    Fungsi utama untuk menjalankan scraper.
    """
    # --- Baca nama jurnal dari file teks ---
    try:
        with open('journals.txt', 'r', encoding='utf-8') as f:
            journal_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: 'journals.txt' tidak ditemukan. Harap buat file ini dan tambahkan nama jurnal ke dalamnya.")
        return

    if not journal_list:
        print("Error: 'journals.txt' kosong. Harap tambahkan nama jurnal ke dalamnya.")
        return

    print(f"Ditemukan {len(journal_list)} jurnal untuk diproses.")
    
    # --- Proses setiap jurnal dan simpan hasilnya ---
    results = []
    for journal in journal_list:
        result_data = search_scimago(journal)
        results.append({
            'Searched Journal': journal,
            'Found Journal Title': result_data['title'],
            'Quartile': result_data['quartile'],
            'Subject Area and Category': result_data['categories'], # Kolom baru ditambahkan di sini
            'SJR Link': result_data['link']
        })
        # Tambahkan jeda acak antar pencarian agar tidak membebani server
        time.sleep(random.uniform(2, 5)) 

    # --- Simpan hasil ke file CSV menggunakan pandas ---
    df = pd.DataFrame(results)
    output_filename = 'scimago_results.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8')

    print(f"\nProses selesai. Hasil disimpan ke '{output_filename}'.")


if __name__ == "__main__":
    main()
