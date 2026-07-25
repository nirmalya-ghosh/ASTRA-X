"""
AstraX Engine — GPU Acceleration
Transparent fallback between CuPy (GPU) and NumPy (CPU).
"""

import logging
import numpy as np
from functools import wraps

logger = logging.getLogger("astrax.engine.gpu")

# Try importing CuPy
try:
    import cupy as cp
    GPU_AVAILABLE = True
    logger.info("CuPy detected — GPU acceleration available")
except ImportError:
    GPU_AVAILABLE = False
    logger.info("CuPy not found — using NumPy (CPU) for all operations")


def get_array_module(gpu_enabled: bool = True):
    """Get the appropriate array module (CuPy or NumPy)."""
    if gpu_enabled and GPU_AVAILABLE:
        return cp
    return np


def to_gpu(data: np.ndarray) -> "np.ndarray | cp.ndarray":
    """Transfer array to GPU if available."""
    if GPU_AVAILABLE:
        return cp.asarray(data)
    return data


def to_cpu(data) -> np.ndarray:
    """Transfer array back to CPU."""
    if GPU_AVAILABLE and hasattr(data, 'get'):
        return data.get()
    return np.asarray(data)


def gpu_accelerated(fallback_to_cpu: bool = True):
    """
    Decorator that attempts GPU execution with CPU fallback.

    Usage:
        @gpu_accelerated()
        def my_function(data, xp=np):
            return xp.fft.fft2(data)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if GPU_AVAILABLE and kwargs.get('gpu', True):
                try:
                    # Try GPU execution
                    gpu_args = [to_gpu(a) if isinstance(a, np.ndarray) else a for a in args]
                    kwargs['xp'] = cp
                    result = func(*gpu_args, **kwargs)
                    return to_cpu(result) if isinstance(result, cp.ndarray) else result
                except Exception as e:
                    if fallback_to_cpu:
                        logger.warning(f"GPU execution failed, falling back to CPU: {e}")
                    else:
                        raise

            kwargs['xp'] = np
            kwargs.pop('gpu', None)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def gpu_info() -> dict:
    """Get GPU information."""
    if not GPU_AVAILABLE:
        return {"available": False, "reason": "CuPy not installed"}

    try:
        device = cp.cuda.Device(0)
        mem_info = device.mem_info
        return {
            "available": True,
            "device_name": str(device),
            "compute_capability": device.compute_capability,
            "total_memory_mb": round(mem_info[1] / 1024 / 1024, 1),
            "free_memory_mb": round(mem_info[0] / 1024 / 1024, 1),
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}
