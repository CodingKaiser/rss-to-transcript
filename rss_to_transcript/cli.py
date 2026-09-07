from pathlib import Path
from typing import Annotated

import httpx
import typer
from questionary.prompts.common import Choice
from rich.console import Console

from rss_to_transcript.download import download
from rss_to_transcript.feed import Episode, fetch_episodes
from rss_to_transcript.picker import VISIBLE_ROWS, checkbox_scrolling
from rss_to_transcript.transcribe import load_model, transcribe

app = typer.Typer(
    help="Download and locally transcribe recent podcast episodes from an RSS feed.",
    add_completion=False,
)
console = Console()


def _label(ep: Episode) -> str:
    date = f"{ep.published:%Y-%m-%d}" if ep.published else "undated"
    parts = [date]
    if ep.duration:
        parts.append(ep.duration)
    return f"{ep.title}  ({', '.join(parts)})"


@app.command()
def run(
    feed: Annotated[str, typer.Option(help="Podcast RSS feed URL.")],
    rows: Annotated[int, typer.Option(help="Episodes visible at once in the picker.")] = VISIBLE_ROWS,
    limit: Annotated[
        int | None, typer.Option(help="Only load the newest N episodes (default: the whole feed).")
    ] = None,
    model: Annotated[str, typer.Option(help="Whisper model size (tiny/base/small/medium/large-v3).")] = "base",
    output: Annotated[Path, typer.Option(help="Directory for audio and transcripts.")] = Path("downloads"),
    timestamps: Annotated[
        bool, typer.Option("--timestamps/--no-timestamps", help="Prefix each transcript line with [HH:MM:SS].")
    ] = True,
) -> None:
    """Search the feed's episodes, then download and transcribe the selected ones."""
    try:
        episodes = fetch_episodes(feed, limit)
    except (ValueError, OSError) as exc:
        console.print(f"[red]Could not read feed:[/red] {exc}")
        raise typer.Exit(1)

    choices = [Choice(title=_label(ep), value=ep) for ep in episodes]
    selected: list[Episode] | None = checkbox_scrolling(
        f"Select episodes ({len(episodes)} in feed):", choices, visible_rows=rows
    )

    if not selected:
        console.print("No episodes selected. Nothing to do.")
        raise typer.Exit(0)

    output.mkdir(parents=True, exist_ok=True)

    console.print(f"Loading Whisper model [bold]{model}[/bold] (first run downloads it)...")
    whisper = load_model(model)

    transcripts: list[Path] = []
    for ep in selected:
        try:
            mp3_path = download(ep, output)
            txt_path = transcribe(whisper, ep, mp3_path, output, timestamps)
            transcripts.append(txt_path)
            console.print(f"[green]✓[/green] {txt_path}")
        # One bad episode shouldn't abort the batch. faster-whisper/ctranslate2 export
        # no exception types, so decode failures arrive as RuntimeError/ValueError.
        except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
            console.print(f"[red]✗ {ep.title}:[/red] {exc}")

    if transcripts:
        console.print(f"\n[bold]Done.[/bold] Wrote {len(transcripts)} transcript(s) to {output}/")
    else:
        console.print("\n[yellow]No transcripts were written.[/yellow]")
        raise typer.Exit(1)
