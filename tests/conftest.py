# pylint: disable=redefined-outer-name
import os
import random
import string

import pytest
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from starlette.testclient import TestClient

from service.api.app import create_app
from service.settings import ServiceConfig, get_config


@pytest.fixture
def service_config() -> ServiceConfig:
    return get_config()


@pytest.fixture
def app(
    service_config: ServiceConfig,
) -> FastAPI:
    app = create_app(service_config)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    return TestClient(app=app)


@pytest.fixture
def unknown_model() -> str:
    return "".join(random.choices(string.ascii_letters, k=10))


@pytest.fixture
def valid_request_data():
    return {"model_name": "popular", "user_id": 1}


@pytest.fixture
def wrong_token():
    token = "".join(random.choices(string.ascii_letters, k=126))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def valid_token():
    return {"Authorization": f"Bearer {os.getenv('BOT_TOKEN')}"}
