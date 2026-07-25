"""
AstraX AI — Candidates API Router
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import get_session, Candidate
from app.models.schemas import CandidateResponse, CandidateListResponse, CandidateReview

logger = logging.getLogger("astrax.candidates")
router = APIRouter()


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    dataset_id: Optional[int] = None,
    classification: Optional[str] = None,
    min_confidence: Optional[float] = None,
    sort_by: str = Query("confidence_score", pattern="^(confidence_score|created_at|snr|magnitude)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List candidates with filtering, sorting, and pagination."""
    query = select(Candidate)
    count_query = select(func.count(Candidate.id))

    if dataset_id:
        query = query.where(Candidate.dataset_id == dataset_id)
        count_query = count_query.where(Candidate.dataset_id == dataset_id)
    if classification:
        query = query.where(Candidate.classification == classification)
        count_query = count_query.where(Candidate.classification == classification)
    if min_confidence is not None:
        query = query.where(Candidate.confidence_score >= min_confidence)
        count_query = count_query.where(Candidate.confidence_score >= min_confidence)

    # Sorting
    sort_col = getattr(Candidate, sort_by)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = (await session.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    result = await session.execute(query.offset(offset).limit(page_size))

    return CandidateListResponse(
        candidates=result.scalars().all(),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get detailed candidate information."""
    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def review_candidate(
    candidate_id: int,
    body: CandidateReview,
    session: AsyncSession = Depends(get_session),
):
    """Review/classify a candidate."""
    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.classification = body.classification
    if body.object_type is not None:
        candidate.object_type = body.object_type
    if body.notes is not None:
        candidate.notes = body.notes
    candidate.reviewed_at = datetime.utcnow()

    return candidate


@router.post("/bulk-review")
async def bulk_review(
    candidate_ids: list[int],
    classification: str,
    session: AsyncSession = Depends(get_session),
):
    """Bulk review multiple candidates."""
    updated = 0
    for cid in candidate_ids:
        candidate = await session.get(Candidate, cid)
        if candidate:
            candidate.classification = classification
            candidate.reviewed_at = datetime.utcnow()
            updated += 1

    return {"updated": updated}

@router.post("/{candidate_id}/classify-ai", response_model=CandidateResponse)
async def ai_classify_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Use AI (OpenRouter) to analyze and classify a candidate based on its metrics."""
    from app.config import settings
    from openai import AsyncOpenAI
    
    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    if settings.llm_provider != "openrouter" or not settings.llm_api_key:
        raise HTTPException(status_code=500, detail="OpenRouter AI is not configured")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.llm_api_key,
    )
    
    prompt = f"""
    You are an expert astronomical AI classifier. Analyze the following candidate detection metrics and classify it as either 'confirmed' (likely real asteroid/object) or 'rejected' (likely artifact/noise).
    
    Metrics:
    - Confidence Score: {candidate.confidence_score}
    - Motion Speed (px/hr): {candidate.motion_speed}
    - Flux: {candidate.flux}
    - SNR: {candidate.snr}
    
    Respond ONLY with a JSON object in this format: {{"classification": "confirmed" | "rejected", "notes": "brief reason why"}}
    """
    
    try:
        response = await client.chat.completions.create(
            model="anthropic/claude-3-haiku-20240307", # OpenRouter fast model
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        result = json.loads(response.choices[0].message.content)
        
        candidate.classification = result.get("classification", "flagged")
        candidate.notes = f"AI Analysis: {result.get('notes', 'No reason provided.')}"
        candidate.reviewed_at = datetime.utcnow()
        await session.commit()
        
        return candidate
    except Exception as e:
        logger.error(f"AI Classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI Classification failed: {str(e)}")
