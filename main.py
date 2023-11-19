from operator import mod
import os
from random import random
from typing import List
import uvicorn
from pydantic import BaseModel

from service.api.app import create_app
from service.settings import get_config


config = get_config()
app = create_app(config)


if __name__ == "__main__":

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(app, host=host, port=port)

# class RecoResponse(BaseModel):
#     user_id: int
#     items: List[int]


# @app.get("/health")
# async def health():
#     return "I am alive"


# @app.get("/reco/{model_name}/{user_id}")
# async def get_reco(model_name: str, user_id: int):
#     if model_name == "top":
#         reco = list(range(10))
#     elif model_name == "random":
#         reco = [random.randint(10, 1000) for _ in range(10)]
#     else:
#         raise ValueError()
#     resp = RecoResponse(user_id=user_id, items=reco)
#     return resp
