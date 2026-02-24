import json
import os
import torch
from transformers import AutoTokenizer, AutoModel


def yorumlari_vektorlestir(sehir):
    ana_dizin = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    giris_dosyasi = os.path.join(
        ana_dizin,
        "json_files",
        f"eksik_mekan_verileri_{sehir.lower()}.json",
    )
    cikis_dosyasi = os.path.join(
        ana_dizin, "json_files", f"eksik_mekan_verisi_vektorlu_{sehir.lower()}.json"
    )

    if not os.path.exists(giris_dosyasi):
        print("Hata: Temizlenmiş AI dosyası bulunamadı!")
        return

    # Model ve Tokenizer Yükleme
    model_yolu = "./models/bert_turkish/"
    print("Model yükleniyor...")
    tokenizer = AutoTokenizer.from_pretrained(model_yolu)
    model = AutoModel.from_pretrained(model_yolu)

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

        inputs = tokenizer(
            tum_metin,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = model(**inputs)

        vektor = outputs.last_hidden_state[0][0].tolist()

        kafe["vektor"] = vektor
        print(f"✅ {kafe['isim']} vektörleştirildi.")

    # Kaydet
    with open(cikis_dosyasi, "w", encoding="utf-8") as f:
        json.dump(kafeler, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem tamam! Vektörlü veri şuraya kaydedildi: {cikis_dosyasi}")


if __name__ == "__main__":
    yorumlari_vektorlestir("ankara")
