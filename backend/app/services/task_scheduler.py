"""
Small helper for starting in-process coroutine background jobs.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import BackgroundTasks

logger = logging.getLogger("astrax.task_scheduler")


def schedule_coroutine(
    background_tasks: BackgroundTasks,
    func: Callable[..., Awaitable[Any]],
    *args: Any,
) -> None:
    """
    Start an async background job immediately when an event loop is running.

    FastAPI's BackgroundTasks are usually fine, but starting the coroutine on the
    active loop avoids tasks sitting in "pending" until the response lifecycle
    finishes or a background callback is skipped by a deployment edge case.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        background_tasks.add_task(func, *args)
        return

    task = loop.create_task(func(*args))

    def log_failure(done: asyncio.Task[Any]) -> None:
        try:
            done.result()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Background coroutine task failed")

    task.add_done_callback(log_failure)
