from typing import Annotated

from fastapi import APIRouter, Depends

from app.agent.graph import FedLensGraph, get_graph
from app.schemas.chat import ActivityEvent, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    graph: Annotated[FedLensGraph, Depends(get_graph)],
) -> ChatResponse:
    result = await graph.invoke(request.message)
    return ChatResponse(
        thread_id=request.thread_id,
        answer=result.answer,
        key_numbers=result.key_numbers,
        visualizations=result.visualizations,
        sources=result.sources,
        activity=[ActivityEvent(**event) for event in result.activity],
        warnings=result.warnings,
    )
