from datetime import UTC, datetime

import pytest

from rss_to_transcript.feed import Episode, fetch_episodes

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Test Podcast</title>
    <item>
      <title>Newest Episode</title>
      <pubDate>Wed, 08 Jul 2026 06:00:00 GMT</pubDate>
      <enclosure url="http://cdn.example/newest.mp3" type="audio/mpeg" length="123"/>
      <itunes:duration>32:10</itunes:duration>
    </item>
    <item>
      <title>Middle Episode</title>
      <pubDate>Wed, 01 Jul 2026 06:00:00 GMT</pubDate>
      <enclosure url="http://cdn.example/middle.mp3" type="audio/mpeg" length="456"/>
      <itunes:duration>1830</itunes:duration>
    </item>
    <item>
      <title>Oldest Episode</title>
      <pubDate>Wed, 24 Jun 2026 06:00:00 GMT</pubDate>
      <enclosure url="http://cdn.example/oldest.mp3" type="audio/mpeg" length="789"/>
    </item>
  </channel>
</rss>
"""

FEED_NO_ENCLOSURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Broken</title>
    <item><title>Has audio</title><enclosure url="http://x/a.mp3" type="audio/mpeg"/></item>
    <item><title>No audio</title></item>
  </channel>
</rss>
"""

EMPTY_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>
"""


def test_returns_episodes_in_feed_order_newest_first():
    eps = fetch_episodes(FEED)
    assert [e.title for e in eps] == ["Newest Episode", "Middle Episode", "Oldest Episode"]


def test_respects_limit():
    eps = fetch_episodes(FEED, limit=2)
    assert [e.title for e in eps] == ["Newest Episode", "Middle Episode"]


def test_no_limit_returns_every_episode():
    eps = fetch_episodes(FEED, limit=None)
    assert len(eps) == 3


def test_limit_larger_than_feed_returns_all():
    eps = fetch_episodes(FEED, limit=99)
    assert len(eps) == 3


def test_extracts_audio_url_and_metadata():
    ep = fetch_episodes(FEED, limit=1)[0]
    assert isinstance(ep, Episode)
    assert ep.audio_url == "http://cdn.example/newest.mp3"
    assert ep.published == datetime(2026, 7, 8, 6, 0, 0, tzinfo=UTC)
    assert ep.duration == "32:10"


def test_skips_entries_without_a_playable_enclosure():
    eps = fetch_episodes(FEED_NO_ENCLOSURE)
    assert [e.title for e in eps] == ["Has audio"]


def test_missing_pubdate_yields_none_published():
    ep = fetch_episodes(FEED_NO_ENCLOSURE, limit=1)[0]
    assert ep.published is None


def test_empty_feed_raises_valueerror():
    with pytest.raises(ValueError):
        fetch_episodes(EMPTY_FEED)
