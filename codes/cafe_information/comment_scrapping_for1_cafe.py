import time
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def google_maps_full_scraper(place_name, lat, lon):
    chrome_options = Options()
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    profil_yolu = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\User Data"

    chrome_options.add_argument(f"--user-data-dir={profil_yolu}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    wait = WebDriverWait(driver, 15)
    all_reviews = []

    try:
        # Arama URL'si - googleusercontent yerine doğrudan maps kullanmak daha stabildir
        url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
        driver.get(url)
        print(f"--- {place_name} Hedefleniyor ---")
        time.sleep(6)

        # 1. Sonuç Seçimi (Reklam Savar)
        try:
            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if results:
                target_element = None
                for res in results:
                    parent_box = res.find_element(By.XPATH, "./../../../../..").text
                    if "Sponsorlu" in parent_box or "Reklam" in parent_box:
                        continue
                    target_element = res
                    break

                if target_element:
                    driver.execute_script("arguments[0].click();", target_element)
                    time.sleep(4)
        except:
            pass

        # 2. Yorumlar Sekmesine Geçiş
        try:
            reviews_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[contains(@aria-label, "Yorumlar")]')
                )
            )
            reviews_btn.click()
            time.sleep(3)
        except:
            print("Yorumlar sekmesi zaten açık veya bulunamadı.")

        # 3. Scroll ve Toplama
        try:
            scrollable_div = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@role="main" and @tabindex="-1"]')
                )
            )
            for _ in range(10):  # Hız için şimdilik 10 scroll
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                time.sleep(1.5)
        except:
            pass

        # 4. Ayıklama
        spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        all_reviews = [s.text.strip() for s in spans if s.text.strip()]

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        driver.quit()

    return list(set(all_reviews))  # Tekrarları silerek döndür


def veri_kaydet(isim, lat, lon, yorumlar):
    dosya_adi = (
        "eksik_mekan_verileri_ankara.json"  # Şehir ismi eklemek karışıklığı önler
    )
    yeni_kayit = {"isim": isim, "osm_lat": lat, "osm_lon": lon, "yorumlar": yorumlar}

    mevcut_veri = []
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r", encoding="utf-8") as f:
            try:
                mevcut_veri = json.load(f)
            except:
                mevcut_veri = []

    mevcut_veri.append(yeni_kayit)
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(mevcut_veri, f, ensure_ascii=False, indent=4)
    print(f"✅ {isim} ({len(yorumlar)} yorum) kaydedildi.")


def baslat():
    print("\n--- Google Maps Veri Tamamlama Sistemi ---")
    print("1. Manuel Tek Kafe Ara")
    print("2. CSV'den Toplu Tara")
    secim = input("Seçim: ")

    if secim == "1":
        isim = input("Kafe İsmi: ")
        lat = input("Lat: ")
        lon = input("Lon: ")
        yorumlar = google_maps_full_scraper(isim, lat, lon)
        veri_kaydet(isim, lat, lon, yorumlar)
    elif secim == "2":
        dosya = input("CSV Yolu: ")
        if os.path.exists(dosya):
            df = pd.read_csv(dosya)
            for _, row in df.iterrows():
                y = google_maps_full_scraper(row["isim"], row["lat"], row["lon"])
                veri_kaydet(row["isim"], row["lat"], row["lon"], y)
                time.sleep(2)


if __name__ == "__main__":
    baslat()
