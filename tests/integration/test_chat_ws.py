"""Chat WebSocket integration tests (Starlette TestClient)."""

import uuid

import pytest
from starlette.testclient import TestClient

from app.main import app

DEV_EMAIL = "artist@example.com"

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_chat_ws_connect_and_typing(client, require_postgres):
    login = client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Dev user not seeded")
    token = login.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room = client.post(
        "/api/v1/chat/rooms",
        headers=headers,
        json={"name": "WS test", "member_ids": []},
    )
    assert room.status_code == 200, room.text
    room_id = room.json()["id"]

    with client.websocket_connect(f"/api/v1/ws/chat/{room_id}?token={token}") as ws:
        ws.send_json({"type": "typing", "active": True})
        ws.send_json(
            {
                "type": "message",
                "body": f"hello-{uuid.uuid4().hex[:8]}",
                "client_message_id": str(uuid.uuid4()),
            }
        )
        saw_message = False
        for _ in range(10):
            event = ws.receive_json()
            if event.get("body") and (event.get("type") in (None, "message") or event.get("echo")):
                saw_message = True
                break
        assert saw_message
