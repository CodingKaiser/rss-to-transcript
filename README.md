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

You'll see the most recent episodes in an interactive checkbox list. Use the
arrow keys and space to select, then Enter to confirm. Each selected episode is
downloaded and transcribed; the `.mp3` and `.txt` are written to `downloads/`.

Transcripts are written one timestamped line per segment:

```
[00:00:06] Hallo und herzlich willkommen.
[00:00:09] Hallo Wolfgang.
```

### Options

| Option     | Default                                        | Description                                        |
| ---------- | ---------------------------------------------- | -------------------------------------------------- |
| `--feed`   | _(required)_                                   | Podcast RSS feed URL                               |
| `--count`  | `10`                                           | Number of recent episodes to list                  |
| `--model`  | `base`                                         | Whisper model size: `tiny`/`base`/`small`/`medium`/`large-v3` |
| `--output` | `downloads`                                    | Directory for audio and transcripts                |

```bash
uv run rss-to-transcript --feed https://example.com/rss --count 5 --model small
```

The Whisper model downloads automatically on first use. Audio already present in
the output directory is reused instead of re-downloaded.

## Development

```bash
uv run pytest        # unit tests (feed parsing + filename logic)
uvx ruff check .     # lint
uv run ty check      # type check
```
