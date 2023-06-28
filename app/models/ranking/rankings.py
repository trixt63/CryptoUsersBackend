from typing import Optional

from pydantic import BaseModel

from app.constants.time_constants import TimeConstants


class TopDAppsQuery(BaseModel):
    order: str = 'desc'
    orderBy: str = 'tvl'
    pageSize: int = 10
    page: int = 1
    duration: int = TimeConstants.A_DAY
    category: Optional[str] = None
    chain: Optional[str] = None


class TopNFTsQuery(BaseModel):
    order: str = 'desc'
    orderBy: str = 'volume'
    pageSize: int = 10
    page: int = 1
    duration: int = TimeConstants.A_DAY


class TopTokensQuery(BaseModel):
    order: str = 'desc'
    orderBy: str = 'tokenHealth'
    pageSize: int = 10
    page: int = 1
    duration: int = TimeConstants.A_DAY


class TopSpotExchangesQuery(BaseModel):
    order: str = 'desc'
    orderBy: str = 'volume'
    pageSize: int = 10
    page: int = 1
    duration: int = TimeConstants.A_DAY


class TopDerivativeExchangesQuery(BaseModel):
    order: str = 'desc'
    orderBy: str = 'volume'
    pageSize: int = 10
    page: int = 1
    duration: int = TimeConstants.A_DAY
