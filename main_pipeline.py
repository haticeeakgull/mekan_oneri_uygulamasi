# import os
# import json
# import time
# import torch
# import math
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from geopy.geocoders import Nominatim
# from supabase import create_client
# from dotenv import load_dotenv
# from sentence_transformers import SentenceTransformer

# # --- AYARLAR ---
# load_dotenv()
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# # ✅ SBERT MODEL (384)
# model = SentenceTransformer(
#     "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# )

# BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
# BRAVE_PROFILE = r"C:\Users\hakgl\AppData\Local\BraveSoftware\Brave-Browser\BotProfile"
# JSON_BACKUP_FILE = "kocaeli_kafeleri_yedek.json"
# DUPLICATE_CHECK_RADIUS_KM = 1.0  # Yarıçap: 1 km

# vibe_sozlugu = {
#     "salaş": ["salaş", "samimi", "mütevazı", "eski usul"],
#     "ders-çalışmalık": ["ders", "çalışma", "laptop", "priz", "sessiz", "odaklanma"],
#     "sosyal-canlı": ["canlı", "kalabalık", "müzik", "hareketli", "popüler"],
#     "kafa-dinlemelik": ["huzur", "dingin", "sakin", "tenha", "dinlendirici"],
# }


# # ------------------------------
# # ✅ SBERT VECTOR (EKLENEN KISIM)
# # ------------------------------
# def get_vector(reviews):
#     if not reviews:
#         return []

#     full_text = " ".join(reviews)

#     embedding = model.encode(full_text, normalize_embeddings=True)

#     return embedding.tolist()


# # ------------------------------
# # Haversine formülü ile iki koordinat arasındaki mesafeyi hesapla (km)
# def haversine_distance(lat1, lon1, lat2, lon2):
#     R = 6371  # Dünya yarıçapı (km)

#     lat1_rad = math.radians(lat1)
#     lat2_rad = math.radians(lat2)
#     delta_lat = math.radians(lat2 - lat1)
#     delta_lon = math.radians(lon2 - lon1)

#     a = (
#         math.sin(delta_lat / 2) ** 2
#         + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
#     )
#     c = 2 * math.asin(math.sqrt(a))
#     distance = R * c

#     return distance


# # DB CHECK - Çift kafe kontrolü (isim + yarıçap)
# # ------------------------------
# def check_if_exists(kafe_adi, lat=None, lon=None):
#     try:
#         # Tam eşleşmeyi kontrol et
#         if lat is not None and lon is not None:
#             res = (
#                 supabase.table("ilce_isimli_kafeler")
#                 .select("id, latitude, longitude")
#                 .eq("kafe_adi", kafe_adi)
#                 .execute()
#             )

#             # Aynı isimli kafeleri kontrol et
#             for cafe in res.data:
#                 db_lat = float(cafe["latitude"])
#                 db_lon = float(cafe["longitude"])

#                 # Mesafeyi hesapla
#                 distance = haversine_distance(lat, lon, db_lat, db_lon)

#                 # Eğer yarıçap içindeyse dublika
#                 if distance <= DUPLICATE_CHECK_RADIUS_KM:
#                     return True, f"({distance:.2f}km uzakta) aynı isimli kafe var"

#             # Yarıçap dışında - yeni şube ise ekle
#             return False, "yeni şube"

#         return False, "yeni kafe"
#     except Exception as e:
#         print(f"Kontrol hatası: {e}")
#         return False, "hata"


# # ------------------------------
# # JSON BACKUP
# # ------------------------------
# def save_to_json_backup(data):
#     file_data = []
#     if os.path.exists(JSON_BACKUP_FILE):
#         with open(JSON_BACKUP_FILE, "r", encoding="utf-8") as f:
#             try:
#                 file_data = json.load(f)
#             except:
#                 file_data = []

#     file_data.append(data)

#     with open(JSON_BACKUP_FILE, "w", encoding="utf-8") as f:
#         json.dump(file_data, f, ensure_ascii=False, indent=4)


