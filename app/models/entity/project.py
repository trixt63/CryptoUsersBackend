from typing import Optional

from pydantic import BaseModel


class OverviewQuery(BaseModel):
    _id: str
    # type: str
    chain: Optional[str] = None


class StatsQuery(BaseModel):
    type: str
    chain: Optional[str] = None
    history: bool = True
