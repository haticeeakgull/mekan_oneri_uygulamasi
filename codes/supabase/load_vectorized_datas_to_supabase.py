import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


with open(
    "json_files/eksik_mekan_verisi_vektorlu_ankara.json", "r", encoding="utf-8"
) as f:
    kafeler = json.load(f)

print(f"{len(kafeler)} mekan yükleniyor...")

for kafe in kafeler:

    if not kafe.get("vektor"):
        continue

    data = {
        "kafe_adi": kafe["isim"],
        "ozellikler": " ".join(kafe["yorumlar"][:3]),
        "embedding": kafe["vektor"],
    }

    try:
        supabase.table("vektor_verili_kafeler").insert(data).execute()
        print(f"✅ {kafe['isim']} yüklendi.")
    except Exception as e:
        print(f"❌ Hata ({kafe['isim']}): {e}")

print("İşlem tamam!")