# def scrape_reviews(place_name, lat, lon):

#     chrome_options = Options()
#     chrome_options.binary_location = BRAVE_PATH

#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--remote-debugging-port=9222")  # Port kilitlenmelerini önler
#     chrome_options.add_argument("--disable-gpu")
#     #chrome_options.add_argument(f"--user-data-dir={BRAVE_PROFILE}")
#     chrome_options.add_argument("--profile-directory=Default")

#     chrome_options.add_argument("--lang=tr-TR")
#     chrome_options.add_experimental_option(
#         "prefs", {"intl.accept_languages": "tr,tr-TR"}
#     )

#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

#     driver = webdriver.Chrome(options=chrome_options)
#     wait = WebDriverWait(driver, 15)

#     reviews = []

#     try:
#         url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
#         driver.get(url)
#         time.sleep(5)

#         try:
#             btn = wait.until(
#                 EC.element_to_be_clickable(
#                     (
#                         By.XPATH,
#                         '//button[contains(@aria-label, "Yorumlar") or contains(@aria-label, "Reviews")]',
#                     )
#                 )
#             )
#             btn.click()
#             time.sleep(3)
#         except:
#             print("Yorum butonu bulunamadı")
#             return []

#         scrollable_div = None
#         selectors = ["div.m6QErb.DxyBCb", "div.m6QErb"]

#         for selector in selectors:
#             try:
#                 scrollable_div = driver.find_element(By.CSS_SELECTOR, selector)
#                 if scrollable_div:
#                     break
#             except:
#                 continue

#         for _ in range(10):
#             if scrollable_div:
#                 driver.execute_script(
#                     "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
#                 )
#             else:
#                 driver.execute_script("window.scrollBy(0, 1000);")

#             time.sleep(1.5)

#         spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
#         reviews = [s.text.strip() for s in spans if s.text.strip()]

#     except Exception as e:
#         print("SCRAPER HATA:", e)

#     finally:
#         driver.quit()

#     return list(set(reviews))


# # ------------------------------
# # LOCATION
# # ------------------------------
# def get_location_details(lat, lon):
#     geolocator = Nominatim(user_agent="ugrak_mekan")
#     try:
#         location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
#         addr = location.raw.get("address", {})

#         semt = addr.get("suburb") or addr.get("neighbourhood") or "Bilinmiyor"
#         ilce = addr.get("city") or addr.get("town") or "Bilinmiyor"

#         return semt, ilce
#     except:
#         return "Bilinmiyor", "Bilinmiyor"


# # ------------------------------
# # VIBES
# # ------------------------------
# def get_vibes(reviews):
#     text = " ".join(reviews).lower()
#     active_vibes = []

#     for vibe, keywords in vibe_sozlugu.items():
#         if sum(1 for k in keywords if k in text) >= 2:
#             active_vibes.append(vibe)

#     return active_vibes


# # ------------------------------
# # DB UPLOAD
# # ------------------------------
# def upload_to_supabase(final_data):

#     try:
#         res_cafe = (
#             supabase.table("ilce_isimli_kafeler")
#             .insert(
#                 {
#                     "kafe_adi": final_data["isim"],
#                     "latitude": final_data["lat"],
#                     "longitude": final_data["lon"],
#                     "ilce_adi": final_data["ilce_adi"],
#                     "semt_adi": final_data["semt_adi"],
#                     "embedding_v2": final_data["vektor"],
#                     "vibe_etiketleri": final_data["vibe_etiketleri"],
#                     "ozellikler": final_data["yorumlar"],
#                 }
#             )
#             .execute()
#         )

#         if res_cafe.data:
#             new_id = res_cafe.data[0]["id"]

#             for yorum in final_data["yorumlar"]:
#                 supabase.table("cafe_yorumlar").insert(
#                     {
#                         "cafe_id": new_id,
#                         "yorum_metni": yorum,
#                         "puan": 5,
#                     }
#                 ).execute()

