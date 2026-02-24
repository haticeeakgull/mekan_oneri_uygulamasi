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
    current_dir = os.path.dirname(os.path.abspath(__file__))  # codes/supabase
    root_dir = os.path.abspath(os.path.join(current_dir, "../../"))  # ana dizin

    # Gerçek yolu oluştur
    tam_yol = os.path.join(root_dir, json_dosya_yolu)

    if not os.path.exists(tam_yol):
        print(f"Hata: Dosya şu adreste bulunamadı: {tam_yol}")
        return

    with open(tam_yol, "r", encoding="utf-8") as f:
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
    verileri_toplu_yukle("json_files/eksik_mekan_verileri_ankara.json")
