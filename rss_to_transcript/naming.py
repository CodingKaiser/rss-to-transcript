import re
import unicodedata

from rss_to_transcript.feed import Episode


def slugify(text: str) -> str:
    """Lowercase ASCII slug: accents stripped, non-alphanumerics collapsed to hyphens."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "episode"


def base_name(ep: Episode) -> str:
    """Filename stem for an episode's audio/transcript, date-prefixed when known."""
    slug = slugify(ep.title)
    if ep.published is None:
        return slug
    return f"{ep.published:%Y-%m-%d}-{slug}"
