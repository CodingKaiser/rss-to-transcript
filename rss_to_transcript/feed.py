from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser


@dataclass
class Episode:
    title: str
    published: datetime | None
    audio_url: str
    duration: str | None


def _audio_url(entry) -> str | None:
    """Return the first playable enclosure URL, preferring audio/* types."""
    enclosures = getattr(entry, "enclosures", []) or []
    for enc in enclosures:
        if str(enc.get("type", "")).startswith("audio/") and enc.get("href"):
            return enc["href"]
    for enc in enclosures:
        if enc.get("href"):
            return enc["href"]
    return None


def _published(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None)
    if parsed is None:
        return None
    # published_parsed is a UTC struct_time; drop tzinfo for a naive local-agnostic value.
    return datetime(*parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)


def fetch_episodes(feed: str, count: int) -> list[Episode]:
    """Parse a podcast feed (URL, path, or raw RSS string) into recent episodes.

    Episodes are returned in feed order (newest first), limited to ``count``.
    Entries without a playable enclosure are skipped. Raises ValueError if the
    feed yields no usable episodes.
    """
    parsed = feedparser.parse(feed)
    episodes: list[Episode] = []
    for entry in parsed.entries:
        url = _audio_url(entry)
        if url is None:
            continue
        episodes.append(
            Episode(
                title=getattr(entry, "title", "Untitled"),
                published=_published(entry),
                audio_url=url,
                duration=getattr(entry, "itunes_duration", None),
            )
        )
        if len(episodes) >= count:
            break

    if not episodes:
        raise ValueError("No episodes with downloadable audio found in the feed.")
    return episodes