#             return True

#     except Exception as e:
#         print("DB HATA:", e)
#         return False


# # ------------------------------
# # JSON DOSYASIDAN OKUMA
# # ------------------------------
# def load_cafes_from_json(filename):
#     try:
#         with open(filename, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         return data if isinstance(data, list) else [data]
#     except FileNotFoundError:
#         print(f"Dosya bulunamadı: {filename}")
#         return []
#     except json.JSONDecodeError:
#         print(f"JSON dosyası hatalı: {filename}")
#         return []


# # ------------------------------
# # TEK KAFE İŞLEME
# # ------------------------------
# def process_single_cafe(name, lat, lon):
#     exists, reason = check_if_exists(name, lat, lon)

#     if exists:
#         if reason == "tam eşleşme":
#             print(f"❌ {name} (aynı koordinat) zaten veritabanında var")
#         else:
#             print(f"❌ {name} zaten veritabanında var ({reason})")
#         return False

#     print(f"📍 {name} için yorumlar çekiliyor...")
#     reviews = scrape_reviews(name, lat, lon)

#     if not reviews:
#         print(f"❌ {name} için yorum bulunamadı")
#         return False

#     semt, ilce = get_location_details(lat, lon)

#     data = {
#         "isim": name,
#         "lat": lat,
#         "lon": lon,
#         "yorumlar": reviews,
#         "vektor": get_vector(reviews),
#         "semt_adi": semt,
#         "ilce_adi": ilce,
#         "vibe_etiketleri": get_vibes(reviews),
#     }

#     save_to_json_backup(data)

#     if upload_to_supabase(data):
#         print(f"✅ {name} başarıyla kaydedildi")
#         return True
#     else:
#         print(f"❌ {name} veritabanına kaydedilemedi")
#         return False


# # ------------------------------
# # MAIN
# # ------------------------------
# def run_pipeline():
#     print("\n=== KAFE VERİSİ ÇEKİCİ ===")
#     choice = (
#         input("Manuel giriş (m) mi yoksa JSON dosyasından okuma (j) mi? (m/j): ")
#         .lower()
#         .strip()
#     )

#     if choice == "m":
#         # Manuel giriş
#         name = input("Kafe adı: ")
#         lat = float(input("Latitude: "))
#         lon = float(input("Longitude: "))
#         process_single_cafe(name, lat, lon)

#     elif choice == "j":
#         # JSON dosyasından okuma
#         json_file = input(
#             "JSON dosya adı (örn: istanbul_kafeleri_yedek.json): "
#         ).strip()

#         cafes = load_cafes_from_json(json_file)
#         if not cafes:
#             print("Kafe verisi yüklenemedi")
#             return

#         print(f"\n📂 {len(cafes)} kafe bulundu\n")

#         success_count = 0
#         fail_count = 0

#         for i, cafe in enumerate(cafes, 1):
#             print(f"\n[{i}/{len(cafes)}]", end=" ")
#             if isinstance(cafe, dict):
#                 # İki format da destekle: (isim, lat, lon) veya (kafe_adi, latitude, longitude)
#                 cafe_name = cafe.get("isim") or cafe.get("kafe_adi")
#                 cafe_lat = cafe.get("lat") or cafe.get("latitude")
#                 cafe_lon = cafe.get("lon") or cafe.get("longitude")

#                 if cafe_name and cafe_lat is not None and cafe_lon is not None:
#                     try:
#                         cafe_lat = float(cafe_lat)
#                         cafe_lon = float(cafe_lon)
#                         if process_single_cafe(cafe_name, cafe_lat, cafe_lon):
#                             success_count += 1
#                         else:
#                             fail_count += 1
#                         time.sleep(2)
#                     except (ValueError, TypeError) as e:
#                         print(f"❌ {cafe_name}: Geçersiz lat/lon değeri - {e}")
#                         fail_count += 1
#                 else:
#                     missing = []
#                     if not cafe_name:
#                         missing.append("isim/kafe_adi")
#                     if cafe_lat is None:
#                         missing.append("lat/latitude")
#                     if cafe_lon is None:
#                         missing.append("lon/longitude")
#                     print(f"❌ Eksik alan(lar): {', '.join(missing)}")
#                     fail_count += 1
#             else:
#                 print(f"❌ Geçersiz kafe formatı (dict değil)")
#                 fail_count += 1

