"""E2E #10: WebSocket reconnect with exponential backoff (API-level harness)."""

import json
import time
import uuid

import pytest
from websocket import WebSocketTimeoutException, create_connection

from conftest import BASE_URL, dev_login

pytestmark = pytest.mark.e2e


def _ws_base() -> str:
    return BASE_URL.replace("http://", "ws://").replace("https://", "wss://")


@pytest.mark.e2e
def test_websocket_reconnect_after_drop(client):
    headers, _ = dev_login(client)
    token = headers["Authorization"].split(" ", 1)[1]

    room = client.post(
        "/api/v1/chat/rooms",
        headers=headers,
        json={"name": f"WS reconnect {uuid.uuid4().hex[:8]}", "member_ids": []},
    )
    assert room.status_code in (200, 201), room.text
    room_id = room.json()["id"]
    ws_url = f"{_ws_base()}/api/v1/ws/chat/{room_id}?token={token}"

    ws1 = create_connection(ws_url, timeout=10)
    try:
        client_msg_id = f"reconnect-{uuid.uuid4()}"
        ws1.send(json.dumps({"body": "before drop", "client_message_id": client_msg_id}))
        time.sleep(0.3)
    finally:
        ws1.close()

    # Simulate reconnect after drop (client would backoff; here immediate reconnect)
    ws2 = create_connection(ws_url, timeout=10)
    try:
        ws2.send(json.dumps({"body": "after reconnect", "client_message_id": f"reconnect-{uuid.uuid4()}"}))
        ws2.settimeout(3)
        try:
            while True:
                raw = ws2.recv()
                payload = json.loads(raw)
                if payload.get("body") == "after reconnect":
                    break
        except WebSocketTimeoutException:
            pass
    finally:
        ws2.close()

    history = client.get(f"/api/v1/chat/rooms/{room_id}/messages", headers=headers)
    assert history.status_code == 200
    payload = history.json()
    messages = payload["items"] if isinstance(payload, dict) and "items" in payload else payload
    bodies = [m["body"] for m in messages]
    assert "before drop" in bodies
    assert "after reconnect" in bodies
