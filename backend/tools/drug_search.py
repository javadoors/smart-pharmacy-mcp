from typing import List, Dict
from pymilvus import Collection
from llm.deepseek import embed_text

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