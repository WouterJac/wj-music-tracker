"""Cover-art cache in the data directory, keyed by content hash so duplicates share one file."""

import hashlib
import os
import tempfile
from pathlib import Path

from wj_music.domain.models import Picture

EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif"}
FALLBACK_EXTENSION = ".bin"


class FileCoverStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def store(self, picture: Picture) -> str:
        digest = hashlib.sha256(picture.data).hexdigest()
        extension = EXTENSIONS.get(picture.mime_type, FALLBACK_EXTENSION)
        name = f"{digest}{extension}"
        target = self._directory / name
        if not target.exists():
            self._directory.mkdir(parents=True, exist_ok=True)
            self._write_atomically(target, picture.data)
        return name

    def _write_atomically(self, target: Path, data: bytes) -> None:
        # A crash mid-write must not leave a truncated file under its final, hash-based name,
        # because store() would later see it exists and never repair it.
        handle, temp_name = tempfile.mkstemp(dir=self._directory, suffix=".tmp")
        try:
            with os.fdopen(handle, "wb") as temp_file:
                temp_file.write(data)
            os.replace(temp_name, target)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
