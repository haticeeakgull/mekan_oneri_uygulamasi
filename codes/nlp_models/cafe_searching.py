import torch
from transformers import AutoTokenizer, AutoModel
from supabase import create_client
import os
import json
from dotenv import load_dotenv

load_dotenv()
model_yolu = "./models/bert_turkish/"
tokenizer = AutoTokenizer.from_pretrained(model_yolu)
model = AutoModel.from_pretrained(model_yolu)
model.eval()

# 2. Supabase Bağlantısı
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def akilli_kafe_ara(kullanici_sorgusu):
    # 1. Vektörleştirme
    inputs = tokenizer(
        kullanici_sorgusu,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    with torch.no_grad():
        outputs = model(**inputs)
    sorgu_vektoru = outputs.last_hidden_state[0][0].tolist()

    # 2. Etiketlerle Uyumlu Kritik Kelimeler
    # SQL'deki vibe_etiketleri sütunundaki kelimeleri buraya eklemek eşleşmeyi artırır
    kritik_kelimeler = [
        "kitap",
        "sessiz",
        "sakin",
        "kütüphane",
        "alkol",
        "bira",
        "pub",
        "salaş",
        "vintage",
        "butik",
        "şık-premium",
        "ders-çalışmalık",
        "sosyal-canlı",
        "kafa-dinlemelik",
        "kafa-dağıtmalık",
        "oyun",
        "tavla",
    ]

    bulunan_anahtarlar = [
        kelime for kelime in kritik_kelimeler if kelime in kullanici_sorgusu.lower()
    ]

    # Eğer özel bir anahtar kelime bulunamadıysa bile boş gitmesin, tüm sorguyu gönderelim
    arama_metni = (
        " ".join(bulunan_anahtarlar) if bulunan_anahtarlar else kullanici_sorgusu
    )

    # 3. YENİ RPC ÇAĞRISI (v4)
    rpc_response = supabase.rpc(
        "kafe_ara_v4",  # Fonksiyon adını güncelledik
        {
            "query_embedding": sorgu_vektoru,
            "search_query": arama_metni,
            "match_threshold": 0.1,  # Daha geniş bir tarama için biraz düşürebilirsin
            "match_count": 5,
        },
    ).execute()

    return rpc_response.data


# TEST EDELİM
arama = ""
sonuclar = akilli_kafe_ara(arama)

if sonuclar:
    for s in sonuclar:

        print(f"Kafe: {s['kafe_adi']} - Benzerlik: %{s['similarity']*100:.2f}")
        print(f"   Etiketler: {s['vibe_etiketleri']}")
else:
    print("Uygun bir mekan bulunamadı.")


# def kafe_tavsiye_et(kullanici_sorgusu):

#     inputs = tokenizer(
#         kullanici_sorgusu,
#         return_tensors="pt",
#         truncation=True,
#         padding=True,
#         max_length=512,
#     )
#     with torch.no_grad():
#         outputs = model(**inputs)

#     # Senin yöntemin olan [0][0] yani CLS token'ı alıyoruz
#     sorgu_vektoru = outputs.last_hidden_state[0][0].tolist()

#     # Supabase'deki 'kafe_ara' fonksiyonunu çağır
#     rpc_response = supabase.rpc(
#         "kafe_ara",
#         {
#             "query_embedding": sorgu_vektoru,
#             "match_threshold": 0.5,  # Benzerlik oranı %50'den büyük olanlar
#             "match_count": 5,  # En yakın 5 kafe
#         },
#     ).execute()

#     return rpc_response.data


# for s in sonuclar:
#     print(f"Kafe: {s['kafe_adi']} - Benzerlik: %{s['similarity']*100:.2f}")
