from typing import List

from fastapi import APIRouter, FastAPI, Request
from pydantic import BaseModel

from service.api.exceptions import ModelNotFoundError, UserNotFoundError
from service.log import app_logger
from service.models import Error
from service.utils import get_unique, read_config
from src.models import LightFMWrapperCustom, OfflineModel, Popular, kNN


class RecoResponse(BaseModel):
    user_id: int
    items: List[int]


config_path = "config.yml"
config = read_config(config_path)

models = {}
# online models
models['lightfm'] = LightFMWrapperCustom(config)
models['knn'] = kNN(config)

# offline models
models['popular'] = Popular(config)
models['userknn'] = OfflineModel("userknn", config)
models['dssm'] = OfflineModel("dssm", config)
models['encoder'] = OfflineModel("encoder", config)
models['recbole_recvae'] = OfflineModel("recvae", config)
models['catboost_ranker'] = OfflineModel("catboost_ranker", config)

router = APIRouter()


@router.get(
    path="/health",
    tags=["Health"],
)
async def health() -> str:
    return "I am alive"


@router.get(
    path="/reco/{model_name}/{user_id}",
    tags=["Recommendations"],
    response_model=RecoResponse,
    responses={
        "404": {"model": Error, "description": "Model or user not found"},
        "200": {"description": "Successful Response"},
    },
)
async def get_reco(
    request: Request,
    model_name: str,
    user_id: int,
) -> RecoResponse:
    app_logger.info(f"Request for model: {model_name}, user_id: {user_id}")

    k_recs = request.app.state.k_recs

    if user_id > 10**9:
        raise UserNotFoundError(error_message=f"User {user_id} not found")
    if model_name in models:
        if user_id in models[model_name].users_mapping:
            reco = models[model_name].recommend(user_id, k_recs)
        else:
            reco = []
    else:
        raise ModelNotFoundError(error_message=f"Model {model_name} not found")

    if len(reco) < k_recs:
        reco += models['popular'].recommend(n_recs=k_recs).tolist()
        reco = get_unique(reco)[:k_recs]
    return RecoResponse(user_id=user_id, items=reco)


def add_views(app: FastAPI) -> None:
    app.include_router(router)
