def create_order(db, member_id: int, items: list):
    total = sum(i["final_price"] for i in items)
    order_id = db.insert_order(member_id, items, total)
    return {"order_id": order_id, "total": total, "payment_qr": f"/pay/{order_id}"}