from pathlib import Path
from typing import Annotated

import questionary
import typer
from rich.console import Console

from rss_to_transcript.download import download
from rss_to_transcript.feed import Episode, fetch_episodes
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
    count: Annotated[int, typer.Option(help="Number of recent episodes to list.")] = 10,
    model: Annotated[str, typer.Option(help="Whisper model size (tiny/base/small/medium/large-v3).")] = "base",
    output: Annotated[Path, typer.Option(help="Directory for audio and transcripts.")] = Path("downloads"),
) -> None:
    """Select recent episodes, then download and transcribe each one."""
    try:
        episodes = fetch_episodes(feed, count)
    except Exception as exc:  # feedparser is lenient; surface fetch/parse issues cleanly
        console.print(f"[red]Could not read feed:[/red] {exc}")
        raise typer.Exit(1)

    choices = [questionary.Choice(title=_label(ep), value=ep) for ep in episodes]
    selected: list[Episode] | None = questionary.checkbox(
        "Select episodes to download and transcribe:", choices=choices
    ).ask()

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
            txt_path = transcribe(whisper, mp3_path, output)
            transcripts.append(txt_path)
            console.print(f"[green]✓[/green] {txt_path}")
        except Exception as exc:  # one bad episode shouldn't abort the batch
            console.print(f"[red]✗ {ep.title}:[/red] {exc}")

    if transcripts:
        console.print(f"\n[bold]Done.[/bold] Wrote {len(transcripts)} transcript(s) to {output}/")
    else:
        console.print("\n[yellow]No transcripts were written.[/yellow]")
        raise typer.Exit(1)
