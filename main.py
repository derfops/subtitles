#!/usr/bin/env python3
"""
main.py ─ Gerador de legendas automáticas + tradução pt‑BR (Plex‑ready)
===============================================================================
• Transcrição OpenAI‑Whisper (modelo tiny por default)  
• Tradução via OpenAI Chat API (detecta SDK novo ≥1.0 *ou* antigo <1.0)  
• Corrige overlaps (≥3 ms) e remove backticks/aspas da tradução  
• Grava UTF‑8:  <video>.en.srt  e  <video>.pt-BR.srt  (Portuguese‑Brazil)

CONFIGURAÇÕES RÁPIDAS – edite aqui ou passe por CLI
"""
# ───────── Config section ─────────
OPENAI_API_KEY            = ""        # "" → usa variável de ambiente
TARGET_LANGUAGE_CODE      = "pt-BR"     # extensão do SRT traduzido
SRT_SOURCE_LANGUAGE_CODE  = "en"      # extensão do SRT original
CHUNK_SIZE_CHARS          = 1500      # reservado (não usado neste script)
CHUNK_OVERLAP_CHARS       = 150       # reservado
DEFAULT_SLEEP_BETWEEN_API = 1.0       # segundos entre chamadas OpenAI
# ───────────────────────────────────

import os, time, argparse, gc, re, subprocess, sys, tempfile, importlib
from pathlib import Path
from typing import List, Dict, Any

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

MEDIA_EXT = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".mp3", ".wav"}

# ───────────── Helpers de tempo / SRT ─────────────
def sec_to_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def fix_segments(raw: List[Dict[str, Any]], delta: float = 0.003):
    """Folga mínima de 3 ms depois do arredondamento."""
    last_end = -delta
    for s in raw:
        if s["start"] - last_end < delta:
            s["start"] = last_end + delta
        if s["end"] - s["start"] < delta:
            s["end"] = s["start"] + delta
        s["start"] = round(s["start"], 3)
        s["end"]   = round(s["end"],   3)
        last_end = s["end"]
    return raw

def to_srt(segs: List[Dict[str, Any]]) -> str:
    out = []
    for i, s in enumerate(segs, 1):
        out += [
            str(i),
            f"{sec_to_ts(s['start'])} --> {sec_to_ts(s['end'])}",
            s["text"].strip(),
            ""
        ]
    out.append("")  # linha em branco final
    return "\n".join(out)

def write_utf8(path: Path, text: str):
    with path.open("w", encoding="utf-8") as f:
        f.write(text)

# ───────────── I/O helpers ─────────────
def extract_audio(video: Path) -> Path:
    tmp = Path(tempfile.gettempdir()) / f"{video.stem}_{int(time.time())}.wav"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-i", str(video),
         "-ac", "1", "-ar", "16000", "-vn", str(tmp)],
        check=True
    )
    return tmp

def sanitize_line(t: str) -> str:
    """Remove backticks e aspas duplas/curvas nas pontas."""
    t = t.strip()
    if (t.startswith(("`", '"', "“")) and t.endswith(("`", '"', "”")) and len(t) > 1):
        t = t[1:-1].strip()
    return t.replace("`", "").replace("“", "").replace("”", "")

