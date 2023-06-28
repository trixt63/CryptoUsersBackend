from typing import Optional

from pydantic import BaseModel


class AlertsQuery(BaseModel):
    chain: Optional[str] = None
    type: Optional[str] = None
    startTime: Optional[int] = None
