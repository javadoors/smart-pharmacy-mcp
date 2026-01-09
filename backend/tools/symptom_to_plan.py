from typing import Dict
from .drug_search import search_drugs
from .rule_engine import evaluate_rules

def generate_plan(symptom_text: str, col, user_ctx: Dict) -> Dict:
    candidates = search_drugs(col, symptom_text, top_k=20)
    minimal = []
    for c in candidates:
        r = evaluate_rules(c["meta"], user_ctx)
        if r["decision"] == "allow":
            minimal.append({"drug": c, "rule": r})

    plan = {"items": [{"drug_id": d["drug"]["drug_id"], "dose": "按说明书", "notes": "多饮水"} for d in minimal]}
    return {"plan": plan, "explain": "模型建议需药师复核"}