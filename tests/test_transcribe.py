from dataclasses import dataclass

from rss_to_transcript.transcribe import format_segments


@dataclass
class FakeSegment:
    start: float
    end: float
    text: str


def test_formats_segments_with_hms_timestamps():
    segs = [
        FakeSegment(4.0, 6.0, " Hallo und herzlich willkommen."),
        FakeSegment(7.2, 8.0, " Hallo Wolfgang."),
    ]
    out = format_segments(segs)
    assert out == "[00:00:04] Hallo und herzlich willkommen.\n[00:00:07] Hallo Wolfgang."


def test_timestamp_handles_hours_and_minutes():
    segs = [FakeSegment(3723.0, 3725.0, "later")]  # 1h 2m 3s
    out = format_segments(segs)
    assert out == "[01:02:03] later"
