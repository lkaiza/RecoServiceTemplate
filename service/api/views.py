from datetime import timedelta
from http.client import HTTPException
from typing import Dict

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from typing_extensions import Annotated

from service.api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
    users_db,
)
from service.api.exceptions import ModelNotFoundError, UserNotFoundError
from service.log import app_logger
from service.models import Error, RecoResponse, Token, TokenData, User
from service.utils import get_unique, read_config
from src.models import LightFMWrapperCustom, OfflineModel, Popular, kNN

app = FastAPI()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

config_path = "config.yml"
config = read_config(config_path)

models = {}
# online models
models["lightfm"] = LightFMWrapperCustom(config)
models["knn"] = kNN(config)

# offline models
models["popular"] = Popular(config)
models["userknn"] = OfflineModel("userknn", config)
models["dssm"] = OfflineModel("dssm", config)
models["encoder"] = OfflineModel("encoder", config)
models["recbole_recvae"] = OfflineModel("recvae", config)
models["catboost_ranker"] = OfflineModel("catboost_ranker", config)


@router.get(
    path="/health",
    tags=["Health"],
)
async def health() -> str:
    return "I am alive"


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]):
    return [{"item_id": "Foo", "owner": current_user.username}]


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
    current_user: User = Depends(get_current_user),
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
        reco += models["popular"].recommend(n_recs=k_recs).tolist()
        reco = get_unique(reco)[:k_recs]
    return RecoResponse(user_id=user_id, items=reco)


def add_views(app: FastAPI) -> None:
    app.include_router(router)
