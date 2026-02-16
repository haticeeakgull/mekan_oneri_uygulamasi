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
    for node in result.nodes:
        name = node.tags.get("name")
        if name:
            data.append({"isim": name })
            
    for way in result.ways:
        name = way.tags.get("name")
        if name:
            data.append({"isim": name})
    
    df = pd.DataFrame(data).drop_duplicates(subset=['isim'])
    df.to_csv("ankara_kafeler.csv", index=False, encoding="utf-8-sig")
    print(f"{len(df)} adet kafe bulundu ve ankara_kafeler.csv dosyasına kaydedildi.")

ankara_kafeleri_listele()