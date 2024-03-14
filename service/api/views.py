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

# online models
lightfm_model = LightFMWrapperCustom(config)
knn_model = kNN(config)

# offline models
popular_model = Popular(config)
userknn_model = OfflineModel("userknn", config)
dssm_model = OfflineModel("dssm", config)
encoder_model = OfflineModel("encoder", config)
catboost_model = OfflineModel("catboost_ranker", config)

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

    if model_name == "popular":
        reco = popular_model.recommend(k_recs)

    elif model_name == "lightfm" and user_id in lightfm_model.users_mapping:
        reco = lightfm_model.recommend([user_id])

    elif model_name == "lightfm" and user_id not in lightfm_model.users_mapping:
        reco = list()

    elif model_name == "knn" and user_id in knn_model.users_mapping:
        reco = knn_model.recommend([user_id], k_recs)

    elif model_name == "knn" and user_id not in knn_model.users_mapping:
        reco = list()

    elif model_name == "catboost_ranker":
        reco = catboost_model.recommend(user_id, k_recs)

    elif model_name == "userknn":
        reco = userknn_model.recommend(user_id, k_recs)

    elif model_name == "dssm":
        reco = dssm_model.recommend(user_id, k_recs)

    elif model_name == "encoder":
        reco = encoder_model.recommend(user_id, k_recs)

    else:
        raise ModelNotFoundError(error_message=f"Model {model_name} not found")

    if len(reco) < k_recs:
        reco += popular_model.recommend(k_recs).tolist()
        reco = get_unique(reco)[:k_recs]

    return RecoResponse(user_id=user_id, items=reco)


def add_views(app: FastAPI) -> None:
    app.include_router(router)
