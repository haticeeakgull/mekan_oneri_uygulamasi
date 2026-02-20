import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. .env dosyasındaki değişkenleri yükle
load_dotenv()

# 2. os.getenv ile bu değişkenlere eriş
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Kontrol: Eğer .env okunamazsa hata verelim
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Hata: .env dosyasından Supabase bilgileri okunamadı!")
    exit()

# 3. Supabase istemcisini başlat
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def verileri_toplu_yukle(json_dosya_yolu):
    with open(json_dosya_yolu, "r", encoding="utf-8") as f:
        kafeler = json.load(f)

    print(f"{len(kafeler)} adet kafe aktarılıyor...")

    # Daha hızlı aktarım için tek tek değil, toplu (Batch) insert yapıyoruz
    # Supabase bir liste gönderdiğinde bunu tek bir SQL komutuyla halleder.
    try:
        # JSON'daki anahtar isimlerini (osm_lat vb.) Supabase sütun isimlerine (lat vb.) eşle
        db_verisi = []
        for k in kafeler:
            db_verisi.append(
                {
                    "name": k["isim"],
                    "lat": k["osm_lat"],
                    "lon": k["osm_lon"],
                    "comments": k["yorumlar"],
                }
            )

        response = supabase.table("kafeler").insert(db_verisi).execute()
        print("✅ Tüm veriler başarıyla Supabase'e aktarıldı!")

    except Exception as e:
        print(f"❌ Aktarım sırasında bir hata oluştu: {e}")


if __name__ == "__main__":
    verileri_toplu_yukle("final_mekan_verisi_temiz.json")
