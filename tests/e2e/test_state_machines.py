"""E2E #11: Illegal state transitions rejected via API."""

import uuid

import pytest


@pytest.mark.e2e
def test_market_order_illegal_transition(client, buyer_headers, auth_headers):
    search = client.get("/api/v1/market/kworks", params={"q": "Сведение"})
    if search.status_code != 200 or not search.json():
        pytest.skip("No seeded kworks")

    order = client.post(
        "/api/v1/market/orders",
        headers=buyer_headers,
        json={"kwork_id": search.json()[0]["id"]},
    )
    if order.status_code == 400:
        pytest.skip("Cannot order own kwork")
    assert order.status_code == 200
    order_id = order.json()["id"]

    illegal = client.post(
        f"/api/v1/market/orders/{order_id}/transition",
        headers=auth_headers,
        json={"to_status": "COMPLETED"},
    )
    assert illegal.status_code == 409
    assert illegal.json()["error"]["code"] == "invalid_state_transition"


@pytest.mark.e2e
def test_office_ready_without_tracks_rejected(client, auth_headers):
    created = client.post(
        "/api/v1/studio/projects",
        json={"title": f"State Machine {uuid.uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    office = client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers={**auth_headers, "Idempotency-Key": f"sm-{uuid.uuid4()}"},
    )
    assert office.status_code == 202
    office_project_id = office.json()["office_project_id"]

    ready = client.post(
        f"/api/v1/office/projects/{office_project_id}/ready",
        headers=auth_headers,
    )
    assert ready.status_code == 400
    assert ready.json()["error"]["code"] in {"no_tracks", "track_missing_media"}
