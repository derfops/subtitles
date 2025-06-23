# Installation Guide

This short guide gets **main.py** working on any Linux/macOS/Windows machine
with Python ≥ 3.8.

---

## 1. System prerequisites

| Tool            | Reason                         | Install hint |
|-----------------|--------------------------------|--------------|
| FFmpeg          | audio extraction               | `sudo apt install ffmpeg` or `brew install ffmpeg` |
| Python ≥ 3.8    | run the script & libraries     | https://python.org/downloads |

> **Windows:** grab a static FFmpeg build from <https://ffmpeg.org/download.html>  
> and add its `/bin` folder to your `PATH`.

---

## 2. Create a virtual environment (💡 recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate
````

---

## 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> On Apple Silicon: if you see a `torch` wheel warning, add
> `pip install 'torch>=2.2.0' --index-url https://download.pytorch.org/whl/cpu`
> **before** installing `openai-whisper`.

---

## 4. Set your OpenAI key (optional but enables high‑quality translation)

```bash
export OPENAI_API_KEY="sk-***********************************"
```

Windows PowerShell → `setx OPENAI_API_KEY "sk-***"`

---

## 5. Run a quick test

```bash
python3 main.py /path/to/some/video.mp4 --translate-engine openai --lang pt-BR
```

*Outputs*

```
video.en.srt         ← English transcription
video.pt-BR.srt        ← Portuguese (Brazil) translation
```

---

## 6. Typical full‑folder run

```bash
python3 main.py /media/Study \
  --model tiny \
  --translate-engine openai \
  --lang pt-BR \
  --sleep 1.0
```

---

## 7. FAQ

| Issue                                       | Fix                                                                             |
| ------------------------------------------- | ------------------------------------------------------------------------------- |
| **“openai.OpenAI not found”**               | `pip install -U openai` (v ≥ 1.0)                                               |
| **`googletrans` httpcore error**            | Dependencies already pinned in *requirements.txt*                               |
| **Whisper runs out of RAM**                 | Swap to `--model tiny` or `base`                                                |
| **Plex shows only the first subtitle file** | Make sure filenames match the video and use `.pt-BR.srt`; run “Refresh Metadata”. |

---

Good subtitles & happy binge‑watching! 🎬
