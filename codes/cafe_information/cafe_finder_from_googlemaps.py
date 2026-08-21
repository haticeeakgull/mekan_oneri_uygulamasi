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

    # 1. CHROME KULLAN (Brave yerine - daha stabil)
    chrome_options.binary_location = (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    )

    # 2. PROFİL SORUNU YOK - Geçici profil kullan
    # chrome_options.add_argument(f"--user-data-dir={profil_yolu}")  # ← KALDIRILDI
    # chrome_options.add_argument("--profile-directory=Default")  # ← KALDIRILDI

    # 3. OTOMASYON GİZLEME VE DİĞER AYARLAR
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--start-maximized")

    # GPU sorunlarını önle
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

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
        print(f"\n{'='*60}")
        print(f"🔍 {city_name.upper()} İÇİN KAFE TARAMASI BAŞLADI")
        print(f"{'='*60}\n")
        try:
            scrollable_div = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
            )
            print("✅ Sonuç paneli bulundu, scroll işlemi başlıyor...\n")

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

                # Her 5 scroll'da bir ilerleme göster
                if scroll_count % 5 == 0:
                    current_places = len(
                        driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
                    )
                    print(
                        f"📜 Scroll {scroll_count} - Şu ana kadar {current_places} mekan bulundu..."
                    )

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
        print(f"\n{'='*60}")
        print("🧹 Mekan kartları analiz ediliyor ve koordinatlar ayıklanıyor...")
        print(f"{'='*60}\n")
        places = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        print(f"📍 Toplam {len(places)} potansiyel mekan bulundu.")

        processed = 0
        skipped = 0

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
                        processed += 1
                        if processed % 10 == 0:
                            print(f"   ✅ {processed} benzersiz mekan işlendi...")
                    else:
                        skipped += 1
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
                                    processed += 1
                                    if processed % 10 == 0:
                                        print(
                                            f"   ✅ {processed} benzersiz mekan işlendi..."
                                        )
            except:
                skipped += 1
                continue

        print(f"\n📊 İşleme Özeti:")
        print(f"   ✅ Benzersiz mekan: {processed}")
        print(f"   ⏭️  Duplike/hatalı: {skipped}")

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
        
        print(f"\n{'='*60}")
        print("✅ İŞLEM TAMAMLANDI!")
        print(f"{'='*60}")
        print(f"📊 Toplam bulunan benzersiz kafe: {len(found_cafes)}")
        print(f"� Dosya konumu: {filename}")
        print(f"{'='*60}\n")
    else:
        print("\n❌ Hiç kafe bulunamadı.")
        print("💡 Öneriler:")
        print("   - İnternet bağlantınızı kontrol edin")
        print("   - Şehir adını doğru yazdığınızdan emin olun")
        print("   - Google Maps'te manuel olarak arama yapıp sonuç olup olmadığını kontrol edin\n")

    return found_cafes


if __name__ == "__main__":
    sehir = input("Hangi şehir için arama yapılsın? (Örn: Ankara): ")
    # Aramayı 'cafe' olarak yapıyoruz, şehri kullanıcıdan alıyoruz.
    google_maps_finder("cafe", sehir)
