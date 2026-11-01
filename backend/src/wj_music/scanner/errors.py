from pathlib import Path


class InvalidFlacError(Exception):
    """A file that should be FLAC cannot be parsed."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Not a readable FLAC file: {path}")
        self.path = path
