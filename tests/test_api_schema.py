from fastapi.testclient import TestClient

from app.api.schemas import ChatResponse, HealthResponse, Recommendation
from app.main import app


def test_health_schema():
    r = HealthResponse()
    assert r.status == "ok"


def test_chat_response_schema():
    r = ChatResponse(
        reply="Hello",
        recommendations=[
            Recommendation(name="Java 8 (New)", url="https://www.shl.com/x/", test_type="K")
        ],
        end_of_conversation=False,
    )
    assert r.recommendations[0].test_type == "K"


def test_health_endpoint_without_agent(monkeypatch):
    import app.state as state

    monkeypatch.setattr(state, "_agent", None)

    class FakeAgent:
        def handle(self, messages):
            from app.api.schemas import ChatResponse

            return ChatResponse(reply="ok", recommendations=[], end_of_conversation=False)

    monkeypatch.setattr(state, "get_agent", lambda: FakeAgent())
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
