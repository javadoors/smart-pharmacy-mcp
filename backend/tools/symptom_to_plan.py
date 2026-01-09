import json
from typing import Dict
from .drug_search import search_drugs
from .rule_engine import evaluate_rules
from llm.deepseek import chat
from llm.prompts import plan_prompt

def generate_plan(symptom_text: str, col, user_ctx: Dict) -> Dict:
    # 1) 候选集合
    candidates = search_drugs(col, symptom_text, top_k=20)
    minimal = []
    for c in candidates:
        r = evaluate_rules(c["meta"], user_ctx)
        if r["decision"] == "allow":
            minimal.append({"drug_id": c["drug_id"], "name": c["name"], "meta": c["meta"]})

    # 2) Chat 生成用药清单（JSON）
    messages = plan_prompt(symptom_text, [{"drug_id": d["drug_id"], "name": d["name"]} for d in minimal], user_ctx)
    content = chat(messages)
    try:
        parsed = json.loads(content)
        items = parsed.get("items", [])
    except Exception:
        # 回退策略：若模型未返回 JSON，使用最小集构造基础清单
        items = [{"drug_id": d["drug_id"], "dose": "按说明书", "notes": "多饮水"} for d in minimal]

    return {"plan": {"items": items}, "explain": "模型建议需药师复核"}