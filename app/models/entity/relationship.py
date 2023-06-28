from typing import Optional

from pydantic import BaseModel


class RelationshipQuery(BaseModel):
    chain: Optional[str] = None
    type: str
    fromNode: str
    toNode: str
