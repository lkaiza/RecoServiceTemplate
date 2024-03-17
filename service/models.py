from datetime import datetime
from typing import Any, List, Optional, Union

# from database import Base, metadata
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from pydantic import BaseModel
from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Table


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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None
