import overpy
import pandas as pd
import os


def kafeleri_listele(sehir):
    api = overpy.Overpass()

    query = f"""
    [out:json];
    area["name"="{sehir}"]->.searchArea;
    (
      node["amenity"="cafe"](area.searchArea);
      way["amenity"="cafe"](area.searchArea);
    );
    out center;
    """

    print(f"{sehir} için kafe listesi çekiliyor...")

    try:
        result = api.query(query)
    except Exception as e:
        print(f"Overpass hatası: {e}")
        return

    data = []

    for node in result.nodes:
        name = node.tags.get("name")
        if name:
            data.append({"isim": name, "lat": float(node.lat), "lon": float(node.lon)})

    for way in result.ways:
        name = way.tags.get("name")
        if name:
            data.append(
                {
                    "isim": name,
                    "lat": float(way.center_lat),
                    "lon": float(way.center_lon),
                }
            )

    if not data:
        print(f"Uyarı: {sehir} için hiç kafe bulunamadı.")
        return

    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["lat", "lon"])

    dosya_adi = f"csv_files/{sehir.lower()}_kafeler.csv"

    os.makedirs("csv_files", exist_ok=True)

    df.to_csv(dosya_adi, index=False, encoding="utf-8-sig")
    print(f"{sehir}: {len(df)} adet şube '{dosya_adi}' dosyasına kaydedildi.")


# Örnek kullanım:
# kafeleri_listele()
# kafeleri_listele("İstanbul")
