from fastapi import FastAPI
from config import init_milvus
from tools.symptom_to_plan import generate_plan
from tools.pricing_inventory import enrich_with_price_inventory
from tools.order_checkout import create_order

app = FastAPI()
col = init_milvus()

# 伪 DB 适配器（示例）
class DB:
    def get_inventory(self, drug_id): return {"stock": 100}
    def get_price(self, drug_id, tier): return {"list_price": 39.9, "discount_rate": 0.9 if tier=="gold" else 1.0}
    def insert_order(self, member_id, items, total): return 10001

db = DB()

@app.post("/symptom/plan")
def symptom_plan(payload: dict):
    user_ctx = payload.get("user_ctx", {})
    plan = generate_plan(symptom_text=payload["symptom"], col=col, user_ctx=user_ctx)
    items = enrich_with_price_inventory(db=db, plan=plan["plan"], member_tier=payload.get("member_tier","basic"))
    order = create_order(db=db, member_id=payload.get("member_id",1), items=items)
    return {"plan": plan, "items": items, "order": order}