"""Download the Montserrat font files (OFL, via Fontsource on jsDelivr). Music and SFX are synthesized by audio.py, nothing else to fetch."""
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
(HERE / "fonts").mkdir(exist_ok=True)
for w in (300, 500, 700, 800, 900):
    for sub in ("latin", "latin-ext"):
        name = f"montserrat-{sub}-{w}-normal.woff2"
        dst = HERE / "fonts" / name
        if not dst.exists():
            urllib.request.urlretrieve(f"https://cdn.jsdelivr.net/npm/@fontsource/montserrat@5.0.19/files/{name}", dst)
        print("ok", name)