#         print(f"\n\n{'='*40}")
#         print(f"İşlem tamamlandı!")
#         print(f"✅ Başarılı: {success_count}")
#         print(f"❌ Başarısız: {fail_count}")
#         print(f"{'='*40}")

#     else:
#         print("❌ Geçersiz seçim. 'm' veya 'j' yazınız")


# # ------------------------------
# if __name__ == "__main__":
#     run_pipeline()
import os
import json
import time
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    SessionNotCreatedException,
    WebDriverException,
    TimeoutException,
)
from geopy.geocoders import Nominatim
from supabase import create_client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- AYARLAR ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ SBERT MODEL (384)
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

BRAVE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ⚠️ Profil kullanmıyoruz - Chrome her seferinde temiz başlayacak
# Her çalıştırmada Google'a manuel giriş yapmanız gerekecek
# Alternatif: Cookies kaydedebiliriz (aşağıda eklenecek)

# ChromeDriver'ı Chrome sürümüne göre elle indirip buraya yolunu yaz.
# Boş bırakırsan Selenium Manager otomatik bulmaya çalışır.
CHROMEDRIVER_PATH = ""  # Selenium Manager otomatik yönetsin

JSON_BACKUP_FILE = "mersin_kafeleri_yedek.json"
DUPLICATE_CHECK_RADIUS_KM = 1.0  # Yarıçap: 1 km

# Driver crash durumunda kaç kez yeniden başlatma denemesi yapılsın
MAX_DRIVER_RETRIES = 3

vibe_sozlugu = {
    "salaş": ["salaş", "samimi", "mütevazı", "eski usul"],
    "ders-çalışmalık": ["ders", "çalışma", "laptop", "priz", "sessiz", "odaklanma"],
    "sosyal-canlı": ["canlı", "kalabalık", "müzik", "hareketli", "popüler"],
    "kafa-dinlemelik": ["huzur", "dingin", "sakin", "tenha", "dinlendirici"],
}


# ------------------------------
# ✅ SBERT VECTOR
# ------------------------------
def get_vector(reviews):
    if not reviews:
        return []
    full_text = " ".join(reviews)
    embedding = model.encode(full_text, normalize_embeddings=True)
    return embedding.tolist()


# ------------------------------
# Haversine formülü
# ------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


# ------------------------------
# DB CHECK - Çift kafe kontrolü
# ------------------------------
def check_if_exists(kafe_adi, lat=None, lon=None):
    try:
        if lat is not None and lon is not None:
            res = (
                supabase.table("ilce_isimli_kafeler")
                .select("id, latitude, longitude")
                .eq("kafe_adi", kafe_adi)
                .execute()
            )

            for cafe in res.data:
                db_lat = float(cafe["latitude"])
                db_lon = float(cafe["longitude"])
                distance = haversine_distance(lat, lon, db_lat, db_lon)

                if distance <= DUPLICATE_CHECK_RADIUS_KM:
                    return True, f"({distance:.2f}km uzakta) aynı isimli kafe var"

            return False, "yeni şube"

        return False, "yeni kafe"
    except Exception as e:
        print(f"Kontrol hatası: {e}")
        return False, "hata"


