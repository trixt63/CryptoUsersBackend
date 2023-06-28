from typing import Optional

from pydantic import BaseModel

from app.constants.time_constants import TimeConstants


class DAppsQuery(BaseModel):
    chain: Optional[str] = None


class DAppLendingBalanceQuery(BaseModel):
    duration: int = TimeConstants.DAYS_30
    chain: Optional[str] = None
    action: str = 'deposit'
