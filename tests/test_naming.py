from datetime import UTC, datetime

from rss_to_transcript.feed import Episode
from rss_to_transcript.naming import base_name, slugify


def _episode(title: str, published: datetime | None) -> Episode:
    return Episode(title=title, published=published, audio_url="http://x/a.mp3", duration=None)


def test_slugify_lowercases_and_hyphenates_spaces():
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_accents():
    assert slugify("Wohlstand für Alle") == "wohlstand-fur-alle"


def test_slugify_drops_punctuation_and_collapses_hyphens():
    assert slugify("Ep. 42: What's next?!") == "ep-42-what-s-next"


def test_slugify_falls_back_when_empty():
    assert slugify("!!!") == "episode"


def test_base_name_prefixes_date():
    ep = _episode("Hello World", datetime(2026, 7, 8, tzinfo=UTC))
    assert base_name(ep) == "2026-07-08-hello-world"


def test_base_name_without_date_omits_prefix():
    ep = _episode("Hello World", None)
    assert base_name(ep) == "hello-world"
