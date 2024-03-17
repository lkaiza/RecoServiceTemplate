from typing import Any, List, Optional, Union

from pydantic import BaseModel


class RecoResponse(BaseModel):
    user_id: int
    items: List[int]


class Error(BaseModel):
    error_key: str
    error_message: str
    error_loc: Optional[Any] = None


class User(BaseModel):
    username: str
    hashed_password: str
    disabled: Union[bool, None] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None
