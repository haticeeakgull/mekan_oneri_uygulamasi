import time
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def google_maps_full_scraper(place_name, lat, lon):
    chrome_options = Options()

    # DOĞRU: Burası .exe dosyasının yolu olmalı
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )

    # DOĞRU: User Data klasörüne kadar olan yol (Default'u buraya yazma!)
    profil_yolu = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\User Data"

    chrome_options.add_argument(f"--user-data-dir={profil_yolu}")
    chrome_options.add_argument("--profile-directory=Default")

    # Otomasyon izlerini gizle (Giriş yaptığında Google'ın 'şüpheli işlem' dememesi için)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    # Webdriver olduğunu gizle
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    wait = WebDriverWait(driver, 15)
    all_reviews = []

    try:
        # Arama URL'si
        url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
        driver.get(url)
        print(f"--- {place_name} Hedefleniyor ---")
        time.sleep(8)  # Profil yüklenirken biraz daha fazla süre tanı

        # ... (Geri kalan reklam savar ve scroll kısımları aynı kalabilir) ...
        # 2. REKLAM SAVAR SEÇİCİ
        print("Sonuçlar analiz ediliyor...")
        try:
            # Tüm sonuç kutularını bul (hfpxzc linkleri barındırır)
            results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

            target_element = None
            for res in results:
                # Kapsayıcı kutunun metnine bak (Sponsorlu yazısı burada olur)
                # Genellikle 5-6 seviye yukarıdadır
                parent_box = res.find_element(By.XPATH, "./../../../../..").text

                if "Sponsorlu" in parent_box or "Reklam" in parent_box:
                    print("Sponsorlu Starbucks atlandı.")
                    continue

                # Eğer reklam değilse, bu bizim organik sonucumuzdur
                target_element = res
                break

            if target_element:
                print(f"Doğru şube bulundu, giriş yapılıyor...")
                driver.execute_script("arguments[0].click();", target_element)
                time.sleep(5)
            else:
                print(
                    "Organik sonuç bulunamadı, doğrudan detay sayfası açılmış olabilir."
                )
        except Exception as e:
            print(f"Seçim hatası: {e}")

        # 3. YORUMLARA GEÇİŞ
        try:
            # Detay sayfası açıldıysa 'Yorumlar' butonuna bas
            reviews_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[contains(@aria-label, "Yorumlar")]')
                )
            )
            reviews_btn.click()
            time.sleep(3)
        except:
            print("Yorumlar sekmesine ulaşılamadı.")

        # 4. SCROLL VE TOPLAMA (Senin HTML analizindeki wiI7pd sınıfı ile)
        print("Yorumlar aşağı kaydırılıyor...")
        try:
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
                # Yeni yüklenenleri sayalım
                current_count = len(driver.find_elements(By.CLASS_NAME, "jftiEf"))
                if current_count >= 60:
                    break
        except:
            pass

        # 5. AYIKLAMA
        spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        for s in spans:
            if s.text.strip() and s.text.strip() not in all_reviews:
                all_reviews.append(s.text.strip())

    except Exception as e:
        print(f"Genel Hata: {e}")
    finally:
        driver.quit()

        with open("mekan_verisi.json", "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=4)
        return all_reviews


# --- TEST ---


lat_test, lon_test = "39.9070912", "32.8602278"
sonuc = google_maps_full_scraper("Arabica", lat_test, lon_test)
print(f"Bitti! Toplam {len(sonuc)} yorum alındı.")