# ------------------------------
# JSON BACKUP
# ------------------------------
def save_to_json_backup(data):
    file_data = []
    if os.path.exists(JSON_BACKUP_FILE):
        with open(JSON_BACKUP_FILE, "r", encoding="utf-8") as f:
            try:
                file_data = json.load(f)
            except Exception:
                file_data = []

    file_data.append(data)

    with open(JSON_BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(file_data, f, ensure_ascii=False, indent=4)


# ------------------------------
# ✅ DRIVER OLUŞTURMA (yeniden kullanılabilir, ayrı fonksiyon)
# ------------------------------
def build_driver():
    chrome_options = Options()
    chrome_options.binary_location = BRAVE_PATH

    # ❌ Profil KULLANILMIYOR - Chrome profil sorunu nedeniyle
    # Her çalıştırmada manuel giriş gerekecek

    print(f"📂 Chrome temiz profille başlatılıyor")
    print(f"🔑 Her çalıştırmada Google'a giriş yapmanız gerekecek")

    # HEADLESS MODE KAPALI - Tarayıcıyı görebilirsin
    # chrome_options.add_argument("--headless=new")  # ← Kapalı

    # GPU sorunlarını tamamen devre dışı bırak
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")

    chrome_options.add_argument("--lang=tr-TR")
    chrome_options.add_experimental_option(
        "prefs", {"intl.accept_languages": "tr,tr-TR"}
    )

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Selenium Manager otomatik driver yönetimi kullansın
    print("⏳ Chrome başlatılıyor...")
    driver = webdriver.Chrome(options=chrome_options)

    # Pencereyi maksimize et (tam ekran)
    driver.maximize_window()
    print("✅ Chrome başlatıldı")

    # Google Maps'i aç (oturum açmak için)
    try:
        driver.get("https://www.google.com/maps")
        print("📍 Google Maps açıldı - Oturum açabilirsiniz")
        time.sleep(2)  # Sayfanın yüklenmesini bekle
    except Exception as e:
        print(f"⚠️ Google Maps açılamadı: {e}")

    return driver


def safe_quit(driver):
    """Driver'ı güvenli şekilde kapatır, hata olsa bile pipeline'ı durdurmaz."""
    if driver is None:
        return
    try:
        driver.quit()
    except Exception as e:
        print(f"Driver kapatma uyarısı (görmezden gelinebilir): {e}")


# ------------------------------
# ✅ SCRAPE REVIEWS (artık dışarıdan driver alıyor, kendi driver'ını açıp kapatmıyor)
# ------------------------------
def scrape_reviews(driver, place_name, lat, lon):
    wait = WebDriverWait(driver, 20)  # 15'ten 20'ye çıkardık
    reviews = []

    try:
        url = f"https://www.google.com/maps/search/{place_name}/@{lat},{lon},17z?hl=tr"
        driver.get(url)
        print(f"   🌐 Sayfa yüklendi: {place_name}")
        time.sleep(5)

        # ✅ YORUM BUTONUNU BULMA - Birden fazla yöntem dene
        btn = None

        # Yöntem 1: Aria-label ile (Türkçe + İngilizce)
        try:
            print("   🔍 Yöntem 1: Aria-label ile aranıyor...")
            btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//button[contains(@aria-label, "Yorumlar") or contains(@aria-label, "Reviews") or contains(@aria-label, "yorum") or contains(@aria-label, "review")]',
                    )
                )
            )
            print("   ✅ Yorum butonu bulundu (Aria-label)")
        except TimeoutException:
            print("   ⚠️ Yöntem 1 başarısız")

        # Yöntem 2: Tab içinde "Yorumlar" yazısı ile
        if not btn:
            try:
                print("   🔍 Yöntem 2: Tab metni ile aranıyor...")
                btn = driver.find_element(
                    By.XPATH,
                    '//button[contains(@class, "hh2c6") and contains(., "Yorumlar")]',
                )
                if btn:
                    print("   ✅ Yorum butonu bulundu (Tab metni)")
            except Exception:
                print("   ⚠️ Yöntem 2 başarısız")

        # Yöntem 3: Herhangi bir buton içinde "Yorumlar" geçiyorsa
        if not btn:
            try:
                print("   🔍 Yöntem 3: Genel button aranıyor...")
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for b in buttons:
                    if "yorumlar" in b.text.lower() or "reviews" in b.text.lower():
                        btn = b
                        print(f"   ✅ Yorum butonu bulundu (Button text: '{b.text}')")
                        break
            except Exception:
                print("   ⚠️ Yöntem 3 başarısız")

        # Yöntem 4: Data-value ile (Google Maps tab sistemi)
        if not btn:
            try:
                print("   🔍 Yöntem 4: Data-value ile aranıyor...")
                btn = driver.find_element(By.XPATH, '//button[@data-value="Yorumlar"]')
                if btn:
                    print("   ✅ Yorum butonu bulundu (Data-value)")
            except Exception:
                print("   ⚠️ Yöntem 4 başarısız")

        # Hiçbir yöntem çalışmadıysa
        if not btn:
            print("   ❌ Yorum butonu bulunamadı (tüm yöntemler denendi)")
            print(f"   📸 Sayfa ekran görüntüsü: {place_name}_screenshot.png")
            driver.save_screenshot(f"{place_name.replace(' ', '_')}_screenshot.png")
            return []

        # Butonu tıkla
        try:
            btn.click()
            print("   ✅ Yorum butonuna tıklandı")
        except Exception as e:
            print(f"   ⚠️ Tıklama başarısız, JavaScript ile deneniyor: {e}")
            driver.execute_script("arguments[0].click();", btn)
            print("   ✅ JavaScript ile tıklandı")

        time.sleep(3)

        scrollable_div = None
        selectors = ["div.m6QErb.DxyBCb", "div.m6QErb", "div.dS8AEf"]

        for selector in selectors:
            try:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, selector)
                if scrollable_div:
                    print(f"   ✅ Scrollable div bulundu: {selector}")
                    break
            except Exception:
                continue

        for i in range(10):
            if scrollable_div:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
                )
            else:
                driver.execute_script("window.scrollBy(0, 1000);")
            if i % 3 == 0:
                print(f"   📜 Scroll {i+1}/10...")
            time.sleep(1.5)

        spans = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        reviews = [s.text.strip() for s in spans if s.text.strip()]
        print(f"   ✅ {len(reviews)} yorum toplandı")

    except WebDriverException as e:
        print("   ❌ SCRAPER - DRIVER HATASI:", e)
        raise
    except Exception as e:
        print(f"   ❌ SCRAPER HATA: {e}")

    return list(set(reviews))


