import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


with open(
    "json_files/vektorlu_mekan_verisi_owner_yorumlarindan_temizlenmis_ankara.json",
    "r",
    encoding="utf-8",
) as f:
    kafeler = json.load(f)

print(f"{len(kafeler)} mekan yükleniyor...")

for kafe in kafeler:

    if not kafe.get("vektor"):
        continue

    data = {
        "kafe_adi": kafe["isim"],
        "ozellikler": " ".join(kafe["yorumlar"][:]),
        "embedding": kafe["vektor"],
        "latitude": kafe["osm_lat"],
        "longitude": kafe["osm_lon"],
    }

    try:
        supabase.table("vektor_verili_adresli_kafeler").insert(data).execute()
        print(f"✅ {kafe['isim']} yüklendi.")
    except Exception as e:
        print(f"❌ Hata ({kafe['isim']}): {e}")

print("İşlem tamam!")
