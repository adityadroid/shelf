from __future__ import annotations

import hashlib
from pathlib import Path


def fast_fingerprint(path: Path) -> str:
    stats = path.stat()
    return f"{path.resolve()}|{stats.st_size}|{getattr(stats, 'st_mtime_ns', int(stats.st_mtime * 1_000_000_000))}"


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
