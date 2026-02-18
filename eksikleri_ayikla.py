import json
import pandas as pd


def eksikleri_tespit_et(json_path, csv_path):
    with open(json_path, "r", encoding="utf-8") as f:
        toplu_sonuc = json.load(f)

    # 2. Başarılı olanları "isim_lat_lon" şeklinde benzersiz bir anahtarla kümeye al
    # Bu sayede farklı şubeler birbirine karışmaz
    basarili_subeler = set()
    for item in toplu_sonuc:
        if len(item.get("yorumlar", [])) > 0:
            # Koordinatları string'e çevirip birleştiriyoruz
            anahtar = (
                f"{item['isim']}_{item['osm_lat']}_{item['osm_lon']}".strip().lower()
            )
            basarili_subeler.add(anahtar)

    # 3. Orijinal CSV dosyasını yükle
    df_orijinal = pd.read_csv(csv_path)

    # 4. Kalanları belirle
    def kaldi_mi(row):
        # CSV'deki her satır için aynı benzersiz anahtarı oluştur
        anahtar = f"{row['isim']}_{row['lat']}_{row['lon']}".strip().lower()
        return anahtar not in basarili_subeler

    # Daha önce çekilmeyenleri (veya yorumu boş olanları) filtrele
    df_kalanlar = df_orijinal[df_orijinal.apply(kaldi_mi, axis=1)]

    print(f"--- Koordinat Bazlı Rapor ---")
    print(f"Toplam Satır (CSV): {len(df_orijinal)}")
    print(f"Başarıyla Çekilen Şube: {len(basarili_subeler)}")
    print(f"Kalan Şube (Farklı Koordinatlar): {len(df_kalanlar)}")

    # Yeni listeyi kaydet
    df_kalanlar.to_csv("ankara_kafeler_kalanlar.csv", index=False)
    return "ankara_kafeler_kalanlar.csv"


if __name__ == "__main__":
    eksikleri_tespit_et("final_mekan_verisi.json", "ankara_kafeler.csv")
