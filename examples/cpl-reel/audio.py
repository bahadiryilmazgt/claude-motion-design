"""CPL reel soundtrack (30 s): Turkish VO (edge-tts, assets/vo) + Mixkit 'Cat Walk' (Arulo #371, 130 BPM) started at
11.88 s so its drop (song 14.769 s) lands on "Her zaman değil" (film 2.89 s), ducked under the voice.
Mixkit SFX placed by measured peak, counter ticks / thuds synthesized on the same easing curves as film.html.
Two-pass loudnorm to -14 LUFS, TP -1."""
import json, subprocess
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
SR, T = 48000, 30.0
N = int(T * SR)
FF = "ffmpeg"


def load(p, filt=None):
    cmd = [FF, "-v", "quiet", "-i", str(p)] + (["-af", filt] if filt else []) + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def write(x, p):
    subprocess.run([FF, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", str(p)], input=x.astype(np.float32).tobytes(), check=True)


def lufs(x):
    p = HERE / "out/_tmp.wav"; write(x, p)
    m = subprocess.run([FF, "-hide_banner", "-i", str(p), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(m[m.rindex("{"):m.rindex("}") + 1])["input_i"])


def to_lufs(x, target):
    return x * 10 ** ((target - lufs(x)) / 20)


def add(dst, src, t, gain=1.0, by_peak=True):
    """Mix src so that its loudest sample (or its start) lands on film time t."""
    s = src * gain
    i0 = int(round(t * SR)) - (int(np.abs(s).sum(1).argmax()) if by_peak else 0)
    lo, hi = max(0, i0), min(len(dst), i0 + len(s))
    if hi > lo: dst[lo:hi] += s[lo - i0:hi - i0]


# ---------- easing copies of film.html ----------
def io(u): return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def eout(u): return 1 - (1 - u) ** 3
def count_ticks(t0, d, a, b, step=1, ease=eout):
    """times where round(lerp(a,b,ease(u))) crosses a multiple of `step` (one tick per visible jump)."""
    out, last = [], None
    for k in range(int(d * 600) + 1):
        tt = t0 + k / 600; v = round(a + (b - a) * ease(min(1, k / (d * 600))))
        q = int(v // step) if b > a else -int(-v // step)
        if last is not None and q != last: out.append(tt)
        last = q
    return out


# ---------- synth ----------
def tone(f0, f1, dur, decay, kind="sine", noise=0.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / dur); ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-tt / decay)
    if noise: y += noise * np.random.default_rng(1).standard_normal(n) * np.exp(-tt / (decay * .3))
    y[:int(.002 * SR)] *= np.linspace(0, 1, int(.002 * SR))
    return np.stack([y, y], 1).astype(np.float32)


def tick(f=3200): return tone(f, f * .92, .05, .012, noise=.15)
def thud(): x = tone(110, 38, .7, .22); x[:int(.12 * SR)] += .5 * tone(220, 80, .12, .03, noise=.3); return x
def downer(): return np.concatenate([.7 * tone(392, 380, .17, .12), .8 * tone(294, 250, .55, .25)])  # two-note fall for "sadece 2 satış"


# ---------- stems ----------
(HERE / "out").mkdir(exist_ok=True)
VO_AT = {"l1": .12, "l2": 4.0, "l3": 11.3, "l4": 17.75, "l5": 26.85}
vo = np.zeros((N, 2), np.float32)
for k, t0 in VO_AT.items():
    v = load(HERE / f"assets/vo/{k}.mp3", "highpass=f=85,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,"
             "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2")
    add(vo, v, t0, by_peak=False)
vo = to_lufs(vo, -15.5)

START = 14.769 - 2.89
mus = load(HERE / "assets/music/m371.mp3")[int(START * SR):][:N].copy()
fi = int(.12 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
mus = to_lufs(mus, -20.0)
# sidechain-style ducking from the voice envelope (30 ms attack, 280 ms release)
env = np.abs(vo).max(1); hop = 240
blk = env[:len(env) // hop * hop].reshape(-1, hop).max(1)
sm = np.zeros_like(blk); a_att, a_rel = np.exp(-1 / (.03 * SR / hop)), np.exp(-1 / (.28 * SR / hop))
for i in range(1, len(blk)):
    c = a_att if blk[i] > sm[i - 1] else a_rel
    sm[i] = c * sm[i - 1] + (1 - c) * blk[i]
duck = 1 - .58 * np.clip(sm / .06, 0, 1)             # about -7.5 dB under speech
g = np.repeat(duck, hop); g = np.pad(g, (0, N - len(g)), constant_values=g[-1])[:N]
mus *= g[:, None]
fo = int(29.35 * SR); mus[fo:] *= (np.linspace(1, 0, N - fo) ** 1.6)[:, None]

# ---------- SFX ----------
S = {k: load(HERE / f"assets/sfx/{v}.mp3") for k, v in dict(click=1125, key=2568, soft=1117, pop=2364, bubble=2357, whoosh=1490,
                                                       rise=1489, impact=1143, sparkle=3083, success=2865, flip=1485, check=1113).items()}
S = {k: v / (np.abs(v).max() + 1e-9) for k, v in S.items()}
sfx = np.zeros((N, 2), np.float32)
EV = []
# S1 hook
EV += [(.06, "soft", .14), (.3, "soft", .10), (.22, "whoosh", .05)]
EV += [(t, ("tick", 3400 - 60 * i), .07) for i, t in enumerate(count_ticks(.55, 1.7, 25, 10, 1, io))]
EV += [(2.3, "pop", .16), (2.34, "sparkle", .10), (2.86, "rise", .10), (2.86, "impact", .34), (2.86, "thud", .5), (3.68, "whoosh", .10)]
# S2 campaign A
EV += [(3.82, "soft", .12), (4.2, "flip", .09), (5.2, "pop", .18), (5.24, "sparkle", .08)]
EV += [(t, ("tick", 2800 + 12 * i), .06) for i, t in enumerate(count_ticks(5.62, .75, 0, 100, 5))]
EV += [(7.12, "click", .14), (7.16, "sparkle", .09), (7.65, "flip", .08)]
EV += [(t, ("tick", 3000), .06) for t in count_ticks(7.72, .6, 0, 20, 2)]
EV += [(9.05, "whoosh", .05), (9.24, "flip", .08), (10.23, "downer", .26), (10.23, "thud", .32)]
EV += [(t, ("tick", 2600), .05) for t in count_ticks(10.6, .6, 0, 500, 50)]
# S3 campaign B
EV += [(11.0, "whoosh", .11), (11.39, "pop", .13), (11.5, "flip", .08), (12.53, "pop", .17)]
EV += [(t, ("tick", 2900), .06) for t in count_ticks(13.6, .75, 0, 60, 5)]
EV += [(14.3, "flip", .08)] + [(t, ("tick", 3100), .06) for t in count_ticks(14.4, .6, 0, 30, 3)]
EV += [(15.24, "flip", .08), (15.49, "impact", .26), (15.5, "success", .13), (15.55, "sparkle", .10)]
EV += [(t, ("tick", 3300 + 80 * i), .07) for i, t in enumerate(count_ticks(15.39, .6, 0, 8, 1))]
# comparison
EV += [(16.03, "whoosh", .10), (16.33, "soft", .10), (16.46, "soft", .10), (16.55, "impact", .34), (16.55, "thud", .45), (16.58, "sparkle", .11)]
EV += [(t, ("tick", 2500), .05) for t in count_ticks(16.8, .55, 0, 500, 50)] + [(t, ("tick", 3500), .05) for t in count_ticks(16.95, .55, 0, 135, 15)]
# metrics
EV += [(17.62, "whoosh", .09)] + [(t, "pop", .11) for t in [18.12, 18.91, 19.71, 20.37, 21.0]] + [(t + .04, "soft", .07) for t in [18.12, 18.91, 19.71, 20.37, 21.0]]
EV += [(21.4, "whoosh", .04), (22.05, "impact", .17), (22.07, "sparkle", .09), (22.18, "pop", .09), (22.62, "pop", .09), (23.95, "whoosh", .09)]
# question
EV += [(24.46, "click", .14), (24.62, "soft", .09), (25.69, "sparkle", .09), (25.82, "pop", .11)]
# final
EV += [(26.72, "whoosh", .11), (29.3, "rise", .09), (26.96, "soft", .10), (28.08, "soft", .09), (28.5, "flip", .09), (28.87, "pop", .10)]
EV += [(29.3, "impact", .36), (29.3, "thud", .5), (29.33, "sparkle", .12)]

SYN = {"thud": thud(), "downer": downer()}
for t, name, gain in EV:
    if isinstance(name, tuple): s = tick(name[1])
    else: s = SYN.get(name, S.get(name))
    add(sfx, s / (np.abs(s).max() + 1e-9), t, gain)

mix = vo + mus + sfx * 1.0
write(vo, HERE / "out/stem_vo.wav"); write(mus, HERE / "out/stem_music.wav"); write(sfx, HERE / "out/stem_sfx.wav")
raw = HERE / "out/raw.wav"; write(mix, raw)
m = subprocess.run([FF, "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
af = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run([FF, "-v", "error", "-y", "-i", str(raw), "-af", af, "-ar", str(SR), str(HERE / "out/audio.wav")], check=True)
(HERE / "out/_tmp.wav").unlink(missing_ok=True)
print("audio -> out/audio.wav", "| VO", round(lufs(vo), 1), "LUFS, music", round(lufs(mus), 1), "LUFS, sfx", round(lufs(sfx), 1), "LUFS")
