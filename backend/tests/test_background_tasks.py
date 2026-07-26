import os

os.environ["ASTRAX_DATABASE_URL"] = "sqlite+aiosqlite:///./test_background_tasks.db"

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from sqlalchemy import select

from app.api.v1.datasets import _index_dataset
from app.api.v1.detection import run_detection
from app.db.models import Base, Dataset, Frame, ProcessingTask, async_session, engine
from app.models.schemas import DetectionRequest


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_index_dataset_background_task_uses_independent_session(tmp_path):
    source = tmp_path / "rows.csv"
    source.write_text("x,y\n1,2\n", encoding="utf-8")

    async with async_session() as session:
        dataset = Dataset(name="CSV", source_path=str(source), status="pending")
        session.add(dataset)
        await session.commit()
        dataset_id = dataset.id

    await _index_dataset(dataset_id, str(source))

    async with async_session() as session:
        dataset = await session.get(Dataset, dataset_id)
        frames = (
            await session.execute(select(Frame).where(Frame.dataset_id == dataset_id))
        ).scalars().all()

    assert dataset.status == "ready"
    assert dataset.file_count == 1
    assert len(frames) == 1
    assert frames[0].header_json["file_type"] == "data"


@pytest.mark.asyncio
async def test_run_detection_commits_task_before_background_dispatch():
    async with async_session() as session:
        dataset = Dataset(name="Ready", source_path="unused.csv", status="ready")
        session.add(dataset)
        await session.commit()

        background_tasks = BackgroundTasks()
        response = await run_detection(
            DetectionRequest(dataset_id=dataset.id),
            background_tasks,
            session,
        )

        task = await session.get(ProcessingTask, response.id)

    assert task is not None
    assert task.status == "pending"
    assert task.task_type == "detection"
    assert len(background_tasks.tasks) == 1
