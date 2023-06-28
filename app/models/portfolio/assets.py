from typing import Optional

from pydantic import BaseModel

from app.constants.time_constants import TimeConstants


class CreditScoreQuery(BaseModel):
    history: bool = False
    duration: int = TimeConstants.DAYS_30
    chain: Optional[str] = None


class TokensQuery(BaseModel):
    chain: Optional[str] = None


class TokenBalanceQuery(BaseModel):
    duration: int = TimeConstants.DAYS_30
    chain: Optional[str] = None
