"""
AstraX AI — Settings API Router
"""

import logging
from fastapi import APIRouter
from app.config import settings
from app.models.schemas import AppSettingsResponse, AppSettingsUpdate

logger = logging.getLogger("astrax.settings")
router = APIRouter()


@router.get("", response_model=AppSettingsResponse)
async def get_settings():
    """Get current application settings."""
    return AppSettingsResponse(
        gpu_enabled=settings.gpu_enabled,
        max_workers=settings.max_workers,
        detection_fwhm=settings.detection_fwhm,
        detection_threshold_sigma=settings.detection_threshold_sigma,
        motion_threshold=settings.motion_threshold,
        confidence_threshold=settings.confidence_threshold,
        noise_sigma_clip=settings.noise_sigma_clip,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )


@router.patch("", response_model=AppSettingsResponse)
async def update_settings(body: AppSettingsUpdate):
    """Update application settings (runtime only, does not persist to .env)."""
    if body.gpu_enabled is not None:
        settings.gpu_enabled = body.gpu_enabled
    if body.max_workers is not None:
        settings.max_workers = body.max_workers
    if body.detection_fwhm is not None:
        settings.detection_fwhm = body.detection_fwhm
    if body.detection_threshold_sigma is not None:
        settings.detection_threshold_sigma = body.detection_threshold_sigma
    if body.motion_threshold is not None:
        settings.motion_threshold = body.motion_threshold
    if body.confidence_threshold is not None:
        settings.confidence_threshold = body.confidence_threshold
    if body.noise_sigma_clip is not None:
        settings.noise_sigma_clip = body.noise_sigma_clip
    if body.llm_provider is not None:
        settings.llm_provider = body.llm_provider
    if body.llm_model is not None:
        settings.llm_model = body.llm_model

    return await get_settings()
