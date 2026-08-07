from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_runs_langgraph_workflow() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={"thread_id": "demo-thread", "message": "How much did NASA spend in FY2025?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["thread_id"] == "demo-thread"
    assert body["warnings"] == ["PostgreSQL is not connected yet."]
    assert body["activity"][0]["type"] == "status"
    assert "PostgreSQL" in body["answer"]


def test_chat_asks_for_missing_agency() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat",
        json={"thread_id": "demo-thread", "message": "How much did the government spend?"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Which federal agency should I analyze?"
