from pydantic import BaseModel
from typing import List, Dict, Optional

class UserCtx(BaseModel):
    age: Optional[int] = None
    pregnant: Optional[bool] = None
    prescription_uploaded: Optional[bool] = None
    fever_celsius: Optional[float] = None

class SymptomRequest(BaseModel):
    symptom: str
    user_ctx: UserCtx

class PlanItem(BaseModel):
    drug_id: int
    dose: str
    notes: str

class Plan(BaseModel):
    items: List[PlanItem]