import time
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def google_maps_full_scraper(place_name):
    chrome_options = Options()
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)

    lat, lon, full_address = "Bulunamadı", "Bulunamadı", "Adres bulunamadı"
    all_reviews = []

    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 15)

        # 1. ARAMA VE SAYFAYI AÇMA
        search_query = f"{place_name} Ankara"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        driver.get(url)
        print(f"--- {place_name} İşleniyor ---")
        time.sleep(5)

        # 2. KOORDİNATLARI VE ADRESİ ÇEKME
        try:
            current_url = driver.current_url
            coords = re.search(r"@([-?\d\.]+),([-?\d\.]+)", current_url)
            if coords:
                lat, lon = coords.group(1), coords.group(2)

            address_element = driver.find_element(
                By.XPATH, '//button[contains(@aria-label, "Adres:")]'
            )
            full_address = address_element.get_attribute("aria-label").replace(
                "Adres: ", ""
            )
        except:
            print(
                "Koordinat veya adres o an alınamadı (Detay sayfasında tekrar denenecek)."
            )

        # 3. YORUMLAR SEKMESİNE GEÇİŞ (KRİTİK BÖLÜM)
        # 3. YORUMLAR SEKMESİNE GEÇİŞ (REKLAM ENGELLEYİCİ MANTIK)
        print("Yorumlar sekmesi aranıyor...")
        try:
            # Önce sayfa zaten detay modunda mı bak (Doğrudan açılmış olabilir)
            reviews_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//button[contains(@aria-label, "Yorumlar")] | //div[@role="tab" and contains(., "Yorumlar")]',
                    )
                )
            )
            reviews_btn.click()
            print("Doğrudan sekmeye tıklandı.")
        except:
            print(
                "Özet ekran/Arama sonuçları saptandı. Sponsorlu olmayan sonuç aranıyor..."
            )
            try:
                # Tüm sonuçları (hfpxzc class'lı elementleri) listele
                results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

                target_node = None
                for res in results:
                    # Bu sonucun üstünde veya yakınında "Sponsorlu" yazıyor mu kontrol et
                    # Genellikle 'Sponsorlu' yazısı bir üst div içinde olur
                    parent_text = res.find_element(By.XPATH, "./../../..").text

                    if "Sponsorlu" in parent_text or "Reklam" in parent_text:
                        print("Sponsorlu içerik atlandı...")
                        continue
                    else:
                        # İlk sponsorlu olmayan sonucu bulduk!
                        target_node = res
                        break

                if target_node:
                    driver.execute_script("arguments[0].click();", target_node)
                    print(f"Organik sonuca tıklandı.")
                    time.sleep(5)

                    # Şimdi yorumlar sekmesine tıkla
                    reviews_btn = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//button[contains(@aria-label, "Yorumlar")]')
                        )
                    )
                    reviews_btn.click()
                else:
                    print("Uygun bir sonuç bulunamadı.")
            except Exception as e:
                print(f"Mekana ulaşılamadı. Hata: {e}")

        # 4. KAYDIRMA VE YÜKLEME
        try:
            scrollable_div = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//div[contains(@class, "m67B6")] | //div[@role="main" and @tabindex="-1"]',
                    )
                )
            )
            print("Yorumlar aşağı kaydırılıyor...")

            for i in range(20):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                time.sleep(2)

                # "Diğer" (Daha fazla) butonlarını aç
                more_btns = driver.find_elements(
                    By.XPATH,
                    '//button[contains(., "Diğer") or contains(@aria-label, "Daha fazla")]',
                )
                for b in more_btns:
                    try:
                        driver.execute_script("arguments[0].click();", b)
                    except:
                        pass

                current_count = len(driver.find_elements(By.CLASS_NAME, "MyEned"))
                print(f"Yüklenen yorum: {current_count}")
                if current_count >= 60:
                    break
        except:
            print("Kaydırma alanı bulunamadı.")

        # 5. VERİLERİ TOPLA
        review_elements = driver.find_elements(By.CLASS_NAME, "MyEned")
        for el in review_elements:
            text = el.text.strip()
            if text and text not in all_reviews:
                all_reviews.append(text)
            if len(all_reviews) >= 60:
                break

    except Exception as e:
        print(f"Genel Hata: {e}")
    finally:
        return {
            "isim": place_name,
            "enlem": lat,
            "boylam": lon,
            "adres": full_address,
            "yorumlar": all_reviews,
        }


# --- ÇALIŞTIRMA ---
sonuc = google_maps_full_scraper("Timboo Kafe")
with open("mekan_verisi.json", "w", encoding="utf-8") as f:
    json.dump(sonuc, f, ensure_ascii=False, indent=4)
print(f"\nİşlem Tamamlandı! {len(sonuc['yorumlar'])} yorum kaydedildi.")
