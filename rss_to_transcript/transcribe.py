from pathlib import Path

from faster_whisper import WhisperModel
from rich.console import Console

console = Console()


def load_model(model_size: str) -> WhisperModel:
    """Load a faster-whisper model for CPU int8 inference (downloads on first use)."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe(model: WhisperModel, mp3_path: Path, dest_dir: Path) -> Path:
    """Transcribe an audio file and write the text to ``dest_dir/<stem>.txt``."""
    target = dest_dir / f"{mp3_path.stem}.txt"
    with console.status(f"Transcribing {mp3_path.name} ..."):
        segments, _info = model.transcribe(str(mp3_path))
        text = "".join(segment.text for segment in segments).strip()
    target.write_text(text + "\n", encoding="utf-8")
    return target
