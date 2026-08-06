from fastapi import APIRouter

from app.schemas.chat import ActivityEvent, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        thread_id=request.thread_id,
        answer=(
            "FedLens backend is initialized. The next milestone will connect this "
            "endpoint to a typed USAspending tool for supported agency-spending questions."
        ),
        activity=[
            ActivityEvent(
                type="status",
                message="Received chat request and returned scaffold response.",
            )
        ],
        warnings=["Data tools are not connected yet."],
    )
