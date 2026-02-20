import json
import pandas as pd
import os


def eksikleri_tespit_et(sehir):
    json_path = "json_files/final_mekan_verisi.json"
    csv_input_path = f"csv_files/{sehir.lower()}_kafeler.csv"
    csv_output_path = f"csv_files/{sehir.lower()}_kafeler_kalanlar.csv"

    # JSON dosyası henüz hiç yoksa (ilk çalışma), orijinal listeyi direkt kalanlar olarak kaydet
    if not os.path.exists(json_path):
        print(
            f"Bilgi: {json_path} bulunamadı. Tüm liste kalanlar olarak işaretleniyor."
        )
        df_orijinal = pd.read_csv(csv_input_path)
        df_orijinal.to_csv(csv_output_path, index=False, encoding="utf-8-sig")
        return csv_output_path

    with open(json_path, "r", encoding="utf-8") as f:
        toplu_sonuc = json.load(f)

    # 2. Başarılı olanları benzersiz anahtarla kümeye al
    basarili_subeler = set()
    for item in toplu_sonuc:

        if len(item.get("yorumlar", [])) > 0:
            anahtar = (
                f"{item['isim']}_{item['osm_lat']}_{item['osm_lon']}".strip().lower()
            )
            basarili_subeler.add(anahtar)

    # 3. Orijinal CSV dosyasını yükle
    if not os.path.exists(csv_input_path):
        print(f"Hata: {csv_input_path} dosyası bulunamadı!")
        return None

    df_orijinal = pd.read_csv(csv_input_path)

    # 4. Kalanları belirle (İsim + Koordinat kontrolü)
    def kaldi_mi(row):
        anahtar = f"{row['isim']}_{row['lat']}_{row['lon']}".strip().lower()
        return anahtar not in basarili_subeler

    df_kalanlar = df_orijinal[df_orijinal.apply(kaldi_mi, axis=1)]

    print(f"\n--- {sehir.upper()} Koordinat Bazlı Rapor ---")
    print(f"Toplam Orijinal Şube: {len(df_orijinal)}")
    print(f"Yorumu Çekilmiş Olan: {len(basarili_subeler)}")
    print(f"Taranacak Kalan Şube: {len(df_kalanlar)}")

    # 5. Kalanlar listesini csv_files klasörüne kaydet
    df_kalanlar.to_csv(csv_output_path, index=False, encoding="utf-8-sig")
    print(f"Kalanlar listesi güncellendi: {csv_output_path}")

    return csv_output_path
