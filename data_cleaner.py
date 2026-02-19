import json


def json_temizle(dosya_yolu):
    # 1. JSON dosyasını oku
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veriler = json.load(f)
    except Exception as e:
        print(f"Hata: Dosya okunamadı! {e}")
        return

    # 2. Verileri tekilleştirmek için bir sözlük oluştur
    # Anahtar (Key) olarak: (isim, lat, lon) kullanacağız
    temiz_veri_sozlugu = {}

    for mekan in veriler:
        isim = mekan.get("isim")
        lat = mekan.get("osm_lat")
        lon = mekan.get("osm_lon")
        yorumlar = mekan.get("yorumlar", [])

        # Benzersiz bir anahtar oluştur (Koordinatlar bazen float farkı yaratmasın diye stringe çeviriyoruz)
        anahtar = (isim, str(lat), str(lon))

        if anahtar not in temiz_veri_sozlugu:
            # Eğer bu mekan sözlükte yoksa ekle
            temiz_veri_sozlugu[anahtar] = mekan
        else:
            # Eğer bu mekan zaten varsa, yorumu daha fazla olanı tut
            mevcut_yorum_sayisi = len(temiz_veri_sozlugu[anahtar].get("yorumlar", []))
            yeni_yorum_sayisi = len(yorumlar)

            if yeni_yorum_sayisi > mevcut_yorum_sayisi:
                temiz_veri_sozlugu[anahtar] = mekan
                print(f"Güncellendi (Dolu olan seçildi): {isim}")

    # 3. Sözlükteki değerleri tekrar liste haline getir
    temiz_liste = list(temiz_veri_sozlugu.values())

    # 4. Temizlenmiş veriyi yeni bir dosyaya kaydet (Veya üzerine yaz)
    temiz_dosya_yolu = "final_mekan_verisi_temiz.json"
    with open(temiz_dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(temiz_liste, f, ensure_ascii=False, indent=4)

    print("-" * 30)
    print(f"İşlem Tamamlandı!")
    print(f"Orijinal kayıt sayısı: {len(veriler)}")
    print(f"Temizlenmiş kayıt sayısı: {len(temiz_liste)}")
    print(f"Silinen mükerrer/boş kayıt: {len(veriler) - len(temiz_liste)}")
    print(f"Yeni dosya: {temiz_dosya_yolu}")


# Kullanımı
json_temizle("final_mekan_verisi.json")
