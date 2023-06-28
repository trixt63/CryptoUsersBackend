from typing import Optional

from pydantic import BaseModel


class SearchQuery(BaseModel):
    keyword: str
    chain: Optional[str] = None
    type: Optional[str] = None


class SuggestionQuery(BaseModel):
    keyword: str
    limit: int = 5
