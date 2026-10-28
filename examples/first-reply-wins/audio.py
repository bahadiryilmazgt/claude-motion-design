"""First Reply Wins soundtrack, 100 % synthesized on the film's beat grid (105 BPM, 20 bars = 45.71 s).
Music: warm pads, soft piano, plucks, pulse bass, gentle drums, riser into the drop on beat 44 (the first reply).
SFX: soft glass taps, keys, swooshes, pops, clock ticks, a bell on the first reply, muted thuds on the late replies.
Writes out/audio.wav at -14 LUFS (two-pass loudnorm, true peak -1.3 dB)."""
import json, subprocess
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
SR = 48000
B = 60 / 105
BAR = 4 * B
T = 80 * B
N = int(round(T * SR)) + 1
rng = np.random.default_rng(105)

music = np.zeros((N, 2))     # goes through the reverb
dry = np.zeros((N, 2))       # kick, bass: no reverb
sfx = np.zeros((N, 2))       # light reverb send separately
duck = np.ones(N)            # sidechain envelope for the drop section

mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i0 = int(round(start * SR))
    if i0 >= N: return
    if i0 < 0: sig = sig[-i0:]; i0 = 0
    n = min(len(sig), N - i0)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i0:i0 + n, 0] += sig[:n] * gain * l * 1.414
    buf[i0:i0 + n, 1] += sig[:n] * gain * r * 1.414


def env_adsr(n, a, d, s, r, dur):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((t - dur) / max(r, 1e-4), 0, 1)
    return e * (1 - rel) ** 2


def pad_note(m, dur, cutoff, a=0.7, r=1.6, detune=(-7, 0, 7)):
    n = int((dur + r) * SR); t = np.arange(n) / SR; f0 = mtof(m); out = np.zeros(n)
    for c in detune:
        f = f0 * 2 ** (c / 1200); ph = rng.random() * 6.28
        for h in range(1, 24):
            if f * h > 9000: break
            amp = (1 / h) / (1 + (f * h / cutoff) ** 4)
            if amp < 0.002: continue
            out += amp * np.sin(2 * np.pi * f * h * t + ph * h)
    vib = 1 + 0.08 * np.sin(2 * np.pi * 0.2 * t + rng.random() * 6)
    return out * env_adsr(n, a, 1.0, 0.85, r, dur) * vib / len(detune)


def piano(m, dur=2.8, bright=1.0):
    n = int((dur + 0.6) * SR); t = np.arange(n) / SR; f0 = mtof(m); out = np.zeros(n)
    for h in range(1, 11):
        fh = f0 * h * np.sqrt(1 + 0.00035 * h * h)
        if fh > 12000: break
        amp = (1 / h ** 1.25) * (bright if h > 3 else 1)
        dec = 2.6 / (1 + 0.55 * (h - 1)) * (220 / max(f0, 110)) ** 0.25
        out += amp * np.sin(2 * np.pi * fh * t) * np.exp(-t / dec)
    att = np.clip(t / 0.004, 0, 1)
    hammer = np.exp(-t / 0.01) * rng.standard_normal(n) * 0.02
    rel = np.clip((t - dur) / 0.5, 0, 1)
    return (out * att + hammer) * (1 - rel) ** 2


def pluck(m, bright=1.0, dec=0.32):
    n = int(1.2 * SR); t = np.arange(n) / SR; f0 = mtof(m); out = np.zeros(n)
    for h in range(1, 12):
        if f0 * h > 10000: break
        out += (1 / h) * (bright ** (h - 1)) * np.sin(2 * np.pi * f0 * h * t) * np.exp(-t / (dec / (1 + 0.35 * h)))
    return out * np.clip(t / 0.002, 0, 1)


def sine_bass(m, dur):
    n = int((dur + 0.05) * SR); t = np.arange(n) / SR; f = mtof(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    return s * env_adsr(n, 0.008, 0.18, 0.6, 0.05, dur)


def kick(g=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.28) + 0.15 * np.exp(-t / 0.004) * rng.standard_normal(n)) * g


def noise_hp(n, k=1):
    x = rng.standard_normal(n)
    for _ in range(k): x = np.diff(x, prepend=0)
    return x / (2 ** k)


def hat(dec=0.035):
    n = int(0.15 * SR); t = np.arange(n) / SR
    return noise_hp(n, 2) * np.exp(-t / dec)


