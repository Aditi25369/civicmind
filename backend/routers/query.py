"""
/query — NL query endpoint.
Uses Vertex AI Agent Engine when VERTEX_AGENT_RESOURCE is set,
falls back to direct Gemini + RAG otherwise.
"""
import os
from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse
from services.gemini_service import query_gemini, search_documents
from services.firestore_service import create_session, get_session, append_message

router = APIRouter()

AGENT_RESOURCE = os.environ.get("VERTEX_AGENT_RESOURCE", "")


async def _call_agent(message: str, domain: str, session_id: str, history: list) -> dict:
    """Call deployed Vertex AI Agent Engine."""
    try:
        import vertexai
        from vertexai import agent_engines
        PROJECT_ID = os.environ["GCP_PROJECT_ID"]
        LOCATION   = os.environ.get("GCP_LOCATION", "us-central1")
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        remote_app = agent_engines.get(AGENT_RESOURCE)
        session    = remote_app.create_session(user_id=session_id)

        response_text = ""
        for event in remote_app.stream_query(
            user_id=session_id,
            session_id=session["id"],
            message=message,
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text"):
                        response_text += part.text

        return {
            "answer": response_text,
            "suggested_actions": [],
            "follow_up_questions": [],
        }
    except Exception as e:
        rag_context, _ = await search_documents(message, domain)
        return await query_gemini(message, domain, history, rag_context)


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest):
    session_id = request.session_id
    if not session_id:
        session_id = await create_session(request.domain.value)

    existing = await get_session(session_id)
    history  = request.history or []
    if existing and existing.get("messages"):
        history = existing["messages"] + [m.model_dump() for m in history]

    if AGENT_RESOURCE:
        result  = await _call_agent(request.message, request.domain.value, session_id, history)
        sources = []
    else:
        rag_context, sources = ("", [])
        if request.use_rag:
            rag_context, sources = await search_documents(request.message, request.domain.value)
        result = await query_gemini(
            message=request.message,
            domain=request.domain.value,
            history=[m.model_dump() if hasattr(m, "model_dump") else m for m in history],
            rag_context=rag_context,
        )

    await append_message(session_id, "user",      request.message)
    await append_message(session_id, "assistant", result["answer"])

    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        domain=request.domain,
        session_id=session_id,
        suggested_actions=result.get("suggested_actions", []),
        follow_up_questions=result.get("follow_up_questions", []),
    )


@router.get("/session/{session_id}")
async def get_chat_history(session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session