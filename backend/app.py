from fastapi import FastAPI, Depends, Query
from config import init_milvus, SessionLocal
from db import ORMDB
from tools.symptom_to_plan import generate_plan
from tools.pricing_inventory import enrich_with_price_inventory
from tools.order_checkout import create_order

app = FastAPI()
col = init_milvus()

def get_db():
    db = SessionLocal()
    try:
        yield ORMDB(db)
    finally:
        db.close()

@app.post("/symptom/plan")
def symptom_plan(payload: dict, db: ORMDB = Depends(get_db)):
    user_ctx = payload.get("user_ctx", {})
    plan = generate_plan(symptom_text=payload["symptom"], col=col, user_ctx=user_ctx)
    items = enrich_with_price_inventory(db=db, plan=plan["plan"], member_tier=payload.get("member_tier","basic"))
    order_id = create_order(db=db, member_id=payload.get("member_id",1), items=items)["order_id"]
    order, order_items = db.get_latest_order(payload.get("member_id",1))
    return {"plan": plan, "items": order_items, "order": order}

@app.get("/order/latest")
def order_latest(member_id: int = Query(...), db: ORMDB = Depends(get_db)):
    order, items = db.get_latest_order(member_id)
    if order:
        return {"order": {"order_id": order["id"], "total": order["total"], "payment_qr": f"/pay/{order['id']}"}, "items": items}
    return {"order": None, "items": []}