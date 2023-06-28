from typing import Optional

from pydantic import BaseModel


class OverviewQuery(BaseModel):
    type: str
    chain: Optional[str] = None


class StatsQuery(BaseModel):
    type: str
    chain: Optional[str] = None
    history: bool = True
