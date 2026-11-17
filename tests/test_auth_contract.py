from unittest.mock import Mock

import jwt
from fastapi.testclient import TestClient

from auth import JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_KEY, create_session
from main import app


def test_access_token_lifetime():
    token = create_session(Mock(), "student_1")
    claims = jwt.decode(
        token, JWT_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE, issuer=JWT_ISSUER
    )
    assert claims["exp"] - claims["iat"] == 900


def test_protected_routes_require_authentication():
    with TestClient(app) as client:
        assert client.post("/chat", json={"message": "hello"}).status_code == 401
        assert client.get("/deadlines").status_code == 401
        assert client.get("/students/1/interests").status_code == 401


def test_cannot_read_another_student(authenticated_student):
    with TestClient(app) as client:
        assert client.get("/students/999999/interests").status_code == 403
