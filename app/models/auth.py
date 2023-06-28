from pydantic import BaseModel


class AuthBody(BaseModel):
    address: str
    signature: str
    nonce: int


class AuthQuery(BaseModel):
    jwt: str
