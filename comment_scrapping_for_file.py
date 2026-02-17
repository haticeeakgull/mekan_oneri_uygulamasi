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
        search_url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z"
        driver.get(search_url)
        print(f"--- {place_name} ({lat}, {lon}) İşleniyor ---")
        time.sleep(6)

        # --- REKLAM SAVAR VE MEKAN SEÇME MANTIĞI ---
        try:
            # 1. Hamle: Olası reklam kartlarını/pop-upları ESC ile kapat
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)

            # Sol listedeki tüm sonuçları bul
            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

            target_clicked = False
            if results:
                for res in results:
                    # Kapsayıcı kutunun metnine bak (Sponsorlu/Reklam yazıyor mu?)
                    container_text = res.find_element(By.XPATH, "./../../../../..").text

                    if "Sponsorlu" in container_text or "Reklam" in container_text:
                        print(
                            f"Sponsorlu sonuç ({res.get_attribute('aria-label')}) atlandı..."
                        )
                        continue

                    # Reklam değilse, organik sonuca tıkla
                    print(
                        f"Organik mekana tıklanıyor: {res.get_attribute('aria-label')}"
                    )
                    driver.execute_script("arguments[0].click();", res)
                    target_clicked = True
                    break

            if not target_clicked:
                print("Uyarı: Organik sonuç bulunamadı!")
                # Eğer hiç organik sonuç yoksa ama sayfa doğrudan açıldıysa devam etsin

            time.sleep(4)
        except Exception as e:
            print(f"Mekan seçme hatası: {e}")

        # 2. ADRES DOĞRULAMA
        try:
            address_btn = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[contains(@aria-label, "Adres:")]')
                )
            )
            print(f"Doğrulanan Adres: {address_btn.get_attribute('aria-label')}")
        except:
            pass

        # 3. YORUMLARA GİT VE SCROLL
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

            for i in range(15):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                time.sleep(2)
                # İstersen her scroll'da bir PAGE_DOWN da atabilirsin (daha garantidir)
                scrollable_div.send_keys(Keys.PAGE_DOWN)
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
    df_reversed = df.iloc[::-1]
    toplu_sonuc = []

    # Şubeleri teker teker gez
    for index, row in df_reversed.iterrows():
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
            with open("toplu_mekan_verisi_yedek1.json", "w", encoding="utf-8") as f:
                json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)

    with open("final_mekan_verisi.json", "w", encoding="utf-8") as f:
        json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)


hepsini_topla()
