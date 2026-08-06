from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_scaffold_response() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={"thread_id": "demo-thread", "message": "How much did NASA spend in FY2025?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["thread_id"] == "demo-thread"
    assert body["warnings"] == ["Data tools are not connected yet."]
    assert body["activity"][0]["type"] == "status"
