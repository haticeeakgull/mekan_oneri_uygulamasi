import os
import sys
import overpy
import selenium

# Kendi yazdığın modülleri içe aktarıyoruz
from codes.cafe_information.cafe_finder import kafeleri_listele
from codes.cafe_information.eksikleri_ayikla import eksikleri_tespit_et
from codes.cafe_information.comment_scrapping_for_file import hepsini_topla
from codes.cafe_information.data_cleaner import json_temizle
from codes.supabase.create_supabase_table import verileri_toplu_yukle


def baslat_operasyon(sehir_adi):
    print(f"\n{sehir_adi.upper()} İÇİN VERİ OPERASYONU BAŞLIYOR...")

    # 0. Klasörlerin varlığından emin olalım
    os.makedirs("csv_files", exist_ok=True)
    os.makedirs("json_files", exist_ok=True)

    # 1. ADIM: Şehirdeki kafeleri Overpass ile bul ve CSV'ye kaydet
    print("\n--- 1. ADIM: Kafe Listesi Oluşturuluyor ---")
    kafeleri_listele(sehir_adi)

    # 2. ADIM: Mevcut JSON ile CSV'yi kıyasla, taranmamışları ayıkla
    print("\n--- 2. ADIM: Eksik/Taranacak Mekanlar Belirleniyor ---")
    eksikleri_tespit_et(sehir_adi)

    # 3. ADIM: Selenium Botunu Başlat (Yedekleme yaparak çalışır)
    print("\n--- 3. ADIM: Google Maps Botu Başlatılıyor (Selenium) ---")
    # Not: hepsini_topla() fonksiyonuna sehir_adi'nı gönderiyoruz
    hepsini_topla(sehir_adi)

    # 4. ADIM: Verileri temizle (Mükerrerleri sil, dolu olanı seç)
    print("\n--- 4. ADIM: Veri Temizleme ve Tekilleştirme ---")
    json_temizle(f"json_files/final_mekan_verisi_{sehir_adi}.json")

    # 5. ADIM: Supabase'e yükle
    print("\n--- 5. ADIM: Veritabanı Aktarımı ---")
    cevap = input(f"{sehir_adi} verileri Supabase'e yüklensin mi? (e/h): ")
    if cevap.lower() == "e":
        verileri_toplu_yukle(f"json_files/final_mekan_verisi_temiz_{sehir_adi}.json")
    else:
        print("İşlem kullanıcı tarafından durduruldu. Veriler JSON olarak saklanıyor.")

    print(f"\n✅ {sehir_adi} operasyonu başarıyla tamamlandı!")


if __name__ == "__main__":
    # İstanbul için deneme yapmak istiyorsan burayı değiştirmen yeterli
    baslat_operasyon("Ankara")
