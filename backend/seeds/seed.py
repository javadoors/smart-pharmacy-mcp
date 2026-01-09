import csv, json
from pymilvus import connections, Collection
from tools.drug_search import upsert_drug

connections.connect(host="milvus", port="19530")
col = Collection("drugs_vectors")

with open("seeds/drugs.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        drug = {
            "id": int(row["id"]),
            "name": row["name"],
            "indications": row.get("indications",""),
            "contraindications": json.loads(row.get("contraindications","[]")),
            "flags": json.loads(row.get("flags","[]")),
            "is_rx": row.get("is_rx","false").lower()=="true",
            "desc": row.get("desc","")
        }
        upsert_drug(col, drug)
print("Seeded drugs into Milvus.")