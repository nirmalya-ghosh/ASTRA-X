"""
AstraX Engine — FITS File Loader
Memory-mapped FITS reading with header extraction and metadata parsing.
"""

import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger("astrax.engine.io")


@dataclass
class FITSFrame:
    """Represents a single FITS frame with its data and metadata."""
    file_path: str
    index: int = 0
    data: Optional[np.ndarray] = None
    header: dict = field(default_factory=dict)
    width: Optional[int] = None
    height: Optional[int] = None
    bitpix: Optional[int] = None
    exposure_time: Optional[float] = None
    filter_name: Optional[str] = None
    date_obs: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    instrument: Optional[str] = None
    wcs: object = None  # astropy WCS object


@dataclass
class FITSDataset:
    """Represents a collection of FITS frames."""
    name: str
    source_path: str
    frames: list[FITSFrame] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def total_size_bytes(self) -> int:
        return sum(Path(f.file_path).stat().st_size for f in self.frames if Path(f.file_path).exists())


class FITSLoader:
    """
    Memory-mapped FITS file loader.

    Loads FITS files using astropy with memmap=True for efficient
    handling of large datasets. Supports .fits, .fits.gz, and
    multi-extension FITS files.
    """

    EXTENSIONS = {".fits", ".fit", ".fts"}
    COMPRESSED_EXTENSIONS = {".fits.gz", ".fit.gz", ".fts.gz"}

    def __init__(self, memmap: bool = True):
        self.memmap = memmap

    def load_frame(self, file_path: Union[str, Path], extension: int = 0) -> FITSFrame:
        """
        Load a single FITS frame.

        Args:
            file_path: Path to the FITS file
            extension: HDU extension index (default: 0)

        Returns:
            FITSFrame with data and metadata
        """
        from astropy.io import fits

        file_path = str(file_path)
        frame = FITSFrame(file_path=file_path)

        with fits.open(file_path, memmap=self.memmap) as hdul:
            # Find the extension with image data
            hdu = hdul[extension]
            if hdu.data is None and len(hdul) > 1:
                for i, ext in enumerate(hdul):
                    if ext.data is not None and ext.data.ndim >= 2:
                        hdu = ext
                        extension = i
                        break

            header = hdu.header
            data = hdu.data

            if data is not None:
                # Handle 3D+ data (take first slice)
                while data.ndim > 2:
                    data = data[0]
                frame.data = np.array(data, dtype=np.float64)
                frame.height, frame.width = frame.data.shape

            # Extract metadata
            frame.bitpix = header.get("BITPIX")
            frame.exposure_time = header.get("EXPTIME") or header.get("EXPOSURE")
            frame.filter_name = header.get("FILTER") or header.get("FILTNAM")
            frame.date_obs = header.get("DATE-OBS")
            frame.instrument = header.get("INSTRUME")
            frame.ra = header.get("RA") or header.get("CRVAL1")
            frame.dec = header.get("DEC") or header.get("CRVAL2")

            # Store full header
            frame.header = self._header_to_dict(header)

            # Try to extract WCS
            try:
                from astropy.wcs import WCS
                frame.wcs = WCS(header)
            except Exception:
                pass

        return frame

    def load_data(self, file_path: Union[str, Path], extension: int = 0) -> np.ndarray:
        """Load just the image data from a FITS file."""
        from astropy.io import fits

        with fits.open(str(file_path), memmap=self.memmap) as hdul:
            hdu = hdul[extension]
            if hdu.data is None:
                for ext in hdul:
                    if ext.data is not None:
                        hdu = ext
                        break

            data = hdu.data
            if data is None:
                raise ValueError(f"No image data found in {file_path}")

            while data.ndim > 2:
                data = data[0]

            return np.array(data, dtype=np.float64)

    def get_header(self, file_path: Union[str, Path], extension: int = 0) -> dict:
        """Get FITS header as a dictionary."""
        from astropy.io import fits

        with fits.open(str(file_path), memmap=True) as hdul:
            return self._header_to_dict(hdul[extension].header)

    def get_extensions_info(self, file_path: Union[str, Path]) -> list[dict]:
        """Get info about all HDU extensions in a FITS file."""
        from astropy.io import fits

        info = []
        with fits.open(str(file_path), memmap=True) as hdul:
            for i, hdu in enumerate(hdul):
                ext_info = {
                    "index": i,
                    "name": hdu.name,
                    "type": type(hdu).__name__,
                    "has_data": hdu.data is not None,
                }
                if hdu.data is not None:
                    ext_info["shape"] = list(hdu.data.shape)
                    ext_info["dtype"] = str(hdu.data.dtype)
                info.append(ext_info)
        return info

    @staticmethod
    def _header_to_dict(header) -> dict:
        """Convert an astropy FITS header to a plain dictionary."""
        result = {}
        for key in header.keys():
            if key and key not in ("COMMENT", "HISTORY", ""):
                try:
                    val = header[key]
                    if isinstance(val, (int, float, str, bool)):
                        result[key] = val
                    else:
                        result[key] = str(val)
                except Exception:
                    pass
        return result

    @staticmethod
    def is_fits_file(file_path: Union[str, Path]) -> bool:
        """Check if a file is a FITS file by extension."""
        name = str(file_path).lower()
        return any(name.endswith(ext) for ext in
                    FITSLoader.EXTENSIONS | FITSLoader.COMPRESSED_EXTENSIONS)
