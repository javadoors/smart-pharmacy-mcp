import os
import requests
from typing import List, Dict
from pymilvus import Collection

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def embed_text(text: str) -> List[float]:
    url = "https://api.deepseek.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {
        "model": "deepseek-embedding",  # DeepSeek 提供的 embedding 模型名称
        "input": text
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def upsert_drug(col: Collection, drug: Dict):
    vec = embed_text(
        f"{drug['name']} {drug.get('indications','')} {drug.get('contraindications','')} {drug.get('desc','')}"
    )
    col.insert([[drug["id"]], [drug["name"]], [vec], [drug]])

def search_drugs(col: Collection, query: str, top_k: int = 10) -> List[Dict]:
    qvec = embed_text(query)
    res = col.search([qvec], "embedding", params={"metric_type":"COSINE"}, limit=top_k,
                     output_fields=["drug_id","name","metadata"])
    out = []
    for hits in res:
        for r in hits:
            out.append({
                "drug_id": r.id,
                "name": r.entity.get("name"),
                "meta": r.entity.get("metadata")
            })
    return out