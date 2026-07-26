"""
File type helpers shared by dataset indexing and detection routing.
"""

from pathlib import Path

FITS_EXTS = {".fits", ".fit", ".fts", ".fits.gz", ".fit.gz"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
DATA_EXTS = {".csv", ".json", ".tsv", ".xls", ".xlsx", ".parquet"}
SUPPORTED_EXTS = FITS_EXTS | IMAGE_EXTS | DATA_EXTS


def normalized_extension(path: str | Path) -> str:
    """Return the meaningful supported extension, including compressed FITS."""
    name = Path(path).name.lower()
    for ext in sorted(SUPPORTED_EXTS, key=len, reverse=True):
        if name.endswith(ext):
            return ext
    return Path(path).suffix.lower()


def dataset_kind(path: str | Path) -> str:
    """Classify a supported dataset file as fits, image, data, zip, or unknown."""
    ext = normalized_extension(path)
    if ext in FITS_EXTS:
        return "fits"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in DATA_EXTS:
        return "data"
    if ext == ".zip":
        return "zip"
    return "unknown"


def is_supported_file(path: str | Path) -> bool:
    return normalized_extension(path) in SUPPORTED_EXTS
