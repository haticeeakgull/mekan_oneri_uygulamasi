from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModel

app = FastAPI()

# Modelini yükle (Daha önce kullandığın model adını buraya yaz)
model_name = "dbmdz/bert-base-turkish-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)


class SearchRequest(BaseModel):
    text: str


@app.post("/embed")
async def get_embedding(request: SearchRequest):
    inputs = tokenizer(
        request.text, return_tensors="pt", padding=True, truncation=True, max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)

    # CLS token'ın vektörünü alıyoruz (768 boyutlu)
    embedding = outputs.last_hidden_state[:, 0, :].flatten().tolist()
    return {"embedding": embedding}


# Test için
@app.get("/")
def read_root():
    return {"status": "BERT API Çalışıyor!"}
