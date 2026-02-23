import json
import os
import torch
from transformers import AutoTokenizer, AutoModel


def yorumlari_vektorlestir(sehir):
    ana_dizin = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    giris_dosyasi = os.path.join(
        ana_dizin,
        "json_files",
        f"mekan_verisi_owner_yorumlarindan_temizlenmis_{sehir.lower()}.json",
    )
    cikis_dosyasi = os.path.join(
        ana_dizin, "json_files", f"final_mekan_verisi_vektorlu_{sehir.lower()}.json"
    )

    if not os.path.exists(giris_dosyasi):
        print("Hata: Temizlenmiş AI dosyası bulunamadı!")
        return

    # Model ve Tokenizer Yükleme
    model_yolu = "./models/bert_turkish/"
    print("Model yükleniyor...")
    tokenizer = AutoTokenizer.from_pretrained(model_yolu)
    model = AutoModel.from_pretrained(model_yolu)

    # Modeli değerlendirme moduna al (Gradyan hesaplamasın, daha hızlı çalışır)
    model.eval()

    with open(giris_dosyasi, "r", encoding="utf-8") as f:
        kafeler = json.load(f)

    print(f"{len(kafeler)} mekan için vektörleştirme başlıyor...")

    for kafe in kafeler:
        # Eğer yorum yoksa boş vektör ata
        if not kafe["yorumlar"]:
            kafe["vektor"] = []
            continue

        # Tüm yorumları birleştir
        tum_metin = " ".join(kafe["yorumlar"])

        # 1. ADIM: Metni Tokenize Et (BERT'in anlayacağı sayılara çevir)
        # padding ve truncation önemli: metin çok uzunsa keser, kısaysa tamamlar
        inputs = tokenizer(
            tum_metin,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        # 2. ADIM: Modele Besle (Vektörleri Üret)
        with torch.no_grad():  # Hafıza kullanımı için hesaplamayı kapatıyoruz
            outputs = model(**inputs)

        # 3. ADIM: Pooling (Tüm metni temsil eden vektörü al - CLS Token)
        # Genelde [CLS] token'ı (ilk token) tüm metnin anlamını taşır
        vektor = outputs.last_hidden_state[0][0].tolist()

        kafe["vektor"] = vektor
        print(f"✅ {kafe['isim']} vektörleştirildi.")

    # Kaydet
    with open(cikis_dosyasi, "w", encoding="utf-8") as f:
        json.dump(kafeler, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem tamam! Vektörlü veri şuraya kaydedildi: {cikis_dosyasi}")


if __name__ == "__main__":
    yorumlari_vektorlestir("ankara")
