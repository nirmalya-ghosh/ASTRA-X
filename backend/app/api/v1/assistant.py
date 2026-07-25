"""
AstraX AI — AI Assistant API Router
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import get_session, ChatMessage
from app.models.schemas import ChatRequest, ChatResponse, ReportRequest

logger = logging.getLogger("astrax.assistant")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """Send a message to the AI assistant."""
    session_id = body.session_id or str(uuid.uuid4())

    # Store user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.message,
        context_json=body.context,
    )
    session.add(user_msg)

    # Generate response via LLM
    try:
        response_text = await _generate_response(body.message, session_id, body.context, body.provider)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        response_text = (
            "I apologize, but I'm unable to generate a response right now. "
            "Please check your LLM provider configuration in Settings. "
            f"Error: {str(e)}"
        )

    # Store assistant response
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_text,
    )
    session.add(assistant_msg)

    return ChatResponse(
        session_id=session_id,
        role="assistant",
        content=response_text,
        created_at=datetime.utcnow(),
    )


@router.post("/explain")
async def explain_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get an AI explanation of a candidate detection."""
    from app.db.models import Candidate

    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    context = {
        "type": "explain_candidate",
        "candidate": {
            "x": candidate.x_centroid,
            "y": candidate.y_centroid,
            "confidence": candidate.confidence_score,
            "snr": candidate.snr,
            "motion_speed": candidate.motion_speed,
            "motion_angle": candidate.motion_angle,
            "classification": candidate.classification,
        }
    }

    prompt = (
        f"Explain this astronomical detection candidate:\n"
        f"- Position: ({candidate.x_centroid:.2f}, {candidate.y_centroid:.2f})\n"
        f"- Confidence Score: {candidate.confidence_score:.3f}\n"
        f"- SNR: {candidate.snr or 'N/A'}\n"
        f"- Motion Speed: {candidate.motion_speed or 'N/A'} px/frame\n"
        f"- FWHM: {candidate.fwhm or 'N/A'}\n"
        f"What could this object be? What should the reviewer look for?"
    )

    try:
        response = await _generate_response(prompt, "explain", context)
    except Exception as e:
        response = f"Unable to generate explanation: {str(e)}"

    return {"candidate_id": candidate_id, "explanation": response}


@router.post("/report")
async def generate_report(
    body: ReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate an observation report."""
    # TODO: Implement full report generation with LLM
    return {
        "status": "pending",
        "message": "Report generation not yet implemented",
    }


@router.get("/history")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """Get chat history for a session."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        ChatResponse(
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


async def _generate_response(
    message: str, session_id: str, context: dict = None, provider: str = None
) -> str:
    """Generate an LLM response using the configured provider."""
    # Use requested provider, or fallback to default
    active_provider = provider or settings.llm_provider

    try:
        if active_provider == "gemini":
            if not settings.llm_gemini_api_key: return "Gemini API key missing."
            return await _call_gemini(message, context)
        elif active_provider == "openai":
            if not settings.llm_openai_api_key: return "OpenAI API key missing."
            return await _call_openai(message, context)
        elif active_provider == "anthropic":
            if not settings.llm_anthropic_api_key: return "Anthropic API key missing."
            return await _call_anthropic(message, context)
        elif active_provider == "openrouter":
            if not settings.llm_openrouter_api_key: return "OpenRouter API key missing."
            return await _call_openrouter(message, context)
        elif active_provider == "deepseek":
            if not settings.llm_deepseek_api_key: return "DeepSeek API key missing."
            return await _call_deepseek(message, context)
        elif active_provider == "grok":
            if not settings.llm_grok_api_key: return "Grok API key missing."
            return await _call_grok(message, context)
        else:
            return f"Unknown LLM provider: {active_provider}"
    except Exception as e:
        return f"Provider {active_provider} failed: {str(e)}"


async def _call_gemini(message: str, context: dict = None) -> str:
    """Call Google Gemini API."""
    import google.generativeai as genai

    genai.configure(api_key=settings.llm_gemini_api_key)
    model = genai.GenerativeModel(settings.llm_model or "gemini-2.0-flash")

    system_prompt = _get_system_prompt(context)
    response = model.generate_content(f"{system_prompt}\n\nUser: {message}")
    return response.text


async def _call_openai(message: str, context: dict = None) -> str:
    """Call OpenAI-compatible API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.llm_openai_api_key,
        base_url=settings.llm_base_url or "https://api.openai.com/v1",
    )

    response = await client.chat.completions.create(
        model=settings.llm_model or "gpt-4o",
        messages=[
            {"role": "system", "content": _get_system_prompt(context)},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


async def _call_anthropic(message: str, context: dict = None) -> str:
    """Call Anthropic API."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.llm_anthropic_api_key)
    response = await client.messages.create(
        model=settings.llm_model or "claude-sonnet-4-20250514",
        max_tokens=2048,
        system=_get_system_prompt(context),
        messages=[{"role": "user", "content": message}],
    )
    return response.content[0].text


async def _call_openrouter(message: str, context: dict = None) -> str:
    """Call OpenRouter API (OpenAI-compatible)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.llm_openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    response = await client.chat.completions.create(
        model=settings.llm_model or "anthropic/claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": _get_system_prompt(context)},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


async def _call_deepseek(message: str, context: dict = None) -> str:
    """Call DeepSeek API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.llm_deepseek_api_key,
        base_url="https://api.deepseek.com",
    )

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": _get_system_prompt(context)},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


async def _call_grok(message: str, context: dict = None) -> str:
    """Call Grok (xAI) API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.llm_grok_api_key,
        base_url="https://api.x.ai/v1",
    )

    response = await client.chat.completions.create(
        model="grok-beta",
        messages=[
            {"role": "system", "content": _get_system_prompt(context)},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


def _get_system_prompt(context: dict = None) -> str:
    """Get the system prompt for the AI assistant."""
    base = (
        "You are AstraX AI Assistant, an expert in astronomical observation and image analysis. "
        "You help researchers analyze FITS astronomical datasets, understand detections, "
        "evaluate candidate moving objects, and draft observation reports. "
        "Always be scientifically accurate. When discussing detections, remind users that "
        "AI analysis assists but does not replace scientific validation. "
        "Use clear, professional language appropriate for astronomers and researchers."
    )
    if context:
        base += f"\n\nCurrent context: {context}"
    return base
