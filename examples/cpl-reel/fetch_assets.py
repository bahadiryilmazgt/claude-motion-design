"""Download the third-party assets for the CPL reel (not redistributed here; check each license):
Mixkit music + SFX (Mixkit free license), Instrument Serif + Inter Tight (OFL, Google Fonts)."""
import urllib.request
from pathlib import Path
H = Path(__file__).parent; UA = {"User-Agent": "Mozilla/5.0"}
def get(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()); print("ok", dest.relative_to(H))
get("https://assets.mixkit.co/music/371/371.mp3", H / "assets/music/m371.mp3")
for sid in ["1125", "2568", "1117", "2364", "2357", "1490", "1489", "1143", "3083", "2865", "1485", "1113"]:
    get(f"https://assets.mixkit.co/active_storage/sfx/{sid}/{sid}-preview.mp3", H / f"assets/sfx/{sid}.mp3")
G = "https://fonts.gstatic.com/s/"
for name, p in {"serif.woff2": "instrumentserif/v5/jizBRFtNs2ka5fXjeivQ4LroWlx-6zUTjg.woff2", "serif-ext.woff2": "instrumentserif/v5/jizBRFtNs2ka5fXjeivQ4LroWlx-6zsTjmbI.woff2",
                "serif-i.woff2": "instrumentserif/v5/jizHRFtNs2ka5fXjeivQ4LroWlx-6zAjjH7M.woff2", "serif-i-ext.woff2": "instrumentserif/v5/jizHRFtNs2ka5fXjeivQ4LroWlx-6zAjgn7MsNo.woff2",
                "tight.woff2": "intertight/v9/NGSwv5HMAFg6IuGlBNMjxLsH8ag.woff2", "tight-ext.woff2": "intertight/v9/NGSwv5HMAFg6IuGlBNMjxLsJ8ah8QA.woff2"}.items():
    get(G + p, H / "fonts" / name)
print("done")
