from typing import Dict

def evaluate_rules(drug: dict, user_ctx: dict) -> dict:
    reasons, decision = [], "allow"
    if drug.get("is_rx") and not user_ctx.get("prescription_uploaded"):
        decision = "require_pharmacist_review"
        reasons.append("处方药需药师复核或上传处方")
    contraindications = drug.get("contraindications", [])
    if "pregnancy" in contraindications and user_ctx.get("pregnant"):
        decision = "block"
        reasons.append("妊娠禁用")
    flags = drug.get("flags", [])
    if "fever_high" in flags and (user_ctx.get("fever_celsius") or 0) >= 39:
        decision = "require_pharmacist_review"
        reasons.append("高热红旗，建议线下就医")
    return {"decision": decision, "reasons": reasons}