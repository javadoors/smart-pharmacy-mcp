from fastapi import FastAPI, Query
from config import init_milvus
from tools.symptom_to_plan import generate_plan
from tools.pricing_inventory import enrich_with_price_inventory
from tools.order_checkout import create_order

app = FastAPI()
col = init_milvus()

# 伪 DB 适配器（示例）
class DB:
    def __init__(self):
        # 用内存模拟订单存储
        self.orders = []
        self.items = {}

    def get_inventory(self, drug_id): 
        return {"stock": 100}

    def get_price(self, drug_id, tier): 
        return {"list_price": 39.9, "discount_rate": 0.9 if tier=="gold" else 1.0}

    def insert_order(self, member_id, items, total):
        order_id = len(self.orders) + 1
        self.orders.append({"id": order_id, "member_id": member_id, "total": total})
        self.items[order_id] = items
        return order_id

    def get_latest_order(self, member_id):
        # 找到该用户最新订单
        for order in reversed(self.orders):
            if order["member_id"] == member_id:
                return order, self.items.get(order["id"], [])
        return None, []

db = DB()

@app.post("/symptom/plan")
def symptom_plan(payload: dict):
    user_ctx = payload.get("user_ctx", {})
    plan = generate_plan(symptom_text=payload["symptom"], col=col, user_ctx=user_ctx)
    items = enrich_with_price_inventory(db=db, plan=plan["plan"], member_tier=payload.get("member_tier","basic"))
    order_id = create_order(db=db, member_id=payload.get("member_id",1), items=items)["order_id"]
    order, order_items = db.get_latest_order(payload.get("member_id",1))
    return {"plan": plan, "items": order_items, "order": order}

@app.get("/order/latest")
def order_latest(member_id: int = Query(...)):
    order, items = db.get_latest_order(member_id)
    if order:
        return {"order": {"order_id": order["id"], "total": order["total"], "payment_qr": f"/pay/{order['id']}"}, "items": items}
    return {"order": None, "items": []}
