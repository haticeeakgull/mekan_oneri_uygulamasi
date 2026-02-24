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
    # 1. Vektörleştirme (Mevcut kodunla aynı)
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

    # 2. Kritik kelimeleri belirle
    kritik_kelimeler = [
        "kitap",
        "sessiz",
        "sakin",
        "kütüphane",
        "alkol",
        "bira",
        "canlı müzik",
        "pub",
        "oyun",
        "tavla",
        "okey",
        "kutu oyunu",
        "ucuz",
        "pahalı",
        "uygun fiyatlı",
        "kahvaltı",
        "kızılay",
        "tunalı",
        "huzurlu",
        "tatlı",
        "nostaljik",
        "butik",
        "geniş",
    ]

    # --- DÜZELTİLEN KISIM BURASI ---
    # Önce değişkeni tanımlıyoruz
    bulunan_anahtarlar = [
        kelime for kelime in kritik_kelimeler if kelime in kullanici_sorgusu.lower()
    ]

    # Sonra bu değişkeni kontrol edip arama_metni'ni oluşturuyoruz
    if bulunan_anahtarlar:
        arama_metni = " ".join(bulunan_anahtarlar)
    else:
        arama_metni = kullanici_sorgusu
    # ------------------------------

    # 3. RPC Çağrısı
    rpc_response = supabase.rpc(
        "kafe_ara_gelismis",
        {
            "query_embedding": sorgu_vektoru,
            "search_query": arama_metni,
            "match_threshold": 0.2,
            "match_count": 5,
        },
    ).execute()

    return rpc_response.data


def kafe_tavsiye_et(kullanici_sorgusu):

    inputs = tokenizer(
        kullanici_sorgusu,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    with torch.no_grad():
        outputs = model(**inputs)

    # Senin yöntemin olan [0][0] yani CLS token'ı alıyoruz
    sorgu_vektoru = outputs.last_hidden_state[0][0].tolist()

    # Supabase'deki 'kafe_ara' fonksiyonunu çağır
    rpc_response = supabase.rpc(
        "kafe_ara",
        {
            "query_embedding": sorgu_vektoru,
            "match_threshold": 0.5,  # Benzerlik oranı %50'den büyük olanlar
            "match_count": 5,  # En yakın 5 kafe
        },
    ).execute()

    return rpc_response.data


# TEST EDELİM
arama = "lise öğrencileri için sesli çalışma mekanı"
sonuclar = akilli_kafe_ara(arama)

for s in sonuclar:
    print(f"Kafe: {s['kafe_adi']} - Benzerlik: %{s['similarity']*100:.2f}")