# ------------------------------
# LOCATION
# ------------------------------
def get_location_details(lat, lon):
    geolocator = Nominatim(user_agent="ugrak_mekan")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10, language="tr")
        addr = location.raw.get("address", {})

        # İl (province/state) - Nominatim'de genellikle 'state' veya 'province' alanında
        il = (
            addr.get("province")
            or addr.get("state")
            or addr.get("region")
            or "Bilinmiyor"
        )

        # İlçe (district/city/town)
        ilce = (
            addr.get("city")
            or addr.get("town")
            or addr.get("county")
            or addr.get("municipality")
            or "Bilinmiyor"
        )

        # Semt (neighbourhood/suburb)
        semt = (
            addr.get("suburb")
            or addr.get("neighbourhood")
            or addr.get("district")
            or "Bilinmiyor"
        )

        print(f"   📍 Konum: {il} / {ilce} / {semt}")
        return il, semt, ilce

    except Exception as e:
        print(f"   ⚠️  Konum bilgisi alınamadı: {e}")
        return "Bilinmiyor", "Bilinmiyor", "Bilinmiyor"


# ------------------------------
# VIBES
# ------------------------------
def get_vibes(reviews):
    text = " ".join(reviews).lower()
    active_vibes = []

    for vibe, keywords in vibe_sozlugu.items():
        if sum(1 for k in keywords if k in text) >= 2:
            active_vibes.append(vibe)

    return active_vibes


