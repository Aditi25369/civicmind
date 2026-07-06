"""
agents/coordinator.py
Simplified version — agent deployment disabled for local demo.
"""

async def run_local(query: str) -> str:
    from services.gemini_service import query_gemini
    result = await query_gemini(
        message=query,
        domain="general",
        history=[],
        rag_context=None,
    )
    return result.get("answer", "")