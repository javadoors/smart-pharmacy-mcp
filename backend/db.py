from sqlalchemy.orm import Session
from domain.models import Drug, Inventory, Price, Order, OrderItem

class ORMDB:
    def __init__(self, session: Session):
        self.session = session

    def get_inventory(self, drug_id):
        inv = self.session.query(Inventory).filter_by(drug_id=drug_id).first()
        return {"stock": inv.stock if inv else 0}

    def get_price(self, drug_id, tier):
        price = self.session.query(Price).filter_by(drug_id=drug_id, member_tier=tier).first()
        if price:
            return {"list_price": float(price.list_price), "discount_rate": float(price.discount_rate)}
        return {"list_price": 0.0, "discount_rate": 1.0}

    def insert_order(self, member_id, items, total):
        order = Order(member_id=member_id, total=total)
        self.session.add(order)
        self.session.flush()  # 获取 order.id
        for it in items:
            oi = OrderItem(order_id=order.id,
                           drug_id=it["drug_id"],
                           qty=1,
                           unit_price=it["unit_price"],
                           final_price=it["final_price"])
            self.session.add(oi)
        self.session.commit()
        return order.id

    def get_latest_order(self, member_id):
        order = self.session.query(Order).filter_by(member_id=member_id).order_by(Order.created_at.desc()).first()
        if not order:
            return None, []
        items = []
        for it in order.items:
            items.append({
                "drug_id": it.drug_id,
                "qty": it.qty,
                "unit_price": float(it.unit_price),
                "final_price": float(it.final_price),
                "dose": "按说明书",
                "notes": "多饮水"
            })
        return {"id": order.id, "member_id": member_id, "total": float(order.total)}, items