import time
import re
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def google_maps_branch_scraper(place_name, lat, lon):
    chrome_options = Options()
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    all_reviews = []

    try:
        # KRİTİK DEĞİŞİKLİK: Doğrudan koordinat odaklı arama URL'si
        # Bu URL Google'ı o koordinatın tam üstüne bırakır
        search_url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z"
        driver.get(search_url)
        print(f"--- {place_name} ({lat}, {lon}) İşleniyor ---")
        time.sleep(6)

        # 1. MEKANI SEÇME (Koordinata en yakın olanı bulma)
        try:
            # Sol listedeki ilk organik sonuca tıkla (Çünkü koordinat verdiğimiz için ilk sonuç o şubedir)
            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if results:
                driver.execute_script("arguments[0].click();", results[0])
                time.sleep(4)
            else:
                print("Sonuç bulunamadı, muhtemelen doğrudan detay sayfası açıldı.")
        except:
            pass

        # 2. ADRES DOĞRULAMA (İsteğe bağlı)
        try:
            address_btn = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[contains(@aria-label, "Adres:")]')
                )
            )
            current_address = address_btn.get_attribute("aria-label")
            print(f"Doğrulanan Adres: {current_address}")
        except:
            pass

        # 3. YORUMLARA GİT VE SCROLL (Senin çalışan scroll mantığın)
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

            for _ in range(15):  # Her şube için 30-40 yorum yeterli dersen
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                time.sleep(2)
        except:
            print("Yorum alanı bulunamadı.")

        # 4. VERİ TOPLAMA
        review_spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        for span in review_spans:
            text = span.text.strip()
            if text and text not in all_reviews:
                all_reviews.append(text)

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        driver.quit()
        return all_reviews


# --- TOPLU İŞLEME DÖNGÜSÜ ---
def hepsini_topla():
    df = pd.read_csv("ankara_kafeler.csv")  # OSM'den gelen koordinatlı liste
    toplu_sonuc = []

    # Şubeleri teker teker gez
    for index, row in df.iterrows():
        print(f"\n[{index+1}/{len(df)}] {row['isim']} taranıyor...")
        yorumlar = google_maps_branch_scraper(row["isim"], row["lat"], row["lon"])

        toplu_sonuc.append(
            {
                "isim": row["isim"],
                "osm_lat": row["lat"],
                "osm_lon": row["lon"],
                "yorumlar": yorumlar,
            }
        )

        # Her 5 şubede bir yedek al (Botun çökme ihtimaline karşı)
        if (index + 1) % 5 == 0:
            with open("toplu_mekan_verisi_yedek.json", "w", encoding="utf-8") as f:
                json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)

    with open("final_mekan_verisi.json", "w", encoding="utf-8") as f:
        json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)


hepsini_topla()  # Başlatmak için bunu kullanın
