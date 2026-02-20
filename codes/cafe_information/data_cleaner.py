import json
import os


def json_temizle(sehir):
    """
    Belirli bir şehir için toplanan JSON verilerini temizler ve tekilleştirir.
    Ankara verilerinin üzerine yazılmaması için şehir bazlı isimlendirme yapar.
    """
    # 1. Şehre özel dosya yollarını tanımla
    sehir_etiketi = sehir.lower()
    giris_dosyasi = f"json_files/final_mekan_verisi_{sehir_etiketi}.json"
    cikis_dosyasi = f"json_files/final_mekan_verisi_temiz_{sehir_etiketi}.json"

    # Giriş dosyası var mı kontrol et
    if not os.path.exists(giris_dosyasi):
        print(f"Hata: Temizlenecek dosya bulunamadı! -> {giris_dosyasi}")
        return

    # 2. JSON dosyasını oku
    try:
        with open(giris_dosyasi, "r", encoding="utf-8") as f:
            veriler = json.load(f)
    except Exception as e:
        print(f"Hata: Dosya okunamadı! {e}")
        return

    # 3. Verileri tekilleştirmek için sözlük oluştur
    temiz_veri_sozlugu = {}

    for mekan in veriler:
        isim = mekan.get("isim")
        lat = mekan.get("osm_lat")
        lon = mekan.get("osm_lon")
        yorumlar = mekan.get("yorumlar", [])

        # Benzersiz anahtar: (isim, lat, lon)
        anahtar = (isim, str(lat), str(lon))

        if anahtar not in temiz_veri_sozlugu:
            temiz_veri_sozlugu[anahtar] = mekan
        else:
            # Aynı mekan varsa, yorum sayısı fazla olanı (daha güncel/dolu olanı) tut
            mevcut_yorum_sayisi = len(temiz_veri_sozlugu[anahtar].get("yorumlar", []))
            yeni_yorum_sayisi = len(yorumlar)

            if yeni_yorum_sayisi > mevcut_yorum_sayisi:
                temiz_veri_sozlugu[anahtar] = mekan
                # print(f"Güncellendi (Dolu olan seçildi): {isim}")

    # 4. Temizlenmiş veriyi listeye çevir ve kaydet
    temiz_liste = list(temiz_veri_sozlugu.values())

    try:
        with open(cikis_dosyasi, "w", encoding="utf-8") as f:
            json.dump(temiz_liste, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Hata: Temizlenmiş veri kaydedilemedi! {e}")
        return

    print("-" * 30)
    print(f"🧹 {sehir.upper()} İÇİN TEMİZLİK TAMAMLANDI")
    print(f"Orijinal kayıt sayısı: {len(veriler)}")
    print(f"Temizlenmiş kayıt sayısı: {len(temiz_liste)}")
    print(f"Silinen mükerrer kayıt: {len(veriler) - len(temiz_liste)}")
    print(f"Kaydedilen dosya: {cikis_dosyasi}")
    print("-" * 30)


if __name__ == "__main__":
    # Test amaçlı kullanım
    json_temizle()
