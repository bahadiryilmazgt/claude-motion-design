"""ElevenLabs TTS with the repo's house voice.

Single source of truth for voice-over defaults. Every VO / dub in this repo goes
through `synthesize()` (or the CLI below), so the voice, model and output format
are set here and nowhere else.

House rules (see CLAUDE.md, "Ev sesi"):
  - voice  Atakan (e9a1KJ0kRpwPORrz92UT), Turkish, Istanbul accent, library voice
  - model  eleven_v4; if the TTS endpoint rejects it, fall back to Text to Dialogue
           with a single input in the same voice
  - NO voice_settings (stability / similarity / style / speed): the voice reads with
    its own saved settings, like the ElevenLabs site with untouched sliders
  - output mp3_44100_128

Overrides (only when the user asks): ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID,
ELEVENLABS_OUTPUT_FORMAT.

Auth: sends ELEVENLABS_API_KEY as `xi-api-key` when it is set; otherwise sends no
key and relies on the session proxy, which injects it for api.elevenlabs.io.
Never hard-code a key here.

CLI:
  python tts_elevenlabs.py "Tam cümlelerle, konuşma diliyle yazılmış metin." out/vo/line01.mp3
  python tts_elevenlabs.py --text-file script.txt out/vo/full.mp3 --timestamps
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io"

HOUSE_VOICE_ID = "e9a1KJ0kRpwPORrz92UT"   # Atakan
HOUSE_MODEL_ID = "eleven_v4"
HOUSE_OUTPUT_FORMAT = "mp3_44100_128"


def defaults() -> dict:
    return {
        "voice_id": os.environ.get("ELEVENLABS_VOICE_ID", HOUSE_VOICE_ID),
        "model_id": os.environ.get("ELEVENLABS_MODEL_ID", HOUSE_MODEL_ID),
        "output_format": os.environ.get("ELEVENLABS_OUTPUT_FORMAT", HOUSE_OUTPUT_FORMAT),
    }


class ElevenLabsError(RuntimeError):
    def __init__(self, status: int, body: str, url: str):
        self.status, self.body = status, body
        hint = {
            401: "no valid key: open the secure credential form (api.elevenlabs.io, header xi-api-key)",
            403: "key refused: open the secure credential form (api.elevenlabs.io, header xi-api-key)",
            402: "plan issue, not a key issue (library voices need a paid plan)",
            429: "rate or concurrency limit: retry later, at most 2 requests at a time on low tiers",
        }.get(status, "")
        super().__init__(f"HTTP {status} from {url}: {body[:400]}" + (f"\n-> {hint}" if hint else ""))


def _post(path: str, payload: dict, output_format: str) -> tuple[bytes, str]:
    url = f"{API}{path}?output_format={output_format}"
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        headers["xi-api-key"] = key
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raise ElevenLabsError(e.code, e.read().decode("utf-8", "replace"), url) from None


def _model_rejected(err: ElevenLabsError) -> bool:
    return err.status in (400, 422) and "model" in err.body.lower()


def synthesize(text: str, out_path: str | Path, *, timestamps: bool = False,
               voice_id: str | None = None, model_id: str | None = None,
               output_format: str | None = None) -> dict:
    """Write `text` spoken by the house voice to `out_path`.

    With timestamps=True also writes `<out_path>.alignment.json` (character start/end
    times), the input for cues.json. Returns a small report dict.
    """
    cfg = defaults()
    voice_id = voice_id or cfg["voice_id"]
    model_id = model_id or cfg["model_id"]
    output_format = output_format or cfg["output_format"]
    suffix = "/with-timestamps" if timestamps else ""

    # No voice_settings on purpose: the voice keeps its own saved settings.
    endpoint = "text-to-speech"
    try:
        body, ctype = _post(f"/v1/text-to-speech/{voice_id}{suffix}",
                            {"text": text, "model_id": model_id}, output_format)
    except ElevenLabsError as e:
        if not _model_rejected(e):
            raise
        endpoint = "text-to-dialogue"
        body, ctype = _post(f"/v1/text-to-dialogue{suffix}",
                            {"inputs": [{"text": text, "voice_id": voice_id}], "model_id": model_id},
                            output_format)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {"file": str(out), "endpoint": endpoint, "voice_id": voice_id,
              "model_id": model_id, "output_format": output_format, "characters": len(text)}
    if timestamps:
        data = json.loads(body)
        out.write_bytes(base64.b64decode(data["audio_base64"]))
        align = {k: data.get(k) for k in ("alignment", "normalized_alignment", "voice_segments") if data.get(k)}
        align_path = out.with_name(out.name + ".alignment.json")
        align_path.write_text(json.dumps({"text": text, **align}, ensure_ascii=False, indent=1))
        report["alignment"] = str(align_path)
    else:
        if "json" in ctype:
            raise ElevenLabsError(200, body.decode("utf-8", "replace"), endpoint)
        out.write_bytes(body)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ElevenLabs TTS with the house voice (Atakan, eleven_v4).")
    ap.add_argument("text", nargs="?", help="text to speak (or use --text-file)")
    ap.add_argument("out", help="output .mp3 path, e.g. out/vo/line01.mp3")
    ap.add_argument("--text-file", help="read the text from this file")
    ap.add_argument("--timestamps", action="store_true", help="also write <out>.alignment.json")
    a = ap.parse_args(argv)
    text = Path(a.text_file).read_text(encoding="utf-8").strip() if a.text_file else a.text
    if not text:
        ap.error("give the text or --text-file")
    print(json.dumps(synthesize(text, a.out, timestamps=a.timestamps), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
