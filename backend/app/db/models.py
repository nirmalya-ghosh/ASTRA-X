"""
AstraX AI — Database Models and Engine Setup
SQLAlchemy async with SQLite for local-first execution.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Text, Boolean, DateTime, JSON,
    ForeignKey, Index
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)
from app.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Dataset(Base):
    """Represents an imported astronomical dataset."""
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, indexing, ready, error
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    frames: Mapped[list["Frame"]] = relationship("Frame", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_datasets_status", "status"),
        Index("idx_datasets_created", "created_at"),
    )


class Frame(Base):
    """Represents a single FITS frame within a dataset."""
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bitpix: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    naxis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exposure_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    filter_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_obs: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ra: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    instrument: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    header_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preview_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="raw")  # raw, calibrated, processed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="frames")
    candidates: Mapped[list["Candidate"]] = relationship("Candidate", back_populates="frame", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_frames_dataset", "dataset_id"),
        Index("idx_frames_status", "status"),
    )


class Candidate(Base):
    """Represents a detected moving-object candidate."""
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    frame_id: Mapped[int] = mapped_column(Integer, ForeignKey("frames.id"), nullable=False)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id"), nullable=False)

    # Position
    x_centroid: Mapped[float] = mapped_column(Float, nullable=False)
    y_centroid: Mapped[float] = mapped_column(Float, nullable=False)
    ra: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bbox_w: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bbox_h: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Photometry
    flux: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    magnitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    snr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fwhm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sharpness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roundness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Motion
    motion_dx: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion_dy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion_angle: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trajectory_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Scoring
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    persistence_score: Mapped[float] = mapped_column(Float, default=0.0)
    detection_count: Mapped[int] = mapped_column(Integer, default=1)

    # Classification
    classification: Mapped[str] = mapped_column(String(50), default="unreviewed")  # unreviewed, confirmed, rejected, flagged
    object_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # asteroid, comet, satellite, artifact, unknown
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    detection_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    frame: Mapped["Frame"] = relationship("Frame", back_populates="candidates")

    __table_args__ = (
        Index("idx_candidates_dataset", "dataset_id"),
        Index("idx_candidates_frame", "frame_id"),
        Index("idx_candidates_confidence", "confidence_score"),
        Index("idx_candidates_classification", "classification"),
    )


class ProcessingTask(Base):
    """Tracks background processing tasks."""
    __tablename__ = "processing_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # index, calibrate, detect, export
    dataset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("datasets.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 - 1.0
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_type", "task_type"),
    )


class ChatMessage(Base):
    """Stores AI assistant chat messages."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_chat_session", "session_id"),
    )


# Database engine and session factory
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=connect_args,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