# ───────────── Tradução ─────────────
def translate(texts: List[str], engine: str, lang: str,
              sleep_s: float) -> List[str]:
    if engine == "none":
        return texts

    if engine == "google":
        from googletrans import Translator
        iso = lang.split("-")[0].lower()
        if iso == "pt-BR":   # google não reconhece “pt-BR”
            iso = "pt"
        translated = Translator().translate(texts, dest=iso)
        return [sanitize_line(t.text) for t in translated]

    if engine == "openai":
        openai = importlib.import_module("openai")

        # Detecta SDK ≥1.0 (possui classe OpenAI) vs <1.0
        use_new_sdk = hasattr(openai, "OpenAI")

        if use_new_sdk:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            def chat_completion(messages):
                return client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.2
                ).choices[0].message.content
        else:
            def chat_completion(messages):
                return openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.2
                ).choices[0].message.content

        guideline = (
            f"Translate from {SRT_SOURCE_LANGUAGE_CODE.upper()} to "
            f"{lang.upper()} (Português do Brasil). "
            "Do NOT translate technical terms, cloud service names, commands, "
            "error codes, words fully in UPPERCASE, or any text inside backticks. "
            "Return plain text without surrounding quotes or backticks."
        )

        CHUNK = 20
        out: List[str] = []
        for i in range(0, len(texts), CHUNK):
            chunk = texts[i:i+CHUNK]
            messages = [
                {"role": "system", "content": guideline},
                {"role": "user",
                 "content": "\n".join(f"{j+1}. {t}" for j, t in enumerate(chunk))}
            ]
            content = chat_completion(messages)
            lines = [sanitize_line(re.sub(r"^\d+[\).]?\s*", "", ln))
                     for ln in content.splitlines() if ln.strip()]
            while len(lines) < len(chunk):
                lines.append("")
            out.extend(lines[:len(chunk)])
            time.sleep(sleep_s)
        return out

    raise ValueError("engine de tradução inválido")

# ───────────── Processa um vídeo ─────────────
def process_file(model, vid: Path, args):
    print(f"▶  {vid.name}")
    en_srt = vid.with_suffix(f".{SRT_SOURCE_LANGUAGE_CODE}.srt")
    pt_srt = vid.with_suffix(f".{args.lang}.srt")

    if not args.overwrite and en_srt.exists() and pt_srt.exists():
        print("   • legendas já existem, pulando")
        return

    audio = extract_audio(vid)
    try:
        res = model.transcribe(str(audio), verbose=False)
        segs = fix_segments([{k: s[k] for k in ("start", "end", "text")}
                             for s in res["segments"]])

        write_utf8(en_srt, to_srt(segs))

        try:
            translated = translate([s["text"] for s in segs],
                                   args.translate_engine, args.lang, args.sleep)
            segs_pt = [{**s, "text": t} for s, t in zip(segs, translated)]
            write_utf8(pt_srt, to_srt(segs_pt))
            print("   • OK (EN + PT‑BR)")
        except Exception as e:
            print(f"   ! Tradução falhou ({e}) – gerado apenas EN")
    finally:
        audio.unlink(missing_ok=True)
        gc.collect()

# ───────────── CLI / main ─────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="Arquivo ou diretório com mídia")
    ap.add_argument("--model", default="tiny",
                    help="Modelo Whisper (tiny|base|small|medium|large)")
    ap.add_argument("--device", default="cpu", help="cpu|cuda")
    ap.add_argument("--translate-engine", default="openai",
                    choices=["openai", "google", "none"])
    ap.add_argument("--lang", default=TARGET_LANGUAGE_CODE,
                    help="Extensão da legenda traduzida (pt-BR = pt‑BR)")
    ap.add_argument("--overwrite", action="store_true",
                    help="Recria SRT mesmo se já existir")
    ap.add_argument("--sleep", type=float, default=DEFAULT_SLEEP_BETWEEN_API,
                    help="Delay entre chamadas OpenAI (segundos)")
    args = ap.parse_args()

    import whisper, torch
    torch.set_num_threads(1)

    print(f"╭─ Carregando modelo {args.model}…")
    model = whisper.load_model(args.model, device=args.device)
    print("╰─ Modelo pronto.\n")

    root = Path(args.target)
    vids = [root] if root.is_file() else [
        f for f in root.rglob("*") if f.suffix.lower() in MEDIA_EXT]

    if not vids:
        sys.exit("Nada a processar.")

    for v in sorted(vids):
        try:
            process_file(model, v, args)
        except Exception as exc:
            print(f"   ! Erro inesperado: {exc}")

if __name__ == "__main__":
    main()
