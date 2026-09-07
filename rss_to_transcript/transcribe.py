from pathlib import Path

from faster_whisper import WhisperModel
from rich.console import Console

from rss_to_transcript.feed import Episode

console = Console()


def _hms(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_header(title: str, podcast: str) -> str:
    """Render the two comment lines naming the episode and the feed it came from."""
    return f"# Episode: {title}\n# Feed: {podcast}"


def format_segments(segments, timestamps: bool = True) -> str:
    """Render Whisper segments one per line, optionally prefixed with ``[HH:MM:SS]``."""
    if timestamps:
        return "\n".join(f"[{_hms(seg.start)}] {seg.text.strip()}" for seg in segments)
    return "\n".join(seg.text.strip() for seg in segments)


def load_model(model_size: str) -> WhisperModel:
    """Load a faster-whisper model for CPU int8 inference (downloads on first use)."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe(model: WhisperModel, ep: Episode, mp3_path: Path, dest_dir: Path, timestamps: bool = True) -> Path:
    """Transcribe an audio file to ``dest_dir/<stem>.txt``, one segment per line.

    The file opens with comment lines naming the episode and its feed.
    """
    target = dest_dir / f"{mp3_path.stem}.txt"
    with console.status(f"Transcribing {mp3_path.name} ..."):
        segments = list(model.transcribe(str(mp3_path))[0])
    header = format_header(ep.title, ep.podcast)
    text = format_segments(segments, timestamps)
    target.write_text(f"{header}\n\n{text}\n", encoding="utf-8")
    return target