# ------------------------------
# DB UPLOAD
# ------------------------------
def upload_to_supabase(final_data):
    try:
        res_cafe = (
            supabase.table("ilce_isimli_kafeler")
            .insert(
                {
                    "kafe_adi": final_data["isim"],
                    "latitude": final_data["lat"],
                    "longitude": final_data["lon"],
                    "il_adi": final_data["il_adi"],
                    "ilce_adi": final_data["ilce_adi"],
                    "semt_adi": final_data["semt_adi"],
                    "embedding_v2": final_data["vektor"],
                    "vibe_etiketleri": final_data["vibe_etiketleri"],
                    "ozellikler": final_data["yorumlar"],
                }
            )
            .execute()
        )

        if res_cafe.data:
            new_id = res_cafe.data[0]["id"]

            for yorum in final_data["yorumlar"]:
                supabase.table("cafe_yorumlar").insert(
                    {
                        "cafe_id": new_id,
                        "yorum_metni": yorum,
                        "puan": 5,
                    }
                ).execute()

            return True

    except Exception as e:
        print("DB HATA:", e)
        return False


# ------------------------------
# JSON DOSYASINDAN OKUMA
# ------------------------------
def load_cafes_from_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except FileNotFoundError:
        print(f"Dosya bulunamadı: {filename}")
        return []
    except json.JSONDecodeError:
        print(f"JSON dosyası hatalı: {filename}")
        return []


# ------------------------------
# ✅ TEK KAFE İŞLEME (artık driver parametresi alıyor)
# ------------------------------
def process_single_cafe(driver, name, lat, lon):
    exists, reason = check_if_exists(name, lat, lon)

    if exists:
        print(f"⏭️  {name} zaten veritabanında var ({reason})")
        return False

    print(f"\n{'='*60}")
    print(f"📍 İşleniyor: {name}")
    print(f"{'='*60}")
    reviews = scrape_reviews(driver, name, lat, lon)

    if not reviews:
        print(f"❌ {name} için yorum bulunamadı\n")
        return False

    print(f"   🌍 Konum bilgileri alınıyor...")
    il, semt, ilce = get_location_details(lat, lon)

    print(f"   🧠 Yorumlar vektörleştiriliyor...")
    data = {
        "isim": name,
        "lat": lat,
        "lon": lon,
        "yorumlar": reviews,
        "vektor": get_vector(reviews),
        "il_adi": il,
        "semt_adi": semt,
        "ilce_adi": ilce,
        "vibe_etiketleri": get_vibes(reviews),
    }

    print(
        f"   🏷️  Vibe etiketleri: {', '.join(data['vibe_etiketleri']) if data['vibe_etiketleri'] else 'Yok'}"
    )

    save_to_json_backup(data)
    print(f"   💾 JSON yedeği kaydedildi")

    if upload_to_supabase(data):
        print(f"✅ {name} başarıyla veritabanına kaydedildi!\n")
        return True
    else:
        print(f"❌ {name} veritabanına kaydedilemedi\n")
        return False


