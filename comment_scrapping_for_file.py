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
    profil_yolu = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\User Data"

    chrome_options.add_argument(f"--user-data-dir={profil_yolu}")
    chrome_options.add_argument("--profile-directory=Default")

    # Otomasyon izlerini gizle (Giriş yaptığında Google'ın 'şüpheli işlem' dememesi için)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    all_reviews = []

    try:
        search_url = (
            f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
        )
        driver.get(search_url)
        print(f"--- {place_name} ({lat}, {lon}) İşleniyor ---")
        time.sleep(6)

        # sponsorlu engelleme ve mekan seçme
        try:
            # Olası reklam kartlarını/pop-upları ESC ile kapatma
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)

            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

            target_clicked = False
            if results:
                for res in results:

                    container_text = res.find_element(By.XPATH, "./../../../../..").text

                    if "Sponsorlu" in container_text or "Reklam" in container_text:
                        print(
                            f"Sponsorlu sonuç ({res.get_attribute('aria-label')}) atlandı..."
                        )
                        continue

                    print(
                        f"Organik mekana tıklanıyor: {res.get_attribute('aria-label')}"
                    )
                    driver.execute_script("arguments[0].click();", res)
                    target_clicked = True
                    break

            if not target_clicked:
                print("Uyarı: Organik sonuç bulunamadı!")

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
    # 1. Önce mevcut veriyi yükle (Eskiler silinmesin diye)
    try:
        with open("final_mekan_verisi.json", "r", encoding="utf-8") as f:
            toplu_sonuc = json.load(f)
        print(f"Mevcut veri yüklendi: {len(toplu_sonuc)} mekan zaten var.")
    except FileNotFoundError:
        toplu_sonuc = []
        print("Mevcut veri bulunamadı, yeni dosya oluşturulacak.")

    # 2. Sadece kalanları oku
    df = pd.read_csv("ankara_kafeler_kalanlar.csv")
    df_reversed = df.iloc[::-1]

    for index, row in df_reversed.iterrows():
        print(f"\n[{index+1}/{len(df)}] {row['isim']} taranıyor...")
        yorumlar = google_maps_branch_scraper(row["isim"], row["lat"], row["lon"])

        # Yeni veriyi listeye ekle
        toplu_sonuc.append(
            {
                "isim": row["isim"],
                "osm_lat": row["lat"],
                "osm_lon": row["lon"],
                "yorumlar": yorumlar,
            }
        )

        # 3. Her şubeden sonra dosyayı güncelle (En garantisi budur)
        # Böylece bot çökerse o ana kadar çektiği her şey dosyaya yazılmış olur
        with open("final_mekan_verisi.json", "w", encoding="utf-8") as f:
            json.dump(toplu_sonuc, f, ensure_ascii=False, indent=4)


hepsini_topla()
