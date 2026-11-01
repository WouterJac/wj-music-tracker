"""Command line entry point: `wj-music scan` and `wj-music serve`."""

from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from wj_music.api.app import create_app
from wj_music.bootstrap import MusicPathNotConfiguredError, ScanOutcome, run_scan
from wj_music.config import MUSIC_PATH_ENV, Settings, find_config_file, load_settings
from wj_music.scanner.errors import MusicFolderNotFoundError

app = typer.Typer(help="WJ Music Tracker", no_args_is_help=True, add_completion=False)

ConfigOption = Annotated[
    Path | None,
    typer.Option(
        "--config", help="Config file. Defaults to config.local.toml in this or a parent folder."
    ),
]


def _settings(config: Path | None) -> Settings:
    return load_settings(config or find_config_file(Path.cwd()))


@app.command()
def scan(config: ConfigOption = None) -> None:
    """Scan the music folder and update the library database. Never writes to the music folder."""
    try:
        outcome = run_scan(_settings(config))
    except MusicPathNotConfiguredError:
        typer.echo(
            f"No music folder set. Set music_path in config.local.toml or {MUSIC_PATH_ENV}.",
            err=True,
        )
        raise typer.Exit(2) from None
    except MusicFolderNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from None
    typer.echo(_summary(outcome))


@app.command()
def serve(config: ConfigOption = None) -> None:
    """Start the web API on the configured loopback address."""
    settings = _settings(config)
    uvicorn.run(create_app(), host=settings.host, port=settings.port)


def _summary(outcome: ScanOutcome) -> str:
    report = outcome.report
    root = outcome.music_path
    lines = [
        f"Scanned {root}",
        f"Added: {len(report.added)}",
        f"Changed: {len(report.changed)}",
        *_listing(report.changed, root),
        f"Removed: {len(report.removed)}",
        *_listing(report.removed, root),
        f"Unchanged: {report.unchanged}",
        f"Errors: {len(report.errors)}",
        *(f"  {_relative(path, root)}: {message}" for path, message in report.errors),
    ]
    totals = outcome.totals
    lines.append(
        f"Library: {_count(totals.tracks, 'track')}, "
        f"{_count(totals.albums, 'album')}, {_count(totals.artists, 'artist')}"
    )
    return "\n".join(lines)


def _listing(paths: list[Path], root: Path) -> list[str]:
    return [f"  {_relative(path, root)}" for path in paths]


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
