import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login():
    response = client.post(
        "/login",
        data={"username": "admin", "password": "123"}
    )
    assert response.status_code == 200


def test_transaction_requires_auth():
    response = client.post("/transaction", json={
        "transaction_id":"t1",
        "user_id":"u1",
        "amount":500,
        "location":"IN"
    })
    assert response.status_code == 401