# ------------------------------
# MAIN
# ------------------------------
def run_pipeline():
    print("\n=== KAFE VERİSİ ÇEKİCİ ===")
    choice = (
        input("Manuel giriş (m) mi yoksa JSON dosyasından okuma (j) mi? (m/j): ")
        .lower()
        .strip()
    )

    if choice not in ["m", "j"]:
        print("❌ Geçersiz seçim. 'm' veya 'j' yazınız")
        return

    # ✅ Driver sadece geçerli seçimden SONRA başlatılıyor
    driver = None
    try:
        print("\n🚀 Chrome başlatılıyor (görünür modda - işlemleri izleyebilirsin)...")
        driver = build_driver()

        # 🔑 Google hesabınızla oturum açması için bekleyin
        print("\n" + "=" * 60)
        print("🔑 GOOGLE OTURUM AÇMA")
        print("=" * 60)
        print("1. Açılan Chrome penceresinde Google Maps'i ziyaret edin")
        print("2. Sağ üstten Google hesabınızla oturum açın")
        print("3. Oturum açtıktan sonra buraya dönün")
        print("=" * 60)

        # Kullanıcının oturum açmasını bekle
        input("\n✅ Oturum açtıktan sonra ENTER tuşuna basın...")
        print("🎯 Devam ediliyor...\n")

    except SessionNotCreatedException as e:
        print("❌ Driver başlatılamadı. Olası nedenler:")
        print(
            "  - Chrome zaten arka planda açık (Görev Yöneticisi'nden chrome.exe'yi kapat)"
        )
        print("  - chromedriver sürümü Chrome sürümüyle uyumsuz")
        print("  - Chrome profili başka bir yerde kullanılıyor")
        print(f"Detay: {e}")
        return
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return

    try:
        if choice == "m":
            name = input("Kafe adı: ")
            lat = float(input("Latitude: "))
            lon = float(input("Longitude: "))
            process_single_cafe(driver, name, lat, lon)

        elif choice == "j":
            json_file = input(
                "JSON dosya adı (örn: istanbul_kafeleri_yedek.json): "
            ).strip()

            cafes = load_cafes_from_json(json_file)
            if not cafes:
                print("Kafe verisi yüklenemedi")
                return

            print(f"\n📂 {len(cafes)} kafe bulundu\n")

            success_count = 0
            fail_count = 0

            for i, cafe in enumerate(cafes, 1):
                print(f"\n[{i}/{len(cafes)}]", end=" ")

                if not isinstance(cafe, dict):
                    print("❌ Geçersiz kafe formatı (dict değil)")
                    fail_count += 1
                    continue

                cafe_name = cafe.get("isim") or cafe.get("kafe_adi")
                cafe_lat = cafe.get("lat") or cafe.get("latitude")
                cafe_lon = cafe.get("lon") or cafe.get("longitude")

                if not (cafe_name and cafe_lat is not None and cafe_lon is not None):
                    missing = []
                    if not cafe_name:
                        missing.append("isim/kafe_adi")
                    if cafe_lat is None:
                        missing.append("lat/latitude")
                    if cafe_lon is None:
                        missing.append("lon/longitude")
                    print(f"❌ Eksik alan(lar): {', '.join(missing)}")
                    fail_count += 1
                    continue

                try:
                    cafe_lat = float(cafe_lat)
                    cafe_lon = float(cafe_lon)
                except (ValueError, TypeError) as e:
                    print(f"❌ {cafe_name}: Geçersiz lat/lon değeri - {e}")
                    fail_count += 1
                    continue

                # ✅ Driver çökerse yeniden başlatmayı dene (MAX_DRIVER_RETRIES kere)
                attempt = 0
                done = False
                while attempt < MAX_DRIVER_RETRIES and not done:
                    try:
                        if process_single_cafe(driver, cafe_name, cafe_lat, cafe_lon):
                            success_count += 1
                        else:
                            fail_count += 1
                        done = True
                    except WebDriverException as e:
                        attempt += 1
                        print(
                            f"⚠️ Driver çöktü, yeniden başlatılıyor (deneme {attempt}/{MAX_DRIVER_RETRIES}): {e}"
                        )
                        safe_quit(driver)
                        time.sleep(3)
                        try:
                            driver = build_driver()
                        except SessionNotCreatedException as e2:
                            print(f"❌ Driver yeniden başlatılamadı: {e2}")
                            fail_count += 1
                            done = True
                            break

                if not done:
                    fail_count += 1
                    print(f"❌ {cafe_name} işlenemedi (maksimum deneme sayısı aşıldı)")

                time.sleep(2)

            print(f"\n\n{'='*40}")
            print("İşlem tamamlandı!")
            print(f"✅ Başarılı: {success_count}")
            print(f"❌ Başarısız: {fail_count}")
            print(f"{'='*40}")

    finally:
        safe_quit(driver)


# ------------------------------
if __name__ == "__main__":
    run_pipeline()
