from typing import Optional

from pydantic import BaseModel


class CostEstimateRequest(BaseModel):
    article_id: int
    context: Optional[str] = None


class CostEstimateResponse(BaseModel):
    article_id: int
    prompt: str
    raw_response: Optional[str] = None
