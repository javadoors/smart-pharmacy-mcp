SYSTEM_PLAN = (
    "你是药师助手。根据症状与候选药品，生成安全、清晰的用药清单。"
    "必须标注用法用量、注意事项、何时就医；若风险较高，建议线下就医。"
)

def plan_prompt(symptom: str, candidates: list, user_ctx: dict) -> list:
    user = {
        "role": "user",
        "content": (
            f"症状：{symptom}\n"
            f"候选药品（已通过规则过滤）：{candidates}\n"
            f"用户上下文：{user_ctx}\n"
            "请给出用药清单（JSON，字段：drug_id、dose、notes），并附简要说明。"
        )
    }
    return [{"role": "system", "content": SYSTEM_PLAN}, user]