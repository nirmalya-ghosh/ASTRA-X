"""
AstraX AI — Dataset API Router
Handles dataset upload, import, listing, and frame access.
"""

import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import get_session, Dataset, Frame
from app.models.schemas import (
    DatasetResponse, DatasetListResponse, DatasetImportFolder,
    FrameResponse, FrameHeaderResponse
)

logger = logging.getLogger("astrax.datasets")
router = APIRouter()


async def _index_dataset(dataset_id: int, source_path: str):
    """Background task: Index a dataset folder and populate frames."""
    from app.db.models import async_session, Dataset, Frame

    try:
        async with async_session() as session:
            # Update status
            dataset = await session.get(Dataset, dataset_id)
            if not dataset:
                return
            dataset.status = "indexing"
            await session.commit()

            # Scan for files
            source = Path(source_path)
            target_files = []

            # Supported extensions mapping
            fits_exts = {".fits", ".fit", ".fts", ".fits.gz", ".fit.gz"}
            img_exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
            data_exts = {".csv", ".json"}
            all_exts = fits_exts | img_exts | data_exts

            if source.is_file():
                if source.suffix.lower() in all_exts:
                    target_files.append(source)
                elif source.suffix.lower() == ".zip":
                    # Extract ZIP
                    import zipfile
                    extract_dir = settings.upload_dir / str(dataset_id)
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(source, 'r') as zf:
                        zf.extractall(extract_dir)
                    for root, _, files in os.walk(extract_dir):
                        for f in files:
                            if Path(f).suffix.lower() in all_exts:
                                target_files.append(Path(root) / f)
            elif source.is_dir():
                for root, _, files in os.walk(source):
                    for f in files:
                        if Path(f).suffix.lower() in all_exts:
                            target_files.append(Path(root) / f)

            target_files.sort(key=lambda p: p.name)
            total_size = sum(f.stat().st_size for f in target_files)

            try:
                from astropy.io import fits as astropy_fits
                has_astropy = True
            except ImportError:
                has_astropy = False

            try:
                from PIL import Image
                has_pil = True
            except ImportError:
                has_pil = False

            for idx, fpath in enumerate(target_files):
                frame = Frame(
                    dataset_id=dataset_id,
                    filename=fpath.name,
                    file_path=str(fpath.resolve()),
                    frame_index=idx,
                )

                ext = fpath.suffix.lower()
                header_dict = {"file_type": "unknown"}

                if ext in fits_exts and has_astropy:
                    header_dict["file_type"] = "fits"
                    try:
                        with astropy_fits.open(str(fpath), memmap=True) as hdul:
                            hdr = hdul[0].header
                            data = hdul[0].data

                            if data is not None:
                                frame.width = data.shape[-1] if len(data.shape) >= 2 else None
                                frame.height = data.shape[-2] if len(data.shape) >= 2 else None

                            frame.bitpix = hdr.get("BITPIX")
                            frame.naxis = hdr.get("NAXIS")
                            frame.exposure_time = hdr.get("EXPTIME") or hdr.get("EXPOSURE")
                            frame.filter_name = hdr.get("FILTER") or hdr.get("FILTNAM")
                            frame.date_obs = hdr.get("DATE-OBS")
                            frame.instrument = hdr.get("INSTRUME")
                            frame.ra = hdr.get("RA") or hdr.get("CRVAL1")
                            frame.dec = hdr.get("DEC") or hdr.get("CRVAL2")

                            for key in hdr.keys():
                                if key and key != "COMMENT" and key != "HISTORY":
                                    try:
                                        val = hdr[key]
                                        if isinstance(val, (int, float, str, bool)):
                                            header_dict[key] = val
                                        else:
                                            header_dict[key] = str(val)
                                    except Exception:
                                        pass
                    except Exception as e:
                        logger.error(f"Error reading FITS header for {fpath}: {e}")

                elif ext in img_exts and has_pil:
                    header_dict["file_type"] = "image"
                    try:
                        with Image.open(fpath) as img:
                            frame.width, frame.height = img.size
                            header_dict["format"] = img.format
                            header_dict["mode"] = img.mode
                            exif = img.getexif()
                            if exif:
                                for k, v in exif.items():
                                    header_dict[f"exif_{k}"] = str(v)
                    except Exception as e:
                        logger.error(f"Error reading image metadata for {fpath}: {e}")
                
                elif ext in data_exts:
                    header_dict["file_type"] = "data"
                    try:
                        file_size = fpath.stat().st_size
                        header_dict["size_bytes"] = file_size
                        if ext == ".csv":
                            with open(fpath, 'r', encoding='utf-8') as f:
                                first_line = f.readline()
                                header_dict["columns"] = first_line.strip().split(',')
                    except Exception as e:
                        logger.error(f"Error reading data file metadata for {fpath}: {e}")

                frame.header_json = header_dict
                session.add(frame)

            # Update dataset
            dataset.file_count = len(target_files)
            dataset.total_size_bytes = total_size
            dataset.status = "ready" if target_files else "empty"

            # Collect metadata
            dataset.metadata_json = {
                "file_count": len(target_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "extensions_found": list(set(f.suffix.lower() for f in target_files)),
            }

            await session.commit()
            logger.info(f"Dataset {dataset_id} indexed: {len(target_files)} files, {total_size / 1024 / 1024:.1f} MB")

    except Exception as e:
        logger.error(f"Error indexing dataset {dataset_id}: {e}")
        try:
            async with async_session() as session:
                dataset = await session.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = "error"
                    await session.commit()
        except Exception:
            pass


@router.post("", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
):
    """Upload a FITS file or ZIP archive."""
    upload_id = str(uuid.uuid4())
    upload_path = settings.upload_dir / upload_id
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / file.filename

    # Stream file to disk
    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(settings.chunk_size):
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    dataset = Dataset(
        name=name or file.filename,
        description=description,
        source_path=str(file_path),
        status="pending",
    )
    session.add(dataset)
    await session.flush()

    # Index in background
    background_tasks.add_task(_index_dataset, dataset.id, str(file_path))

    return dataset


@router.post("/import-folder", response_model=DatasetResponse, status_code=201)
async def import_folder(
    body: DatasetImportFolder,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Import a dataset from a local filesystem path."""
    source = Path(body.path)
    if not source.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {body.path}")

    dataset = Dataset(
        name=body.name or source.name,
        description=body.description,
        source_path=str(source.resolve()),
        status="pending",
    )
    session.add(dataset)
    await session.flush()

    background_tasks.add_task(_index_dataset, dataset.id, str(source.resolve()))

    return dataset


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """List all datasets with optional filtering."""
    query = select(Dataset).order_by(Dataset.created_at.desc())
    count_query = select(func.count(Dataset.id))

    if status:
        query = query.where(Dataset.status == status)
        count_query = count_query.where(Dataset.status == status)

    total = (await session.execute(count_query)).scalar() or 0
    result = await session.execute(query.offset(skip).limit(limit))
    datasets = result.scalars().all()

    return DatasetListResponse(datasets=datasets, total=total)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get dataset details."""
    dataset = await session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/frames", response_model=list[FrameResponse])
async def list_frames(
    dataset_id: int,
    session: AsyncSession = Depends(get_session),
):
    """List all frames in a dataset."""
    result = await session.execute(
        select(Frame)
        .where(Frame.dataset_id == dataset_id)
        .order_by(Frame.frame_index)
    )
    return result.scalars().all()


@router.get("/{dataset_id}/frames/{frame_index}/header", response_model=FrameHeaderResponse)
async def get_frame_header(
    dataset_id: int,
    frame_index: int,
    session: AsyncSession = Depends(get_session),
):
    """Get FITS header for a specific frame."""
    result = await session.execute(
        select(Frame)
        .where(Frame.dataset_id == dataset_id, Frame.frame_index == frame_index)
    )
    frame = result.scalar_one_or_none()
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    return FrameHeaderResponse(
        frame_id=frame.id,
        filename=frame.filename,
        headers=frame.header_json or {},
    )


@router.get("/{dataset_id}/frames/{frame_index}/preview")
async def get_frame_preview(
    dataset_id: int,
    frame_index: int,
    stretch: str = "zscale",
    colormap: str = "gray",
    session: AsyncSession = Depends(get_session),
):
    """Get a rendered PNG preview of a FITS frame."""
    from fastapi.responses import StreamingResponse
    import io

    result = await session.execute(
        select(Frame)
        .where(Frame.dataset_id == dataset_id, Frame.frame_index == frame_index)
    )
    frame = result.scalar_one_or_none()
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    try:
        from astropy.io import fits as astropy_fits
        from astropy.visualization import ZScaleInterval, MinMaxInterval, AsinhStretch, LinearStretch
        import numpy as np
        from PIL import Image

        with astropy_fits.open(frame.file_path, memmap=True) as hdul:
            data = hdul[0].data
            if data is None:
                # Try first extension with data
                for ext in hdul:
                    if ext.data is not None:
                        data = ext.data
                        break

            if data is None:
                raise HTTPException(status_code=422, detail="No image data in FITS file")

            # Handle 3D+ data (take first slice)
            while len(data.shape) > 2:
                data = data[0]

            data = data.astype(np.float64)

            # Apply stretch
            if stretch == "zscale":
                interval = ZScaleInterval()
            else:
                interval = MinMaxInterval()

            vmin, vmax = interval.get_limits(data)
            data = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)

            # Convert to 8-bit image
            img_data = (data * 255).astype(np.uint8)
            img = Image.fromarray(img_data, mode='L')

            # Apply colormap if not gray
            if colormap != "gray":
                try:
                    import matplotlib.cm as cm
                    cmap = cm.get_cmap(colormap)
                    colored = cmap(data)
                    img_data = (colored[:, :, :3] * 255).astype(np.uint8)
                    img = Image.fromarray(img_data, mode='RGB')
                except Exception:
                    pass

            # Encode to PNG
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)

            return StreamingResponse(buffer, media_type="image/png")

    except ImportError:
        raise HTTPException(status_code=500, detail="astropy/Pillow not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a dataset and its frames."""
    dataset = await session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Clean up uploaded files
    upload_path = settings.upload_dir / str(dataset_id)
    if upload_path.exists():
        shutil.rmtree(upload_path)

    await session.delete(dataset)
