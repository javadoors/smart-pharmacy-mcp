from typing import Dict, List

def enrich_with_price_inventory(db, plan: Dict, member_tier: str) -> List[Dict]:
    """
    根据用药计划，查询库存和价格，生成带价格信息的药品列表。
    参数:
        db: 数据库适配器，需实现 get_inventory(drug_id) 和 get_price(drug_id, tier)
        plan: 用药计划，格式 {"items": [{"drug_id": int, "dose": str, "notes": str}, ...]}
        member_tier: 会员等级，例如 "basic", "gold"
    返回:
        items: 列表，每个元素包含药品信息、库存、价格、折扣和最终价格
    """
    items = []
    for it in plan["items"]:
        inv = db.get_inventory(it["drug_id"])
        price = db.get_price(it["drug_id"], member_tier)

        items.append({
            **it,
            "stock": inv["stock"],
            "unit_price": price["list_price"],
            "discount_rate": price.get("discount_rate", 1.0),
            "final_price": price["list_price"] * price.get("discount_rate", 1.0)
        })
    return items