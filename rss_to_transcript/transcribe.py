from pathlib import Path

from faster_whisper import WhisperModel
from rich.console import Console

console = Console()


def _hms(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_segments(segments) -> str:
    """Render Whisper segments as one ``[HH:MM:SS] text`` line each."""
    return "\n".join(f"[{_hms(seg.start)}] {seg.text.strip()}" for seg in segments)


def load_model(model_size: str) -> WhisperModel:
    """Load a faster-whisper model for CPU int8 inference (downloads on first use)."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe(model: WhisperModel, mp3_path: Path, dest_dir: Path) -> Path:
    """Transcribe an audio file to ``dest_dir/<stem>.txt`` as timestamped lines."""
    target = dest_dir / f"{mp3_path.stem}.txt"
    with console.status(f"Transcribing {mp3_path.name} ..."):
        segments = list(model.transcribe(str(mp3_path))[0])
    text = format_segments(segments)
    target.write_text(text + "\n", encoding="utf-8")
    return target
