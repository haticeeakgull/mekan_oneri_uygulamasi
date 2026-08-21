import os
import requests
import time
import random  # Karıştırma işlemi için eklendi
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "cafe_photos"


def get_precise_photo_url(cafe_name, lat, lng, ilce_adi):
    """
    Find-Place mantığıyla daha az veri çekerek fotoğraf referansı yakalar.
    """
    search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    input_text = f"{cafe_name} {ilce_adi} İstanbul"

    # Koordinatları temizle ve float'a çevirerek formatla
    try:
        clean_lat = float(str(lat).strip())
        clean_lng = float(str(lng).strip())
    except Exception as e:
        print(f"⚠️ Koordinat dönüştürme hatası ({cafe_name}): {e}")
        return None

    params = {
        "input": input_text,
        "inputtype": "textquery",
        "locationbias": f"circle:100@{clean_lat},{clean_lng}",
        "fields": "photos,place_id",
        "key": GOOGLE_API_KEY,
    }

    try:
        res = requests.get(search_url, params=params, timeout=10).json()

        # Google'ın döndüğü durum kodunu kontrol edelim
        status = res.get("status")
        if status != "OK":
            print(
                f"⚠️ Google API Durumu ({cafe_name}): {status} | Mesaj: {res.get('error_message', 'Açıklama yok')}"
            )
            return None

        candidates = res.get("candidates", [])
        if candidates and candidates[0].get("photos"):
            photo_ref = candidates[0]["photos"][0]["photo_reference"]
            return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1000&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
        else:
            print(f"🔍 {cafe_name} için mekan bulundu ama fotoğrafı yok.")

    except Exception as e:
        print(f"⚠️ Kod içi hata ({cafe_name}): {e}")

    return None


def start_safe_photo_marathon(limit=15, il_adi="İstanbul"):
    # 1. Zaten fotoğrafı olanların ID listesini alıyoruz
    existing_photos = supabase.table("cafe_fotograflar").select("cafe_id").execute()
    existing_ids = {str(item["cafe_id"]) for item in existing_photos.data}

    # 2. Belirtilen ildeki tüm kafeleri çek
    cafes = (
        supabase.table("ilce_isimli_kafeler")
        .select("id, kafe_adi, latitude, longitude, ilce_adi")
        .eq("il_adi", il_adi)
        .execute()
    )

    # 3. Henüz fotoğrafı olmayanları ayıkla
    pending_cafes = [c for c in cafes.data if str(c["id"]) not in existing_ids]

    # --- KRİTİK DOKUNUŞ: Listeyi Rastgele Karıştır ---
    random.shuffle(pending_cafes)
    # -----------------------------------------------

    print(
        f"🚀 {il_adi} - Toplam {len(cafes.data)} kafe var. {len(pending_cafes)} tanesi eksik. Limit: {limit}"
    )
    success_count = 0

    for cafe in pending_cafes:
        if success_count >= limit:
            break

        c_id = cafe["id"]
        c_name = cafe["kafe_adi"]
        c_lat = cafe["latitude"]
        c_lng = cafe["longitude"]
        c_ilce = cafe["ilce_adi"]

        print(f"🔄 İşleniyor: {c_name} ({c_ilce})")

        # Fotoğraf URL al
        photo_url = get_precise_photo_url(c_name, c_lat, c_lng, c_ilce)

        if photo_url:
            try:
                img_res = requests.get(photo_url, timeout=15)

                if img_res.status_code == 200 and len(img_res.content) > 20000:
                    path = f"{c_id}/main.jpg"

                    # Supabase Storage Yükleme
                    supabase.storage.from_(BUCKET_NAME).upload(
                        path=path,
                        file=img_res.content,
                        file_options={"content-type": "image/jpeg", "x-upsert": "true"},
                    )

                    final_public_url = supabase.storage.from_(
                        BUCKET_NAME
                    ).get_public_url(path)

                    # DB'ye yaz
                    supabase.table("cafe_fotograflar").insert(
                        {"cafe_id": c_id, "foto_url": final_public_url}
                    ).execute()

                    print(f"✅ Başarılı: {c_name}")
                    success_count += 1
                    time.sleep(2.0)  # Rate limit için bekleme süresi artırıldı
                else:
                    print(f"❌ {c_name} için uygun görsel yok veya dosya çok küçük.")
            except Exception as e:
                print(f"⚠️ Hata ({c_name}): {e}")
        else:
            print(f"🔍 {c_name} bulunamadı.")


if __name__ == "__main__":
    # İl seçimi yap
    print("\n=== FOTOĞRAF YÜKLEME ===")
    print("Hangi il için fotoğraf yüklemek istiyorsun?")
    print("Örnek: İstanbul, Ankara, İzmir, Antalya, Bursa")

    il_choice = input("\nİl adı: ").strip()

    if not il_choice:
        il_choice = "İstanbul"  # Varsayılan

    # Maliyet uyarısı
    print("\n" + "=" * 60)
    print("💰 MALİYET UYARISI")
    print("=" * 60)
    print(f"Günlük limit: 200 kafe (önerilen)")
    print(f"Tahmini maliyet: ~$3.40/gün (Find Place API)")
    print(f"Aylık ücretsiz: $200")
    print(f"Ay sonunda: ~$102 (limitin %51'i) ✅")
    print(f"İstanbul için: ~5 gün sürer")
    print("=" * 60)

    onay = input("\nDevam etmek istiyor musun? (e/h): ").strip().lower()

    if onay != "e":
        print("❌ İşlem iptal edildi.")
        exit()

    # Dengeli limit: günde 200 kafe (aylık $102)
    start_safe_photo_marathon(limit=200, il_adi=il_choice)
