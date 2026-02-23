import time
import pandas as pd
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def google_maps_finder(search_query, city_name):
    chrome_options = Options()

    # 1. BRAVE VE PROFIL AYARLARI
    # Brave .exe yolunu kontrol et
    chrome_options.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )

    # Kendi kullanıcı adınla yolu doğrula (brave://version/ içinden bakabilirsin)
    profil_yolu = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\User Data"
    chrome_options.add_argument(f"--user-data-dir={profil_yolu}")
    chrome_options.add_argument("--profile-directory=Default")

    # 2. OTOMASYON GİZLEME VE DİĞER AYARLAR
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
    found_cafes = []
    end_of_scroll = False

    try:
        # Arama URL'si
        url = f"https://www.google.com/maps/search/{search_query}+{city_name}"
        driver.get(url)

        print("Sayfa yükleniyor...")
        time.sleep(7)

        # 3. KAYDIRMA İŞLEMİ (Sayfa sonuna kadar)
        print(f"--- {city_name.upper()} İÇİN TARAMA BAŞLADI ---")
        try:
            scrollable_div = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
            )

            last_height = driver.execute_script(
                "return arguments[0].scrollHeight", scrollable_div
            )
            scroll_count = 0

            while not end_of_scroll:
                # Aşağı kaydır
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
                scroll_count += 1
                print(f"Kaydırma yapılıyor... {scroll_count}")
                time.sleep(3)  # Google'ın yeni sonuçları yüklemesi için süre

                # Kontrol 1: "Sayfanın sonuna ulaştınız" yazısı var mı?
                page_content = driver.page_source
                if (
                    "Sayfanın sonuna ulaştınız" in page_content
                    or "Başka sonuç yok" in page_content
                ):
                    print("✅ Google Maps: Sayfanın sonuna ulaştınız yazısı görüldü.")
                    end_of_scroll = True
                    break

                # Kontrol 2: Yükseklik değişimi (Yazı gelmese bile scroll durduysa çık)
                new_height = driver.execute_script(
                    "return arguments[0].scrollHeight", scrollable_div
                )
                if new_height == last_height:
                    time.sleep(2)  # Emin olmak için son bir bekleme
                    if new_height == driver.execute_script(
                        "return arguments[0].scrollHeight", scrollable_div
                    ):
                        print("ℹ️ Yeni sonuç yüklenmiyor, tarama tamamlandı.")
                        end_of_scroll = True

                last_height = new_height

                # Güvenlik sınırı (Çok büyük listelerde botun kilitlenmemesi için)
                if scroll_count > 100:
                    print("⚠️ Güvenlik sınırı (100 scroll) aşıldı.")
                    break

        except Exception as e:
            print(f"Kaydırma panelinde sorun oluştu: {e}")

        # 4. VERİLERİ TOPLA VE ANALİZ ET
        print("Mekan kartları analiz ediliyor...")
        places = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        print(
            f"Toplam {len(places)} potansiyel mekan bulundu. Koordinatlar ayıklanıyor..."
        )

        for place in places:
            try:
                name = place.get_attribute("aria-label")
                link = place.get_attribute("href")

                # Koordinat Ayıklama (Regex - İki farklı format için)
                coord_match = re.search(r"!3d([-?\d\.]+)!4d([-?\d\.]+)", link)
                if not coord_match:
                    coord_match = re.search(r"@([-?\d\.]+),([-?\d\.]+)", link)

                if coord_match:
                    lat = coord_match.group(1)
                    lon = coord_match.group(2)

                    # Liste içinde daha önce kaydedilip kaydedilmediğini kontrol et
                    if not any(
                        f["lat"] == lat and f["lon"] == lon for f in found_cafes
                    ):
                        found_cafes.append({"isim": name, "lat": lat, "lon": lon})
                else:
                    # Link içinden '@' ile başlayan parçayı manuel ayıkla
                    parts = link.split("/")
                    for part in parts:
                        if part.startswith("@"):
                            coords = part.replace("@", "").split(",")
                            if len(coords) >= 2:
                                lat, lon = coords[0], coords[1]
                                if not any(
                                    f["lat"] == lat and f["lon"] == lon
                                    for f in found_cafes
                                ):
                                    found_cafes.append(
                                        {"isim": name, "lat": lat, "lon": lon}
                                    )
            except:
                continue

    except Exception as e:
        print(f"Genel bir hata oluştu: {e}")

    finally:
        driver.quit()

    # 5. CSV KAYDI
    if found_cafes:
        if not os.path.exists("csv_files"):
            os.makedirs("csv_files")

        filename = f"csv_files/{city_name.lower()}_kafe_listesi.csv"
        df = pd.DataFrame(found_cafes)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n✅ İŞLEM TAMAMLANDI!")
        print(f"📊 Toplam bulunan benzersiz mekan: {len(found_cafes)}")
        print(f"📍 Dosya buraya kaydedildi: {filename}")
    else:
        print(
            "❌ Hiç mekan bulunamadı. Lütfen arama terimini veya bağlantınızı kontrol edin."
        )

    return found_cafes


if __name__ == "__main__":
    sehir = input("Hangi şehir için arama yapılsın? (Örn: Ankara): ")
    # Aramayı 'cafe' olarak yapıyoruz, şehri kullanıcıdan alıyoruz.
    google_maps_finder("cafe", sehir)
