# rss-to-transcript

A command-line app that downloads recent episodes from a podcast RSS feed and
transcribes them to text **locally** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
(no cloud APIs, no system `ffmpeg` required).

## Install

```bash
uv sync
```

## Usage

```bash
uv run rss-to-transcript --feed https://example.com/podcast/rss
```

Every episode the feed publishes is loaded into an interactive picker showing
10 at a time. Use the arrow keys to scroll, **type to filter by title**
(backspace to edit, and the filter is case-insensitive), space to select, then
Enter to confirm. Each selected episode is downloaded and transcribed; the
`.mp3` and `.txt` are written to `downloads/`.

```
? Select episodes (312 in feed): (type to filter, <space> to select, <enter> to confirm)
 » ○ Episode 031  (2026-03-04, 41:02)
   ◉ Episode 032  (2026-03-11, 38:55)
   ○ Episode 033  (2026-03-18, 44:10)
  showing 10 of 312
```

Filtering searches episode titles only. Note that RSS has no pagination, so the
picker can only reach the episodes present in the feed — most podcasts publish
only their most recent few hundred.

Transcripts are written one timestamped line per segment:

```
[00:00:06] Hallo und herzlich willkommen.
[00:00:09] Hallo Wolfgang.
```

### Options

| Option     | Default                                        | Description                                        |
| ---------- | ---------------------------------------------- | -------------------------------------------------- |
| `--feed`   | _(required)_                                   | Podcast RSS feed URL                               |
| `--rows`   | `10`                                           | Episodes visible at once in the picker             |
| `--limit`  | _(whole feed)_                                 | Only load the newest N episodes                    |
| `--model`  | `base`                                         | Whisper model size: `tiny`/`base`/`small`/`medium`/`large-v3` |
| `--output` | `downloads`                                    | Directory for audio and transcripts                |

```bash
uv run rss-to-transcript --feed https://example.com/rss --rows 20 --model small
```

The Whisper model downloads automatically on first use. Audio already present in
the output directory is reused instead of re-downloaded.

## Development

```bash
uv run pytest        # unit tests (feed parsing + filename logic)
uvx ruff check .     # lint
uv run ty check      # type check
```
