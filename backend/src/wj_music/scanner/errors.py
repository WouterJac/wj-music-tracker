from pathlib import Path


class InvalidFlacError(Exception):
    """A file that should be FLAC cannot be parsed."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Not a readable FLAC file: {path}")
        self.path = path


class MusicFolderNotFoundError(Exception):
    """The music folder is missing or not a directory, for example an unplugged drive.

    Scanning it would look like every file was deleted, so the scan refuses to run.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(f"Music folder not found or not a directory: {path}")
        self.path = path
