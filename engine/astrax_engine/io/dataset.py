"""
AstraX Engine — Dataset Indexer
Scans folders for FITS files, detects observation sequences, groups frames.
"""

import os
import logging
from pathlib import Path
from typing import Union
from dataclasses import dataclass, field

from astrax_engine.io.fits_loader import FITSLoader, FITSFrame, FITSDataset

logger = logging.getLogger("astrax.engine.io.dataset")


@dataclass
class ObservationGroup:
    """A group of frames from the same observation sequence."""
    name: str
    filter_name: str = ""
    target: str = ""
    frames: list[FITSFrame] = field(default_factory=list)
    date_start: str = ""
    date_end: str = ""


class DatasetIndexer:
    """
    Indexes a folder of FITS files into a structured dataset.

    Capabilities:
    - Recursive directory scanning
    - ZIP archive extraction
    - Observation sequence detection (by filter, date, target)
    - Frame grouping
    - Metadata aggregation
    """

    def __init__(self, loader: FITSLoader = None):
        self.loader = loader or FITSLoader(memmap=True)

    def scan_directory(self, path: Union[str, Path]) -> list[Path]:
        """Recursively scan for FITS files in a directory."""
        path = Path(path)
        fits_files = []

        if path.is_file():
            if self.loader.is_fits_file(path):
                fits_files.append(path)
            elif path.suffix.lower() == ".zip":
                fits_files.extend(self._extract_zip(path))
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for f in sorted(files):
                    fpath = Path(root) / f
                    if self.loader.is_fits_file(fpath):
                        fits_files.append(fpath)

        fits_files.sort(key=lambda p: p.name)
        logger.info(f"Found {len(fits_files)} FITS files in {path}")
        return fits_files

    def index_dataset(
        self,
        path: Union[str, Path],
        name: str = None,
        load_data: bool = False,
    ) -> FITSDataset:
        """
        Index a directory into a FITSDataset.

        Args:
            path: Directory or file path
            name: Dataset name (defaults to directory name)
            load_data: Whether to load image data (False = headers only)

        Returns:
            FITSDataset with all frames indexed
        """
        path = Path(path)
        fits_files = self.scan_directory(path)

        dataset = FITSDataset(
            name=name or path.name,
            source_path=str(path.resolve()),
        )

        for idx, fpath in enumerate(fits_files):
            try:
                if load_data:
                    frame = self.loader.load_frame(fpath)
                else:
                    # Header-only mode for fast indexing
                    frame = FITSFrame(file_path=str(fpath), index=idx)
                    frame.header = self.loader.get_header(fpath)
                    self._extract_metadata(frame)

                frame.index = idx
                dataset.frames.append(frame)
            except Exception as e:
                logger.error(f"Error indexing {fpath}: {e}")

        # Aggregate metadata
        dataset.metadata = self._aggregate_metadata(dataset)
        logger.info(f"Indexed dataset '{dataset.name}': {dataset.frame_count} frames")

        return dataset

    def group_by_filter(self, dataset: FITSDataset) -> list[ObservationGroup]:
        """Group frames by filter name."""
        groups = {}
        for frame in dataset.frames:
            key = frame.filter_name or "unknown"
            if key not in groups:
                groups[key] = ObservationGroup(name=key, filter_name=key)
            groups[key].frames.append(frame)
        return list(groups.values())

    def detect_sequences(self, dataset: FITSDataset) -> list[ObservationGroup]:
        """Detect observation sequences by time and pointing."""
        # Simple grouping: consecutive frames with same filter
        sequences = []
        current_group = None

        for frame in dataset.frames:
            filter_key = frame.filter_name or "unknown"

            if current_group is None or current_group.filter_name != filter_key:
                if current_group and current_group.frames:
                    sequences.append(current_group)
                current_group = ObservationGroup(
                    name=f"Sequence {len(sequences) + 1} ({filter_key})",
                    filter_name=filter_key,
                )

            current_group.frames.append(frame)

        if current_group and current_group.frames:
            sequences.append(current_group)

        return sequences

    def _extract_metadata(self, frame: FITSFrame) -> None:
        """Extract metadata from header dict into frame attributes."""
        h = frame.header
        frame.bitpix = h.get("BITPIX")
        frame.exposure_time = h.get("EXPTIME") or h.get("EXPOSURE")
        frame.filter_name = h.get("FILTER") or h.get("FILTNAM")
        frame.date_obs = h.get("DATE-OBS")
        frame.instrument = h.get("INSTRUME")
        frame.ra = h.get("RA") or h.get("CRVAL1")
        frame.dec = h.get("DEC") or h.get("CRVAL2")

        naxis1 = h.get("NAXIS1")
        naxis2 = h.get("NAXIS2")
        if naxis1 and naxis2:
            frame.width = int(naxis1)
            frame.height = int(naxis2)

    def _aggregate_metadata(self, dataset: FITSDataset) -> dict:
        """Aggregate metadata across all frames."""
        filters = set()
        instruments = set()
        dates = []
        exposures = []

        for f in dataset.frames:
            if f.filter_name:
                filters.add(f.filter_name)
            if f.instrument:
                instruments.add(f.instrument)
            if f.date_obs:
                dates.append(f.date_obs)
            if f.exposure_time:
                exposures.append(f.exposure_time)

        return {
            "frame_count": dataset.frame_count,
            "filters": sorted(filters),
            "instruments": sorted(instruments),
            "date_range": [min(dates), max(dates)] if dates else [],
            "exposure_times": sorted(set(exposures)),
        }

    def _extract_zip(self, zip_path: Path) -> list[Path]:
        """Extract FITS files from a ZIP archive."""
        import zipfile
        import tempfile

        extract_dir = zip_path.parent / f"{zip_path.stem}_extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        fits_files = []
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if self.loader.is_fits_file(info.filename) and not info.is_dir():
                    zf.extract(info, extract_dir)
                    fits_files.append(extract_dir / info.filename)

        return sorted(fits_files)
