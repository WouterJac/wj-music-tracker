"""Cover-art cache in the data directory, keyed by content hash so duplicates share one file."""

import hashlib
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
            target.write_bytes(picture.data)
        return name
