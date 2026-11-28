"""Background worker for long-running Cartoon Studio operations.

The HTTP routes used to claim a job and then run the Godot/FFmpeg work inside
the request, so the browser waited for hours, a closed tab left the work
running, and cancellation could not interrupt anything. This worker runs the
same work in a background thread instead:

- the route enqueues the job and returns its id (``202``);
- ``OperationWorker`` claims it, executes the registered handler, and records
  completion or failure;
- the handler reports progress and checks cancellation between units, so a
  cancelled job stops before the next scene instead of after the whole render.

The worker is deliberately small: one thread, one claimed job at a time, and a
lease covering the operation's budget. It does not run a second job in parallel
because the target hardware (8 GB RAM, integrated GPU) is the constraint that
made the queue sequential in the first place.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.job_queue import JobQueue, JobQueueError

DEFAULT_LEASE_SECONDS = 4 * 3600.0
DEFAULT_POLL_SECONDS = 1.0


class OperationCancelled(RuntimeError):
    """Raised by a handler when the owner cancelled the running job."""


@dataclass
class JobContext:
    """What a handler may do with the job it is running."""

    queue: JobQueue
    job_id: str
    project_id: str
    worker_id: str

    def report(self, progress: int, total: int | None = None) -> None:
        """Persist progress; raise OperationCancelled once cancellation is requested.

        The cancellation check comes first so a cancelled job never advances its
        reported progress after the owner has asked it to stop.
        """
        if self.queue.cancel_requested(self.job_id):
            raise OperationCancelled("The owner cancelled this job.")
        if not self.queue.report_progress(
            self.job_id, self.worker_id, progress, total=total
        ):
            raise OperationCancelled("The job is no longer owned by this worker.")

    def cancelled(self) -> bool:
        """Return whether the owner has requested cancellation."""
        return self.queue.cancel_requested(self.job_id)


Handler = Callable[[JobContext], dict[str, Any] | None]


class OperationWorker:
    """Run queued operations in one background thread."""

    def __init__(
        self,
        queue: JobQueue,
        handlers: dict[str, Handler],
        worker_id: str = "background-worker",
        lease_seconds: float = DEFAULT_LEASE_SECONDS,
        poll_seconds: float = DEFAULT_POLL_SECONDS,
    ) -> None:
        self.queue = queue
        self.handlers = dict(handlers)
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.poll_seconds = poll_seconds
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._wake = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def register(self, operation: str, handler: Handler) -> None:
        self.handlers[operation] = handler

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="cartoon-studio-worker", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        self._wake.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
        self._thread = None

    def wake(self) -> None:
        """Ask the loop to look for a queued job immediately."""
        self._wake.set()

    def run_once(self) -> bool:
        """Claim and run at most one job; returns True when one was handled."""
        job = self.queue.claim_next(
            self.worker_id, lease_seconds=self.lease_seconds
        )
        if job is None:
            return False
        job_id = str(job["job_id"])
        operation = str(job["operation"])
        handler = self.handlers.get(operation)
        if handler is None:
            self.queue.fail(
                job_id,
                self.worker_id,
                f"No background handler is registered for {operation}.",
                retry=False,
            )
            return True
        context = JobContext(
            queue=self.queue,
            job_id=job_id,
            project_id=str(job["project_id"]),
            worker_id=self.worker_id,
        )
        try:
            output = handler(context) or {}
        except OperationCancelled as error:
            try:
                self.queue.mark_cancelled(job_id, self.worker_id, reason=str(error))
            except JobQueueError:
                # The job was cancelled or reclaimed meanwhile; nothing to record.
                pass
        except Exception as error:  # noqa: BLE001 - one job must not stop the worker
            try:
                self.queue.fail(
                    job_id, self.worker_id, f"{type(error).__name__}: {error}"
                )
            except JobQueueError:
                pass
        else:
            try:
                self.queue.complete(job_id, self.worker_id, output=output)
            except JobQueueError:
                pass
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self.run_once():
                continue
            self._wake.wait(self.poll_seconds)
            self._wake.clear()
