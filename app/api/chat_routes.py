"""RAG chat routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import RagServiceDependency, get_rag_service
from app.schemas.chat_schema import ChatAskRequest, ChatAskResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatAskResponse)
def ask_chat(
    request: ChatAskRequest,
    rag_service: RagServiceDependency = Depends(get_rag_service),
) -> ChatAskResponse:
    """Answer a chat question through the RAG service."""

    try:
        rag_answer = rag_service.answer_question(
            question=request.question,
            top_k=request.top_k,
            where=request.filters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RAG service failed") from exc

    return ChatAskResponse(
        answer=rag_answer.answer,
        sources=rag_answer.sources,
        retrieved_chunks=rag_answer.retrieved_chunks,
    )
