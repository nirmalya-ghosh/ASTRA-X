"""
AstraX AI — Pydantic Response/Request Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Dataset Schemas ──────────────────────────────────────────────

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_path: Optional[str] = None


class DatasetImportFolder(BaseModel):
    path: str = Field(..., min_length=1, description="Local filesystem path to import")
    name: Optional[str] = None
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source_path: str
    status: str
    file_count: int
    total_size_bytes: int
    metadata_json: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int


# ── Frame Schemas ────────────────────────────────────────────────

class FrameResponse(BaseModel):
    id: int
    dataset_id: int
    filename: str
    frame_index: int
    width: Optional[int]
    height: Optional[int]
    bitpix: Optional[int]
    exposure_time: Optional[float]
    filter_name: Optional[str]
    date_obs: Optional[str]
    ra: Optional[float]
    dec: Optional[float]
    instrument: Optional[str]
    status: str
    preview_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FrameHeaderResponse(BaseModel):
    frame_id: int
    filename: str
    headers: dict


# ── Candidate Schemas ────────────────────────────────────────────

class CandidateResponse(BaseModel):
    id: int
    frame_id: int
    dataset_id: int
    x_centroid: float
    y_centroid: float
    ra: Optional[float]
    dec: Optional[float]
    bbox_x: Optional[int]
    bbox_y: Optional[int]
    bbox_w: Optional[int]
    bbox_h: Optional[int]
    flux: Optional[float]
    magnitude: Optional[float]
    snr: Optional[float]
    fwhm: Optional[float]
    sharpness: Optional[float]
    roundness: Optional[float]
    motion_dx: Optional[float]
    motion_dy: Optional[float]
    motion_speed: Optional[float]
    motion_angle: Optional[float]
    confidence_score: float
    risk_score: float
    persistence_score: float
    detection_count: int
    classification: str
    object_type: Optional[str]
    notes: Optional[str]
    detection_method: Optional[str]
    metadata_json: Optional[dict]
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CandidateReview(BaseModel):
    classification: str = Field(..., pattern="^(confirmed|rejected|flagged|unreviewed)$")
    object_type: Optional[str] = None
    notes: Optional[str] = None


class CandidateListResponse(BaseModel):
    candidates: list[CandidateResponse]
    total: int
    page: int
    page_size: int


# ── Processing Schemas ───────────────────────────────────────────

class ProcessingStep(BaseModel):
    name: str
    enabled: bool = True
    params: Optional[dict] = None


class ProcessingRequest(BaseModel):
    dataset_id: int
    steps: list[ProcessingStep] = []


class DetectionRequest(BaseModel):
    dataset_id: int
    fwhm: float = 3.0
    threshold_sigma: float = 5.0
    motion_threshold: float = 2.0
    min_persistence: int = 2
    enable_motion_detection: bool = True
    enable_false_positive_filter: bool = True


class TaskStatusResponse(BaseModel):
    id: int
    task_type: str
    status: str
    progress: float
    message: Optional[str]
    result_json: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── AI Assistant Schemas ─────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    context: Optional[dict] = None  # e.g., current dataset/candidate info
    provider: Optional[str] = None  # openrouter, deepseek, openai, gemini, grok


class ChatResponse(BaseModel):
    session_id: str
    role: str
    content: str
    created_at: datetime


class ReportRequest(BaseModel):
    dataset_id: int
    candidate_ids: Optional[list[int]] = None
    report_type: str = "observation_log"  # observation_log, scientific_report, summary
    format: str = "markdown"  # markdown, pdf


# ── Export Schemas ───────────────────────────────────────────────

class ExportRequest(BaseModel):
    dataset_id: int
    format: str = "csv"  # csv, json, pdf, png, zip
    candidate_ids: Optional[list[int]] = None
    include_images: bool = False
    include_metadata: bool = True


class ExportResponse(BaseModel):
    task_id: int
    format: str
    status: str
    download_url: Optional[str] = None


# ── Settings Schemas ─────────────────────────────────────────────

class AppSettingsResponse(BaseModel):
    gpu_enabled: bool
    max_workers: int
    detection_fwhm: float
    detection_threshold_sigma: float
    motion_threshold: float
    confidence_threshold: float
    noise_sigma_clip: float
    llm_provider: Optional[str]
    llm_model: Optional[str]


class AppSettingsUpdate(BaseModel):
    gpu_enabled: Optional[bool] = None
    max_workers: Optional[int] = Field(None, ge=1, le=32)
    detection_fwhm: Optional[float] = Field(None, gt=0)
    detection_threshold_sigma: Optional[float] = Field(None, gt=0)
    motion_threshold: Optional[float] = Field(None, gt=0)
    confidence_threshold: Optional[float] = Field(None, ge=0, le=1)
    noise_sigma_clip: Optional[float] = Field(None, gt=0)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


# ── General ──────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    gpu_available: bool
    datasets_count: int
    candidates_count: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
