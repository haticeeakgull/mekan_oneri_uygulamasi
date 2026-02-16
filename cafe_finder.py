import overpy
import pandas as pd


def ankara_kafeleri_listele():
    api = overpy.Overpass()
    query = """
    [out:json];
    area["name"="Ankara"]->.searchArea;
    (
      node["amenity"="cafe"](area.searchArea);
      way["amenity"="cafe"](area.searchArea);
    );
    out center;
    """
    print("Ankara kafe listesi çekiliyor...")
    result = api.query(query)

    data = []

    # Node (Nokta) ve Way (Alan/Bina) verilerini tara
    for node in result.nodes:
        name = node.tags.get("name")
        if name:
            data.append({"isim": name, "lat": float(node.lat), "lon": float(node.lon)})

    for way in result.ways:
        name = way.tags.get("name")
        if name:
            # Way verilerinde 'center' kullanılır
            data.append(
                {
                    "isim": name,
                    "lat": float(way.center_lat),
                    "lon": float(way.center_lon),
                }
            )

    df = pd.DataFrame(data)
    # Aynı isim ve konuma sahip olanları temizleyelim
    df = df.drop_duplicates(subset=["lat", "lon"])

    df.to_csv("ankara_kafeler.csv", index=False, encoding="utf-8-sig")
    print(f"{len(df)} adet şube koordinatlarıyla birlikte kaydedildi.")


ankara_kafeleri_listele()
