from __future__ import annotations

from pathlib import Path

from shelf.core.models import SUPPORTED_EXTENSIONS
from shelf.indexing.models import JobType
from shelf.storage.repositories import FolderRepository, JobRepository, ScannerStateRepository


class ReconciliationService:
    def __init__(
        self,
        folder_repository: FolderRepository,
        document_repository,
        job_repository: JobRepository,
        scanner_state: ScannerStateRepository,
    ) -> None:
        self.folder_repository = folder_repository
        self.document_repository = document_repository
        self.job_repository = job_repository
        self.scanner_state = scanner_state

    def run(self) -> None:
        discovered: set[str] = set()
        for folder_path in self.folder_repository.list_paths():
            root = Path(folder_path)
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    normalized = str(path.resolve())
                    discovered.add(normalized)
                    self.job_repository.enqueue(
                        JobType.UPSERT,
                        normalized,
                        folder_id=self.folder_repository.get_id_for_path(normalized),
                    )

        indexed_paths = set(self.document_repository.list_document_paths())
        for removed in indexed_paths - discovered:
            self.job_repository.enqueue(JobType.DELETE, removed)

        self.scanner_state.set("last_reconciliation", {"count": len(discovered)})
