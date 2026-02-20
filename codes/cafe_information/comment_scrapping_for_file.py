import time
import json
import os
import shutil
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def google_maps_branch_scraper(place_name, lat, lon):
    """Tarayıcıyı açıp yorumları çeken çekirdek fonksiyon."""
    chrome_options = Options()
    # Kendi Brave yolunu ve profilini buraya ekle
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    profil_yolu = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\User Data"

    chrome_options.add_argument(f"--user-data-dir={profil_yolu}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    all_reviews = []

    try:
        search_url = (
            f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
        )
        driver.get(search_url)
        print(f"--- {place_name} İşleniyor ---")
        time.sleep(5)

        # 1. ORGANİK SONUCU BUL VE TIKLA
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if results:
                for res in results:
                    container_text = res.find_element(By.XPATH, "./../../../../..").text
                    if (
                        "Sponsorlu" not in container_text
                        and "Reklam" not in container_text
                    ):
                        driver.execute_script("arguments[0].click();", res)
                        time.sleep(4)
                        break
        except Exception as e:
            print(f"Seçim hatası: {e}")

        # 2. YORUMLARA GİT VE SCROLL
        try:
            reviews_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[contains(@aria-label, "Yorumlar")]')
                )
            )
            reviews_btn.click()
            time.sleep(3)

            scrollable_div = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@role="main" and @tabindex="-1"]')
                )
            )

            # 10-15 kez aşağı kaydır (ihtiyaca göre artırabilirsin)
            for _ in range(12):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                time.sleep(1.5)
        except:
            print("Yorum alanı bulunamadı veya hiç yorum yok.")

        # 3. YORUMLARI TOPLA
        review_spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        for span in review_spans:
            text = span.text.strip()
            if text and text not in all_reviews:
                all_reviews.append(text)

    except Exception as e:
        print(f"Scraper hatası: {e}")
    finally:
        driver.quit()
        return all_reviews


def hepsini_topla(sehir):
    """CSV'yi okuyan, yedekleyen ve döngüyü yöneten ana fonksiyon."""
    json_path = f"json_files/final_mekan_verisi_{sehir}.json"
    backup_path = f"json_files/final_mekan_verisi_{sehir}.json.bak"
    csv_kalanlar_path = f"csv_files/{sehir.lower()}_kafeler_kalanlar.csv"

    # Mevcut JSON verisini yükle
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            toplu_sonuc = json.load(f)
    else:
        toplu_sonuc = []

    # Kalanlar listesini oku
    if not os.path.exists(csv_kalanlar_path):
        print("Kalanlar dosyası yok!")
        return

    df = pd.read_csv(csv_kalanlar_path)
    # Baştan sona veya sondan başa; nasıl istersen
    for index, row in df.iterrows():
        # JSON'da bu mekana bak: Zaten var mı ve yorumu çekilmiş mi?
        zaten_taranmis = False
        for kayit in toplu_sonuc:
            if kayit["osm_lat"] == row["lat"] and kayit["osm_lon"] == row["lon"]:
                if len(kayit.get("yorumlar", [])) > 0:
                    zaten_taranmis = True
                    break

        if zaten_taranmis:
            print(f"⏩ {row['isim']} zaten taranmış ve yorumu var, geçiliyor.")
            continue

        # Eğer yukarıdaki kontrole takılmadıysa, bot yorum çekmeye başlar
        print(f"\n🔍 [{index+1}/{len(df)}] {row['isim']} taranıyor...")
        cekilen_yorumlar = google_maps_branch_scraper(
            row["isim"], row["lat"], row["lon"]
        )

        # ... veriyi kaydetme işlemleri

        # Veriyi ekle
        toplu_sonuc.append(
            {
                "isim": row["isim"],
                "osm_lat": row["lat"],
                "osm_lon": row["lon"],
                "yorumlar": cekilen_yorumlar,
            }
        )

        # --- YEDEKLE VE KAYDET ---
        if os.path.exists(json_path):
            shutil.copy2(json_path, backup_path)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)

        print(f"Kaydedildi. Toplam mekan sayısı: {len(toplu_sonuc)}")


if __name__ == "__main__":
    hepsini_topla()
