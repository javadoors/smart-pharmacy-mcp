def enrich_with_price_inventory(db, plan, member_tier: str):
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