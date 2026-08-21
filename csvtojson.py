import pandas as pd

# 1. CSV dosyasını oku
df = pd.read_csv("codes/cafe_information/csv_files/trabzon_kafe_listesi.csv")

# 2. JSON olarak kaydet (Türkçe karakterleri korumak için force_ascii=False)
df.to_json(
    "json_files/trabzon_kafe_listesi.json",
    orient="records",
    indent=4,
    force_ascii=False,
)

print("✅ CSV dosyası başarıyla JSON'a dönüştürüldü!")
