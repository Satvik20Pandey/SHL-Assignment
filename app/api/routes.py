from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse, HealthResponse
from app.state import get_agent

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    get_agent()
    return HealthResponse()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    agent = get_agent()
    # Keep API robust if client accidentally sends longer histories.
    # Assignment limit is 8 turns, so we keep the latest 8 messages.
    trimmed = body.messages[-8:]
    return agent.handle(trimmed)
