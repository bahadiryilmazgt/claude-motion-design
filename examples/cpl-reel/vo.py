"""Turkish voice-over with edge-tts (tr-TR-EmelNeural), one file per line + word timings -> assets/vo/cues.json.
CPL is spelled "si-pi-el" so the voice says it the way Turkish marketers do (letter by letter it reads "ce-pe-le")."""
import asyncio, json, os, ssl, sys
import edge_tts, edge_tts.communicate as c
from pathlib import Path

HERE = Path(__file__).parent
ca = "/root/.ccr/ca-bundle.crt"
if os.path.exists(ca): c._SSL_CTX = ssl.create_default_context(cafile=ca)
VOICE, RATE, PITCH = "tr-TR-EmelNeural", "+14%", "+6Hz"
RATES = {"l4": "+20%"}
LINES = {
    "l1": "Düşük si-pi-el, başarılı reklam mı? Her zaman değil!",
    "l2": "A kampanyası: on euroya yüz lead! Harika, değil mi? Ama sonuç... sadece iki satış.",
    "l3": "B kampanyası ise on sekiz euro si-pi-el ile daha az lead getiriyor... ama tam sekiz satış yapıyor!",
    "l4": "Çünkü önemli olan; lead kalitesi, satış oranı, müşteri maliyeti. Si-pi-el sadece başlangıç! Asıl soru: bu lead'ler satışa dönüşüyor mu?",
    "l5": "Reklam performansını lead ile değil, sonuçla ölç!",
}


async def one(key, text):
    com = edge_tts.Communicate(text, VOICE, rate=RATES.get(key, RATE), pitch=PITCH, boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY"))
    audio, words = bytearray(), []
    async for m in com.stream():
        if m["type"] == "audio": audio += m["data"]
        elif m["type"] == "WordBoundary":
            words.append({"w": m["text"], "t": m["offset"] / 1e7, "d": m["duration"] / 1e7})
    (HERE / f"assets/vo/{key}.mp3").write_bytes(bytes(audio))
    return words


async def main(keys):
    p = HERE / "assets/vo/cues.json"
    cues = json.loads(p.read_text()) if p.exists() else {}
    for k in keys:
        for attempt in range(4):
            try: cues[k] = await one(k, LINES[k]); break
            except Exception as e: print("retry", k, e); await asyncio.sleep(2 ** attempt)
        print(k, round(cues[k][-1]["t"] + cues[k][-1]["d"], 2), "s")
    p.write_text(json.dumps(cues, ensure_ascii=False, indent=1))

asyncio.run(main(sys.argv[1:] or list(LINES)))
