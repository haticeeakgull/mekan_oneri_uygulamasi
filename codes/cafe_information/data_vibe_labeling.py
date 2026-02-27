import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# 1. Supabase Bağlantısı
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Vibe ve Özellik Sözlüğü
vibe_sozlugu = {
    "salaş": ["salaş", "samimi", "lüks değil", "mütevazı", "eski usul"],
    "vintage": ["vintage", "retro", "nostalji", "plak", "antika", "eskicil"],
    "butik": ["butik", "küçük", "şirin", "gizli köşe", "özgün", "az masa"],
    "şık-premium": ["şık", "premium", "lüks", "zarif", "kaliteli sunum", "dekorasyon"],
    "ders-çalışmalık": [
        "ders",
        "çalışma",
        "laptop",
        "priz",
        "kütüphane",
        "sessiz",
        "odaklanma",
        "bilgisayar",
    ],
    "sosyal-canlı": [
        "canlı",
        "kalabalık",
        "hareketli",
        "popüler",
        "gürültülü",
        "müzik",
    ],
    "kafa-dinlemelik": [
        "kafa dinleme",
        "huzur",
        "tenha",
        "dingin",
        "sakin",
        "dinlendirici",
    ],
    "kafa-dağıtmalık": [
        "kafa dağıtma",
        "eğlence",
        "oyun",
        "tavla",
        "okey",
        "langırt",
        "muhabbet",
    ],
}


def etiketleri_analiz_et(yorumlar):
    mekan_vibes = []

    tum_metin = " ".join(yorumlar).lower()

    # Vibe Analizi
    for vibe, kelimeler in vibe_sozlugu.items():
        # Eğer bu vibe grubundan en az 2 kelime geçiyorsa etiketi ekle
        eslesme_sayisi = sum(1 for kelime in kelimeler if kelime in tum_metin)
        if eslesme_sayisi >= 2:
            mekan_vibes.append(vibe)

    return mekan_vibes


def verileri_zenginlestir_ve_guncelle(sehir):
    # JSON Dosyasını Oku
    dosya_yolu = f"json_files/vektorlu_mekan_verisi_owner_yorumlarindan_temizlenmis_{sehir.lower()}.json"

    if not os.path.exists(dosya_yolu):
        print("Dosya bulunamadı!")
        return

    with open(dosya_yolu, "r", encoding="utf-8") as f:
        kafeler = json.load(f)

    print(f"{len(kafeler)} mekan analiz ediliyor ve Supabase'e gönderiliyor...")

    for kafe in kafeler:
        vibes = etiketleri_analiz_et(kafe.get("yorumlar"))

        # Supabase Güncelleme
        try:
            supabase.table("vektor_verili_adresli_kafeler").update(
                {
                    "vibe_etiketleri": vibes,
                }
            ).eq("kafe_adi", kafe["isim"]).execute()

            print(f"✅ {kafe['isim']} güncellendi. Vibes: {vibes}")
        except Exception as e:
            print(f"❌ {kafe['isim']} güncellenirken hata: {e}")


if __name__ == "__main__":
    verileri_zenginlestir_ve_guncelle("ankara")
