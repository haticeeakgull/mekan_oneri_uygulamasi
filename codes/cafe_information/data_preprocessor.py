import json
import os


def yorum_temizle(sehir):
    giris_dosyasi = f"json_files/final_mekan_verisi_vektorlu_{sehir.lower()}.json"
    cikis_dosyasi = f"json_files/vektorlu_mekan_verisi_owner_yorumlarindan_temizlenmis_{sehir.lower()}.json"

    if not os.path.exists(giris_dosyasi):
        print(f"Hata: {giris_dosyasi} bulunamadı!")
        return

    kara_liste = [
        "değerlendirmeniz",
        "nazik yorumunuz",
        "bekleriz",
        "rica ederiz",
        "geri bildirim",
        "tüm yorumlarınız",
        "merhaba",
        "değerli yorum",
        "yorumunuz",
        "işletmemiz",
        "efendim",
        "yorumlarınız",
        "geri dönüşleriniz",
    ]

    with open(giris_dosyasi, "r", encoding="utf-8") as f:
        kafeler = json.load(f)

    temiz_kafeler = []

    for kafe in kafeler:
        eski_yorumlar = kafe.get("yorumlar", [])
        yeni_yorumlar = []

        for yorum in eski_yorumlar:

            if len(yorum.strip()) < 5:
                continue

            is_owner_reply = False
            for kelime in kara_liste:
                if kelime in yorum.lower():

                    is_owner_reply = True
                    break

            if not is_owner_reply:
                yeni_yorumlar.append(yorum.strip())

        if yeni_yorumlar:
            kafe["yorumlar"] = yeni_yorumlar
            temiz_kafeler.append(kafe)

    with open(cikis_dosyasi, "w", encoding="utf-8") as f:
        json.dump(temiz_kafeler, f, ensure_ascii=False, indent=4)

    print(f"✅ {sehir.upper()} verisi temizlendi!")
    print(f"Orijinal mekan sayısı: {len(kafeler)}")
    print(f"Kalan mekan sayısı: {len(temiz_kafeler)}")
    print(f"Yeni dosya: {cikis_dosyasi}")


if __name__ == "__main__":
    yorum_temizle("ankara")
