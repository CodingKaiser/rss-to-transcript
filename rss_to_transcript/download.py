from pathlib import Path

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)

from rss_to_transcript.feed import Episode
from rss_to_transcript.naming import base_name


def download(ep: Episode, dest_dir: Path) -> Path:
    """Stream an episode's audio to ``dest_dir/<base>.mp3``, showing progress.

    If the target already exists and is non-empty, it is reused (no re-download).
    """
    target = dest_dir / f"{base_name(ep)}.mp3"
    if target.exists() and target.stat().st_size > 0:
        return target

    tmp = target.with_suffix(".mp3.part")
    with httpx.stream("GET", ep.audio_url, follow_redirects=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0)) or None
        columns = [
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ]
        with Progress(*columns) as progress:
            task = progress.add_task(f"↓ {target.name}", total=total)
            with tmp.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    tmp.replace(target)
    return target