def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR
    x = noise_hp(n, 1); e = np.zeros(n)
    for d in (0, 0.011, 0.022): e += np.exp(-np.clip(t - d, 0, None) / 0.012) * (t >= d)
    return x * (e * 0.5 + np.exp(-t / 0.12) * 0.4)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y


def tone(f, dur, dec, att=0.003):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t / dec) * np.clip(t / att, 0, 1)


def bell(f, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for p, a, d in ((1, 1, 1.6), (2.0, .5, 1.0), (2.76, .35, .7), (5.4, .2, .35), (8.9, .08, .2)):
        out += a * np.sin(2 * np.pi * f * p * t) * np.exp(-t / d)
    return out * np.clip(t / 0.002, 0, 1)


def whoosh(dur, peak=0.6, fc=1800):
    n = int(dur * SR); t = np.arange(n) / SR
    x = lowpass(rng.standard_normal(n), fc) - lowpass(rng.standard_normal(n), fc / 6) * 0.5
    e = np.where(t < dur * peak, (t / (dur * peak)) ** 2, np.exp(-(t - dur * peak) / (dur * 0.18)))
    return x * e


def shimmer(dur=1.4, f0=2600, n_p=14, seed=0):
    r = np.random.default_rng(seed); n = int(dur * SR); out = np.zeros(n)
    for k in range(n_p):
        st = int(r.random() * dur * 0.6 * SR); f = f0 * (1 + r.random() * 1.2)
        seg = tone(f, dur - st / SR, 0.25 + r.random() * 0.3)
        out[st:st + len(seg)] += seg * (0.4 + 0.6 * r.random())
    return out / n_p * 3


# ======================= arrangement =======================
CH = {  # bass root, pad voicing, arp tones
    'Bm': (35, [59, 62, 66, 69], [71, 74, 78, 81]),
    'G': (31, [59, 62, 67, 69], [67, 71, 74, 79]),
    'D': (38, [57, 62, 66, 69, 64], [74, 78, 81, 86]),
    'A': (33, [57, 61, 64, 69], [69, 73, 76, 81]),
    'Asus': (33, [57, 62, 64, 69], [69, 74, 76, 81]),
}
BARS = ['Bm', 'G', 'D', 'A', 'Bm', 'G', 'Bm', 'G', 'D', 'A', 'Asus', 'D', 'A', 'G', 'Bm', 'G', 'G', 'A', 'D', 'D']
CUT = [700, 800, 900, 1000, 1100, 1200, 1100, 1300, 1600, 2000, 2500, 3600, 3600, 3400, 650, 600, 1500, 1900, 2300, 2000]
PADG = [.5, .55, .6, .6, .6, .6, .55, .55, .6, .62, .66, .7, .7, .7, .5, .45, .6, .62, .68, .6]

for k, name in enumerate(BARS):
    t0 = k * BAR
    root, voic, arp = CH[name]
    dur = BAR + (2.5 if k == 19 else 0.05)
    for m in voic:
        add(music, t0, pad_note(m, dur, CUT[k], a=0.9 if k in (0, 14, 16) else 0.35, r=2.2 if k == 19 else 1.4), PADG[k] * 0.07, pan=(m % 5 - 2) * 0.18)
    # sub pad an octave under the root
    add(music, t0, pad_note(root + 12, dur, 400, a=.6, detune=(0,)), 0.05 if k not in (14, 15) else 0.035)
    # plucked 8th arps: bars 4-13 and 16-18
    if 4 <= k <= 13 or 16 <= k <= 18:
        pat = [0, 2, 1, 3, 2, 1, 3, 2]
        bright = 0.45 if k < 11 else (0.62 if k < 14 else 0.5)
        g = 0.05 if k < 6 else (0.06 if k < 11 else 0.075)
        if k >= 16: g = 0.045
        for j in range(8):
            if k == 10 and j >= 7: continue  # breath before the drop
            add(music, t0 + j * B / 2, pluck(arp[pat[j]], bright), g * (1.0 if j % 2 == 0 else 0.72), pan=0.35 if j % 2 else -0.35)
    # pulse bass: race and drop
    if 6 <= k <= 13:
        steps = 8
        for j in range(steps):
            if k == 10 and j >= 7: continue
            g = 0.16 if k < 11 else 0.2
            add(dry, t0 + j * B / 2, sine_bass(root + 12 if k < 11 else root + 12, B / 2 * 0.85), g * (1 if j % 2 == 0 else 0.7))
    # drums
    if 8 <= k <= 10:   # heartbeat kick on 1 and 3 + 16th ticking hats growing
        for j in (0, 2):
            add(dry, t0 + j * B, kick(), 0.32 + 0.05 * (k - 8))
        for j in range(16):
            if k == 10 and j >= 14: continue
            add(music, t0 + j * B / 4, hat(0.02), (0.02 + 0.012 * (k - 8)) * (1.3 if j % 4 == 2 else 0.8), pan=0.25)
    if 11 <= k <= 13:  # drop groove
        for j in range(4):
            add(dry, t0 + j * B, kick(), 0.42)
            i0 = int((t0 + j * B) * SR); n = int(0.42 * SR); tt = np.arange(min(n, N - i0)) / SR
            duck[i0:i0 + len(tt)] = np.minimum(duck[i0:i0 + len(tt)], 1 - 0.45 * np.exp(-tt / 0.16))
        for j in (1, 3): add(music, t0 + j * B, clap(), 0.12)
        for j in range(8): add(music, t0 + j * B / 2 + B / 2 * (j % 2 == 0) * 0, hat(0.03 if j % 2 else 0.018), 0.05 if j % 2 else 0.025, pan=-0.2)
    if 16 <= k <= 18:  # soft shaker in the ending
        for j in range(8): add(music, t0 + j * B / 2, hat(0.05), 0.018 if j % 2 else 0.01, pan=0.3)

# piano lines (beats): intro motif, sparse in the race, brighter on the drop, chords in the ending
PIANO = [(0, 78, .9), (2.5, 76, .6), (3, 74, .7), (4, 74, .8), (6, 71, .6), (8, 69, .7), (9.5, 74, .6), (11, 78, .7), (12, 76, .8), (14, 73, .6),
         (16, 74, .5), (18, 78, .5), (20, 71, .45), (22, 74, .45),
         (44, 78, 1), (44, 86, .45), (45.5, 81, .7), (46, 83, .6), (47, 81, .6), (48, 76, .8), (49.5, 81, .6), (50, 85, .6), (51, 88, .5),
         (52, 79, .8), (53.5, 83, .6), (54, 86, .6), (55, 83, .5),
         (56, 71, .55), (58, 74, .45), (60, 67, .5), (62, 71, .4)]
for bt, m, v in PIANO: add(music, bt * B, piano(m, 2.6 if bt < 56 else 3.2), 0.11 * v, pan=0.1)
for bt, chord, v in ((64, [55, 59, 62, 67, 71], .8), (66.6, [59, 62, 67], .5), (68, [57, 61, 64, 69, 73], .8), (70.6, [61, 64, 69], .5),
                     (72, [50, 57, 62, 66, 69, 74], 1.0), (74.5, [66, 69, 74, 78], .55), (76, [50, 57, 62, 66, 69, 76], .8), (78, [74, 78, 81, 86], .5)):
    for i, m in enumerate(chord): add(music, bt * B + i * 0.012, piano(m, 3.6), 0.07 * v, pan=(i - 2) * 0.12)

# riser into the drop (bars 9.5-11), silence on the last half beat
rs, re_ = 38 * B, 43.6 * B
n = int((re_ - rs) * SR); tt = np.arange(n) / SR; u = tt / tt[-1]
riser = noise_hp(n, 1) * u ** 2.5 * 0.5 + np.sin(2 * np.pi * np.cumsum(300 + 900 * u ** 2) / SR) * u ** 3 * 0.12
add(music, rs, riser, 0.12)
gap0, gap1 = int(43.62 * B * SR), int(44 * B * SR)
fadeg = np.ones(N); fadeg[gap0:gap1] = np.linspace(1, 0.12, gap1 - gap0) ** 2

# ======================= SFX (beats) =======================
def glass(): return tone(2093, .6, .16) * .6 + tone(3136, .6, .1) * .4 + tone(4186, .6, .05) * .2
def pop(f=900): n = int(.12 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(f + 900 * t / .12) / SR) * np.exp(-t / .03)
def key(): n = int(.04 * SR); t = np.arange(n) / SR; return noise_hp(n, 1) * np.exp(-t / .006) + tone(1700, .04, .008) * .3
def tick(): return tone(2400, .05, .006) * .7 + tone(1200, .05, .01) * .5
def thud(): return lowpass(tone(150, .5, .12) + tone(220, .5, .06) * .5, 600)

S = []
for bt in (2, 9.5, 18.5, 25, 33.5, 45): S.append((bt, glass(), .05, 0))
S += [(7, tone(1500, .3, .02) * .6 + tone(180, .3, .06), .12, 0), (8, whoosh(.55, .5, 2600), .06, .3)]
for c in range(0, 66, 2): S.append((9.3 + 4.3 * c / 66 + (c % 3) * 0.02, key(), .05, 0.1))
S += [(13.9, whoosh(.35, .7, 3000), .06, 0), (14, pop(700), .12, .2), (14.5, tone(2800, .2, .05) * .5, .03, .2)]
S += [(15.6, whoosh(1.0, .6, 1800), .07, 0), (17.1, shimmer(1.2, 2400, 10, 1), .05, 0)]
for i in range(5): S.append((17.1 + i * .2 + 1.3, pop(1100 + i * 120), .06, (i - 2) * .3))
for bt in range(19, 44): S.append((bt, tick(), .02 + .025 * (bt - 19) / 25, .15 if bt % 2 else -.15))
for li, a1, _ in ((0, 27, 0), (3, 31, 0), (4, 34.6, 0), (1, 37.4, 0), (2, 40, 0)): S.append((a1, tone(1600, .15, .03) * .5 + tone(2000, .15, .02) * .4, .035, (li - 2) * .3))
S += [(44, bell(1318.5, 3.5), .09, 0), (44, bell(659.25, 3), .05, 0), (44, shimmer(2.2, 2200, 18, 2), .07, 0), (44, tone(55, 1.2, .35), .25, 0)]
S += [(44.5, whoosh(1.2, .55, 2200), .06, 0), (46.6, pop(900), .08, -.2), (47.2, tone(2600, .15, .04) * .6, .04, -.2), (50, pop(750), .08, .2)]
S += [(51.4, whoosh(.6, .7, 2400), .06, 0), (52.4, shimmer(1.6, 2800, 16, 3), .07, 0), (52.4, tone(1046.5, 1, .3) * .5 + tone(1568, 1, .3) * .35, .06, 0)]
S += [(55.8, whoosh(1.0, .4, 1600), .06, 0)]
for li, bt in ((0, 57), (1, 58), (3, 59), (4, 60)): S.append((bt, thud(), .14, (li - 2) * .3))
S += [(58, tone(73.4, 2.6, .9) + tone(146.8, 2.6, .5) * .3, .12, 0)]
S += [(64, whoosh(1.6, .5, 1400), .07, 0)]
for bt, f in ((64.6, 587.3), (66.6, 659.3), (68.6, 740)): S += [(bt, bell(f, 2.5), .05, 0), (bt, tone(f / 4, 1, .3), .08, 0)]
S += [(73.6, shimmer(1.8, 2600, 16, 4), .05, 0), (76.5, shimmer(2.4, 3000, 22, 5), .06, 0), (76, glass(), .04, 0)]
for bt, sig, g, pan in S: add(sfx, bt * B, sig, g, pan)

# ======================= mix =======================
def reverb(x, secs=2.4, wet=0.28, pre=0.02):
    n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (secs / 6.9) * 1.0)
        ir = np.concatenate([np.zeros(int(pre * SR)), ir]); ir /= np.sqrt(np.sum(ir ** 2))
        L = 1 << int(np.ceil(np.log2(len(x) + len(ir))))
        y = np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir, L), L)[:len(x)]
        out[:, c] = y
    return x * (1 - wet) + out * wet * 1.6

mus = reverb(music, 2.6, 0.32) * duck[:, None] * fadeg[:, None]
mixed = mus + dry * duck[:, None] ** 0.3 * fadeg[:, None] + reverb(sfx, 1.4, 0.22)
mixed[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
f0 = int((T - 1.4) * SR); mixed[f0:] *= np.linspace(1, 0, N - f0)[:, None] ** 1.6
mixed /= np.abs(mixed).max() + 1e-9
(HERE / 'out').mkdir(exist_ok=True)
rawp = HERE / 'out/raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f64le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', str(rawp)], input=(mixed * 0.8).astype(np.float64).tobytes(), check=True)
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(rawp), '-af', 'loudnorm=I=-14:TP=-1.3:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
af = (f"loudnorm=I=-14:TP=-1.3:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(rawp), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', str(HERE / 'out/audio.wav')], check=True)
print('audio -> out/audio.wav', round(T, 3), 's')
