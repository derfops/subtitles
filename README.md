# Automatic Subtitle Generator (`main.py`) <!-- omit in toc -->

Whisper ➜ `.en.srt` + `.pt-BR.srt` ready for Plex
Transcribes any video/audio file, fixes time‑code overlaps, and translates—using either **OpenAI** or **Google Translate**—while preserving technical terminology.

---

* [Features](#features)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Configuration](#configuration)
  * [Global variables](#global-variables)
  * [CLI options](#cli-options)
* [Plex Compatibility](#plex-compatibility)
* [Examples](#examples)
* [How the Translation Prompt Works](#how-the-translation-prompt-works)
* [OpenAI SDK ≥ 1.0 vs < 1.0](#openai-sdk-≥10-vs-‹10)
* [Troubleshooting](#troubleshooting)
* [Road‑map / To‑do](#road‑map--to‑do)
* [License](#license)

---

## Features

* **Whisper transcription** – uses any Whisper model (`tiny` default).
* **Automatic translation** – choose **OpenAI** or **Google Translate**; plain transcription also supported.
* **Terminology‑safe** – prompt keeps cloud service names, commands, error codes, etc.
* **Overlap fixer** – guarantees ≥ 3 ms gap between subtitle blocks after rounding (required by Plex).
* **SDK‑aware** – detects and works with both `openai‑python` ≥ 1.0 and older < 1.0.
* **Rate‑limit friendly** – configurable `--sleep` delay between OpenAI requests.
* **Clean output** – strips backticks/quotes the model may add.
* **Plex‑ready filenames** –

  * `<video>.en.srt`   (original)
  * `<video>.pt-BR.srt` (Portuguese‑Brazil) → shows as **Portuguese (Brazil)** in Plex.

## Prerequisites

| Package                                              | Reason                                         |
| ---------------------------------------------------- | ---------------------------------------------- |
| `ffmpeg`                                             | audio extraction                               |
| `openai-whisper`                                     | transcription engine                           |
| `openai` ≥ 1.0 \| `<1.0`                             | translation (if you choose OpenAI)             |
| `googletrans==3.1.0a0` + `httpx<0.25` + `httpcore<1` | Google fallback                                |
| `torch`                                              | backend for Whisper (installed with `whisper`) |

```bash
sudo apt install ffmpeg        # Debian/Ubuntu
pip install openai-whisper \
           "openai>=1"         \
           "googletrans==3.1.0a0" "httpx<0.25" "httpcore<1"
```

## Installation

```bash
git clone <your-repo>
cd <repo>
# (optionally) create and activate a virtualenv here
pip install -r requirements.txt   # or use the list above
```

*Export your OpenAI key (skip if you’ll only use Google):*

```bash
export OPENAI_API_KEY="sk-..."
```

## Quick Start

```bash
python3 main.py /path/to/videos
```

Outputs:

```
Movie.en.srt
Movie.pt-BR.srt
```

`pt-BR` is the ISO‑639‑2 code used by OpenSubtitles for **Portuguese (Brazil)**, automatically recognised by Plex.

## Configuration

### Global variables

Located at the top of `main.py` for quick editing.

| Variable                                   | Default    | Purpose                               |
| ------------------------------------------ | ---------- | ------------------------------------- |
| `OPENAI_API_KEY`                           | `""`       | If left blank, script reads from env. |
| `TARGET_LANGUAGE_CODE`                     | `pt-BR`      | File‑extension of translated SRT.     |
| `SRT_SOURCE_LANGUAGE_CODE`                 | `en`       | File‑extension of source SRT.         |
| `CHUNK_SIZE_CHARS` / `CHUNK_OVERLAP_CHARS` | 1500 / 150 | Reserved for future chunking.         |
| `DEFAULT_SLEEP_BETWEEN_API`                | `1.0` s    | Delay between OpenAI calls.           |

### CLI options

```
positional arguments:
  target                 File or directory with media

optional arguments:
  --model tiny|base|small|medium|large   Whisper model (default: tiny)
  --device cpu|cuda                      Where to run Whisper (default: cpu)
  --translate-engine openai|google|none  Select translator (default: openai)
  --lang pt-BR|pt|por|...                  Extension for translated SRT (default: pt-BR)
  --overwrite                            Regenerate SRT even if they exist
  --sleep FLOAT                          Seconds to wait between OpenAI requests
```

## Plex Compatibility

* Use `.pt-BR.srt` for **Portuguese (Brazil)**; `.pt.srt`/`.por.srt` are recognised but show as generic “Portuguese”.
* File name **must** exactly match the video (case‑sensitive).
* If Plex still doesn’t list new subs, choose **Refresh Metadata** or **Analyze** on the folder.

## Examples

| Task                                          | Command                                             |
| --------------------------------------------- | --------------------------------------------------- |
| Transcribe & translate all videos in a folder | `python3 main.py ~/videos`                          |
| Same, but force Whisper `base`                | `python3 main.py ~/videos --model base`             |
| Only English transcription (no translation)   | `python3 main.py video.mp4 --translate-engine none` |
| Translate with Google, not OpenAI             | `python3 main.py ~/vid --translate-engine google`   |
| Add 2 s delay between OpenAI calls            | `python3 main.py ~/vid --sleep 2`                   |

## How the Translation Prompt Works

> **System message**:
> “Translate from EN to pt-BR (Português do Brasil).
> **Do NOT translate** technical terms, cloud service names, commands, error codes, UPPERCASE words, or text inside backticks.
> Return plain text.”

*Each chunk (≤ 20 segments) is numbered for context; numbering is stripped from results.*
Backticks and quotes are sanitized afterwards.

## OpenAI SDK ≥ 1.0 vs < 1.0

The script auto‑detects:

| Version                     | Detection                  | Call used                        |
| --------------------------- | -------------------------- | -------------------------------- |
| **≥ 1.0** (`openai.OpenAI`) | `hasattr(openai,"OpenAI")` | `client.chat.completions.create` |
| **< 1.0**                   | else                       | `openai.ChatCompletion.create`   |

No manual change required.

## Troubleshooting

| Issue                                           | Fix                                                                                                       |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `openai.OpenAI` not found                       | `pip install --upgrade openai`                                                                            |
| *“googletrans erro httpcore.SyncHTTPTransport”* | Ensure `googletrans==3.1.0a0` and `httpcore<1`                                                            |
| Plex loads only the first SRT                   | Ensure no time‑code overlaps (script already enforces 3 ms). Delete Plex cache or hit *Refresh Metadata*. |
| Memory errors with Whisper                      | Use smaller model `--model tiny` or `base`.                                                               |

## Road‑map / To‑do

* Optional VTT output
* Automatic chunking for very long segments (`CHUNK_SIZE_CHARS`)
* Dockerfile for one‑line run
* GUI wrapper (Tkinter / Web UI)

## License

MIT – do whatever you want, blame yourself if it breaks.
