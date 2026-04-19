from __future__ import annotations

import threading
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from shelf.core.models import SUPPORTED_EXTENSIONS
from shelf.indexing.models import JobType
from shelf.storage.repositories import FolderRepository, JobRepository


def is_supported_path(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


class QueueingEventHandler(FileSystemEventHandler):
    def __init__(self, folder_repository: FolderRepository, job_repository: JobRepository) -> None:
        super().__init__()
        self.folder_repository = folder_repository
        self.job_repository = job_repository
        self._recent: dict[str, str] = {}
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = str(Path(event.src_path).resolve())
        if not is_supported_path(path):
            return

        with self._lock:
            event_key = f"{event.event_type}:{path}:{getattr(event, 'dest_path', '')}"
            if self._recent.get(path) == event_key:
                return
            self._recent[path] = event_key

        folder_id = self.folder_repository.get_id_for_path(path)
        if isinstance(event, FileSystemMovedEvent):
            self.job_repository.enqueue(
                JobType.MOVE,
                str(Path(event.dest_path).resolve()),
                old_path=path,
                folder_id=folder_id,
            )
            return

        if event.event_type == "deleted":
            self.job_repository.enqueue(JobType.DELETE, path, folder_id=folder_id)
        else:
            self.job_repository.enqueue(JobType.UPSERT, path, folder_id=folder_id)


class WatcherService:
    def __init__(self, folder_repository: FolderRepository, job_repository: JobRepository) -> None:
        self.folder_repository = folder_repository
        self.job_repository = job_repository
        self.observer = Observer()
        self._scheduled_paths: set[str] = set()

    def refresh(self, paths: list[str]) -> None:
        new_paths = set(paths)
        if new_paths == self._scheduled_paths:
            return
        self.stop()
        self.observer = Observer()
        handler = QueueingEventHandler(self.folder_repository, self.job_repository)
        for path in new_paths:
            self.observer.schedule(handler, path, recursive=True)
        if new_paths:
            self.observer.start()
        self._scheduled_paths = new_paths

    def stop(self) -> None:
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)
        self._scheduled_paths = set()
