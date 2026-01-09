"""
order_checkout.py
负责生成订单并返回订单信息。
"""
from typing import List, Dict

def create_order(db, member_id: int, items: List[Dict]) -> Dict:
    """
    根据药品列表生成订单。
    参数:
        db: 数据库适配器，需实现 insert_order(member_id, items, total)
        member_id: 用户 ID
        items: 药品列表，每个元素包含 drug_id, final_price 等信息
    返回:
        dict: 包含订单号、总金额和支付二维码链接
    """
    total = sum(i["final_price"] for i in items)
    order_id = db.insert_order(member_id, items, total)

    return {
        "order_id": order_id,
        "total": total,
        "payment_qr": f"/pay/{order_id}"
    }