import json, os, subprocess, sys, uuid
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
BPM = 128
BEAT = 60 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
SND = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
NS = uuid.UUID("6f0a4b2e-9c1d-4e7a-8b3f-2d5c6e7f8a90")
folders = {}


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    nz = np.nonzero(np.abs(x) > 1e-3)[0]
    if len(nz):
        x = x[max(0, nz[0] - 16):]
    x = x / (np.max(np.abs(x)) + 1e-12)
    loud = np.nonzero(np.abs(x) > 10 ** (-54 / 20))[0]
    if len(loud):
        x = x[:loud[-1] + int(SR * 0.01)]
    return x


def fade_tail(x, ms=8):
    n = min(len(x), int(SR * ms / 1000))
    if n > 0:
        x = x.copy()
        x[-n:] *= np.linspace(1, 0, n)[:, None] if x.ndim == 2 else np.linspace(1, 0, n)
    return x


def finish(x, peak=0.89):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) + 1e-12
    return fade_tail(x * (peak / m))


def save(folder, name, x, bpm=0):
    x = finish(x)
    key = folder + "/" + name
    uid = str(uuid.uuid5(NS, key))
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    wavfile.write(os.path.join(OUT, uid), SR, pcm)
    dur = len(x) / SR
    folders.setdefault(folder, []).append({"uuid": uid, "name": name, "bpm": bpm, "duration": round(dur, 4), "sample_rate": SR})
    return uid


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def polyblep_saw(freq, n, phase0=0.0):
    dt = freq / SR
    t = (phase0 + dt * np.arange(n)) % 1.0
    y = 2 * t - 1
    m = t < dt
    x = t[m] / dt
    y[m] -= 2 * x - x * x - 1
    m = t > 1 - dt
    x = (t[m] - 1) / dt
    y[m] -= x * x + 2 * x + 1
    return y


def adsr(n, a, d, s, r, gate):
    t = np.arange(n) / SR
    env = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = t >= gate
    if np.any(rel):
        g = env[np.argmax(rel)] if np.argmax(rel) > 0 else s
        env[rel] = g * np.exp(-(t[rel] - gate) / max(r, 1e-4))
    return env


def lowpass_sweep(x, cutoffs, q=0.7, block=256):
    y = np.zeros_like(x)
    zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(cutoffs[min(i, len(cutoffs) - 1)], 30, SR * 0.45))
        sos = signal.butter(2, fc, btype="low", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        y[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return y


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, btype="high", fs=SR, output="sos"), x, axis=0)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, btype="low", fs=SR, output="sos"), x, axis=0)


def make_ir(seconds=2.8, damp=5000):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
    ir = lp(ir, damp)
    ir[:int(SR * 0.012)] = 0
    return ir / np.sqrt(np.sum(ir ** 2, axis=0))


IR = make_ir()


def reverb(x, wet=0.25, ir=IR):
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    tail = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], axis=1)
    return x + wet * tail


def stereo(x):
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def pump(n, depth=0.7, recover=0.32, offset=0.0):
    t = (np.arange(n) / SR + offset) % BEAT
    g = np.where(t < recover, 1 - depth * (1 - t / recover) ** 2, 1.0)
    return g


def glue(x, drive=1.6):
    return np.tanh(x * drive) / np.tanh(drive)


def render(events, total, voice, channels=2):
    out = np.zeros((int(total * SR) + SR * 3, channels))
    for start, dur, arg in events:
        v = voice(arg, dur)
        if v.ndim == 1:
            v = stereo(v) if channels == 2 else v[:, None]
        i = int(start * SR)
        out[i:i + len(v)] += v[:len(out) - i]
    return out


# ---------------- drums (CC0) ----------------
TR8 = os.path.join(SND, "mck", "TR8")
F808 = os.path.join(SND, "f808")
d = lambda sub, f: load(os.path.join(TR8, sub, f))

kick909 = [d("BD", "004_909_Bass_Drum_1.wav"), d("BD", "005_909_Bass_Drum_2.wav"), d("BD", "006_909_Bass_Drum_3.wav")]
kick909a = d("BD", "012_909_AttackBD_1.wav")
kick808 = d("BD", "001_808_Bass_Drum_1.wav")
kick808l = d("BD", "007_808_Bass_Drum_Long_1.wav")
clap909 = d("PERC", "019_909_Hand_Clap.wav")
clap909l = d("PERC", "020_909_Hand_Clap_Long.wav")
clap808 = d("PERC", "017_808_Hand_Clap.wav")
snare909 = [d("SD", "005_909_Snare_Drum_1.wav"), d("SD", "006_909_Snare_Drum_2.wav"), d("SD", "007_909_Snare_Drum_3.wav")]
snare808 = d("SD", "001_808_Snare_Drum_1.wav")
snap = d("PERC", "024_808_Finger_Snap.wav")
ch909 = d("HATS", "008_909_Closed_HiHat.wav")
chs909 = d("HATS", "010_909_Closed_HiHat_Short.wav")
oh909 = d("HATS", "007_909_Open_HiHat.wav")
ch808 = d("HATS", "002_808_Closed_HiHat.wav")
oh808 = d("HATS", "001_808_Open_HiHat.wav")
ride909 = d("HATS", "026_909_Ride_Cymbal.wav")
crash909 = d("HATS", "020_909_Crash_Cymbal.wav")
shaker = d("PERC", "026_808_Maracas.wav")
tamb = d("PERC", "036_707_Tambourine.wav")
rim909 = d("PERC", "009_909_Rim_Shot.wav")
cowbell = d("PERC", "033_808_Cowbell.wav")
conga = d("PERC", "001_727_Low_Conga.wav")
claves = d("PERC", "010_808_Claves_1.wav")
fischer_bd = load(os.path.join(F808, "bd8", "BD1050.WAV"))


def festival_kick(base, sub_hz=55, drive=2.4, length=0.45):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = sub_hz + 160 * np.exp(-t / 0.018)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
    b = np.zeros(n)
    b[:min(n, len(base))] = base[:n]
    x = 0.8 * hp(b, 90) + sub
    return glue(x, drive)


K = "Trommer/Kick"
save(K, "Festival Kick", festival_kick(kick909[0]))
save(K, "Festival Kick (hard)", festival_kick(kick909a, sub_hz=55, drive=4.0, length=0.42))
save(K, "909 Kick 1", kick909[0])
save(K, "909 Kick 2", kick909[1])
save(K, "909 Kick 3", kick909[2])
save(K, "909 Attack Kick", kick909a)
save(K, "808 Kick", kick808)
save(K, "808 Kick lang", kick808l)
save(K, "808 Kick (ekte maskin)", fischer_bd)

big_clap_dry = np.zeros(int(SR * 0.6))
big_clap_dry[:len(clap909l)] += clap909l[:len(big_clap_dry)]
big_clap_dry[:len(clap808)] += 0.6 * clap808[:len(big_clap_dry)]
C = "Trommer/Clap og snare"
save(C, "Festival Clap", reverb(hp(big_clap_dry, 300), wet=0.35))
save(C, "909 Clap", clap909)
save(C, "909 Clap lang", clap909l)
save(C, "808 Clap", clap808)
save(C, "909 Snare 1", snare909[0])
save(C, "909 Snare 2", snare909[1])
save(C, "909 Snare 3", snare909[2])
save(C, "808 Snare", snare808)
save(C, "Finger-snap", reverb(snap, 0.3))

H = "Trommer/Hi-hats og cymbaler"
save(H, "909 Closed Hat", ch909)
save(H, "909 Closed Hat kort", chs909)
save(H, "909 Open Hat", oh909)
save(H, "808 Closed Hat", ch808)
save(H, "808 Open Hat", oh808)
save(H, "909 Ride", ride909)
save(H, "909 Crash", crash909)
save(H, "Crash med hall", reverb(crash909, 0.5))

P = "Trommer/Perkusjon"
save(P, "Shaker", shaker)
save(P, "Tamburin", tamb)
save(P, "909 Rim", rim909)
save(P, "Cowbell", cowbell)
save(P, "Conga", conga)
save(P, "Claves", claves)

# ---------------- drum loops ----------------


def place(out, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(out):
        return
    seg = x[:len(out) - i] * gain
    if out.ndim == 2 and seg.ndim == 1:
        seg = seg[:, None]
    out[i:i + len(seg)] += seg


def drum_loop(bars, parts):
    n = int(bars * BAR * SR)
    out = np.zeros((n + SR, 2))
    for sample, pattern, gain in parts:
        for b in range(bars):
            for s, ch in enumerate(pattern):
                if ch != "-":
                    place(out, sample, b * BAR + s * STEP, gain * (1.0 if ch == "x" else 0.55))
    return out[:n]


fk = festival_kick(kick909[0])


def shorten(x, seconds):
    x = x[:int(SR * seconds)].copy()
    n = min(len(x), int(SR * 0.04))
    x[-n:] *= np.linspace(1, 0, n)
    return x


oh_short = shorten(oh909, 0.22)
ch_short = shorten(ch909, 0.06)
fc = reverb(hp(big_clap_dry, 300), wet=0.3)
L = "Loops 128 BPM/Trommer"
save(L, "House-beat full", glue(drum_loop(4, [
    (fk, "x---x---x---x---", 1.0), (fc, "----x-------x---", 0.75), (oh_short, "--x---x---x---x-", 0.4),
    (ch_short, "x-o-x-o-x-o-x-o-", 0.12), (shaker, "-o-o-o-o-o-o-o-o", 0.18), (ride909, "x---x---x---x---", 0.08)]), 1.15), BPM)
save(L, "Kick og clap", drum_loop(4, [(fk, "x---x---x---x---", 1.0), (fc, "----x-------x---", 0.7)]), BPM)
save(L, "Bare kick", drum_loop(4, [(fk, "x---x---x---x---", 1.0)]), BPM)
save(L, "Topp-loop (hats og shaker)", drum_loop(4, [
    (oh_short, "--x---x---x---x-", 0.5), (ch_short, "x-o-x-o-x-o-x-o-", 0.15), (shaker, "-o-o-o-o-o-o-o-o", 0.22),
    (ride909, "x---x---x---x---", 0.1)]), BPM)


def snare_roll(bars):
    n = int(bars * BAR * SR)
    out = np.zeros((n + SR, 2))
    total = bars * 16
    for s in range(total):
        p = s / total
        every = 4 if p < 0.5 else 2 if p < 0.75 else 1
        if s % every == 0:
            sn = snare909[0]
            rate = 1 + 0.5 * p
            idx = np.arange(0, len(sn) - 1, rate)
            pitched = np.interp(idx, np.arange(len(sn)), sn)
            place(out, pitched, s * STEP, 0.25 + 0.75 * p ** 1.5)
    out = out[:n]
    cut = np.interp(np.arange(n), [0, n], [200, 2000])
    for c in range(2):
        out[:, c] = out[:, c] - lowpass_sweep(out[:, c], cut)
    return reverb(out, 0.3)


save(L, "Snare-virvel bygg-opp (4 takter)", snare_roll(4), BPM)
save(L, "Snare-virvel bygg-opp (8 takter)", snare_roll(8), BPM)

# ---------------- synths ----------------
A_MINOR = [0, 2, 3, 5, 7, 8, 10]
PROG = [0, 5, 2, 6]
ROOT = 57


def deg_midi(deg, base=ROOT):
    o, r = divmod(deg, 7)
    return base + A_MINOR[r] + 12 * o


def chord_notes(deg):
    notes = [deg_midi(deg + i) for i in (0, 2, 4)]
    notes = [n - 12 if n > 69 else n for n in notes]
    return sorted(notes) + [deg_midi(deg) + 12 if deg_midi(deg) + 12 <= 76 else deg_midi(deg)]


def supersaw(midi, dur, voices=7, spread=28, cutoff=6500, a=0.01, r=0.35, level=1.0):
    n = int((dur + r * 4) * SR)
    out = np.zeros((n, 2))
    for v in range(voices):
        det = spread * (2 * v / (voices - 1) - 1) if voices > 1 else 0
        w = polyblep_saw(mtof(midi) * 2 ** (det / 1200), n, rng.random())
        pan = 0.85 * (2 * v / (voices - 1) - 1) if voices > 1 else 0
        out[:, 0] += w * np.sqrt((1 - pan) / 2)
        out[:, 1] += w * np.sqrt((1 + pan) / 2)
    out /= np.sqrt(voices)
    out = lp(out, cutoff)
    env = adsr(n, a, 0.4, 0.85, r, dur)
    return out * env[:, None] * level


def chords_loop(rhythm, voice_kw, do_pump, wet=0.3):
    events = []
    for b, deg in enumerate(PROG):
        for s, l in rhythm:
            events.append((b * BAR + s * STEP, l * STEP, deg))
    def voice(deg, dur):
        return sum(supersaw(m, dur, **voice_kw) for m in chord_notes(deg))
    out = render(events, 4 * BAR, voice)
    out = reverb(out, wet)
    n = int(4 * BAR * SR)
    tail = out[n:n + int(SR * 0.5)]
    out = out[:n].copy()
    out[:len(tail)] += tail * np.linspace(1, 0, len(tail))[:, None]
    if do_pump:
        out *= pump(n)[:, None]
    return glue(out, 1.3)


S = "Loops 128 BPM/Akkorder (A-moll)"
full = [(0, 16)]
save(S, "Supersaw-akkorder med pump", chords_loop(full, {}, True), BPM)
save(S, "Supersaw-akkorder uten pump", chords_loop(full, {}, False), BPM)
save(S, "Offbeat-stabs", chords_loop([(2, 1.5), (6, 1.5), (10, 1.5), (14, 1.5)], {"cutoff": 4000, "r": 0.15}, False, 0.35), BPM)
save(S, "Festival-stabs (rytme)", chords_loop([(0, 2), (3, 2), (6, 2), (10, 2), (12, 2)], {"cutoff": 5000, "r": 0.2}, True, 0.35), BPM)
save(S, "Myk pad", chords_loop(full, {"voices": 5, "spread": 14, "cutoff": 1800, "a": 0.6, "r": 1.2, "level": 0.8}, False, 0.5), BPM)


def bass_voice(midi, dur, cutoff0=1800, cutoff1=260):
    n = int((dur + 0.08) * SR)
    w = polyblep_saw(mtof(midi), n) + 0.7 * np.sin(2 * np.pi * mtof(midi) * np.arange(n) / SR)
    t = np.arange(n) / SR
    cut = cutoff1 + (cutoff0 - cutoff1) * np.exp(-t / 0.09)
    w = lowpass_sweep(w, cut, block=128)
    env = adsr(n, 0.004, 0.2, 0.8, 0.03, dur)
    return w * env


def bass_loop(rhythm, base=33, do_pump=False):
    events = [(b * BAR + s * STEP, l * STEP, deg_midi(deg, base)) for b, deg in enumerate(PROG) for s, l in rhythm]
    out = render(events, 4 * BAR, bass_voice, channels=1)[:int(4 * BAR * SR), 0]
    if do_pump:
        out *= pump(len(out), 0.5)
    return glue(out, 1.5)


B = "Loops 128 BPM/Bass (A-moll)"
save(B, "Offbeat-bass", bass_loop([(2, 2), (6, 2), (10, 2), (14, 2)]), BPM)
save(B, "Rullende bass", bass_loop([(2, 1), (3, 1), (6, 1), (7, 1), (10, 1), (11, 1), (14, 1), (15, 1)]), BPM)
save(B, "Sub-bass lange toner", bass_loop([(0, 16)], do_pump=True), BPM)

MEL = [(0, 4, 2), (3, 7, 1), (6, 6, 2), (10, 4, 2), (14, 2, 2), (16, 5, 2), (19, 7, 1), (22, 9, 2), (26, 7, 2), (30, 5, 2),
       (32, 4, 2), (35, 6, 1), (38, 9, 2), (42, 6, 2), (46, 4, 2), (48, 3, 2), (51, 6, 1), (54, 8, 2), (58, 6, 3), (62, 1, 2)]


def pluck_voice(midi, dur):
    n = int((dur + 0.4) * SR)
    w = sum(polyblep_saw(mtof(midi) * 2 ** (c / 1200), n, rng.random()) for c in (-9, 0, 9)) / 3
    t = np.arange(n) / SR
    w = lowpass_sweep(w, 600 + 6000 * np.exp(-t / 0.12), block=128)
    env = np.exp(-t / 0.28) * np.minimum(1, t / 0.002)
    return w * env


def melody_loop(voice, base=69, wet=0.35, delay=True, arp=False):
    if arp:
        events = []
        for b, deg in enumerate(PROG):
            cyc = [deg, deg + 2, deg + 4, deg + 7]
            for s in range(0, 16, 2):
                events.append((b * BAR + s * STEP, 2 * STEP, deg_midi(cyc[(s // 2) % 4], base - 12)))
    else:
        events = [(s * STEP, l * STEP, deg_midi(r, base)) for s, r, l in MEL]
    out = render(events, 4 * BAR, voice)
    if delay:
        dl = int(BEAT * 0.75 * SR)
        echo = np.zeros_like(out)
        echo[dl:, 0] = out[:-dl, 0] * 0.35
        echo[2 * dl:, 1] = out[:-2 * dl, 1] * 0.25
        out = out + lp(echo, 3500)
    out = reverb(out, wet)
    return out[:int(4 * BAR * SR)]


M = "Loops 128 BPM/Melodi (A-moll)"
save(M, "Pluck-melodi", melody_loop(pluck_voice), BPM)
save(M, "Pluck-arpeggio", melody_loop(pluck_voice, arp=True), BPM)
save(M, "Supersaw-lead (drop)", glue(melody_loop(lambda m, dur: supersaw(m, dur, voices=7, spread=22, cutoff=7000, r=0.12), base=69, wet=0.3), 1.4), BPM)

# ---------------- FX ----------------
F = "Effekter"


def noise_riser(bars):
    n = int(bars * BAR * SR)
    x = rng.standard_normal((n, 2))
    t = np.linspace(0, 1, n)
    cut = 300 * (40 ** t)
    y = np.stack([lowpass_sweep(x[:, c], cut) for c in range(2)], axis=1)
    y = hp(y, 150) * (t ** 2)[:, None]
    return reverb(y, 0.3)


save(F, "Riser hvit støy (4 takter)", noise_riser(4), BPM)
save(F, "Riser hvit støy (8 takter)", noise_riser(8), BPM)


def pitch_riser(bars):
    n = int(bars * BAR * SR)
    t = np.linspace(0, 1, n)
    f = 110 * (16 ** t)
    ph = np.cumsum(f) / SR
    w = sum(np.sign(np.sin(2 * np.pi * (ph * (1 + 0.006 * k)))) for k in (-1, 0, 1)) / 3
    w = lp(w, 4000) * (0.2 + 0.8 * t ** 1.5)
    return reverb(stereo(w), 0.35)


save(F, "Pitch-riser (8 takter)", pitch_riser(8), BPM)


def downlifter(bars=2):
    n = int(bars * BAR * SR)
    x = rng.standard_normal(n)
    t = np.linspace(0, 1, n)
    y = lowpass_sweep(x, 9000 * (0.02 ** t)) * (1 - t) ** 1.5
    return reverb(stereo(y), 0.4)


save(F, "Downlifter (2 takter)", downlifter(), BPM)
rev = reverb(crash909, 0.5)[::-1]
save(F, "Reverse crash", rev[-int(BAR * SR):] if len(rev) > BAR * SR else rev)


def impact():
    n = int(SR * 3.0)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t / 0.15)) / SR) * np.exp(-t / 0.9)
    crack = lp(rng.standard_normal(n), 2500) * np.exp(-t / 0.08)
    return glue(reverb(boom + 0.4 * crack, 0.45), 1.8)


save(F, "Impact (boom)", impact())
n = int(SR * 2.0)
t = np.arange(n) / SR
save(F, "Sub drop", glue(np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t / 0.7) + 25) / SR) * np.exp(-t / 1.2), 1.5))

order = ["Trommer/Kick", "Trommer/Clap og snare", "Trommer/Hi-hats og cymbaler", "Trommer/Perkusjon",
         "Loops 128 BPM/Trommer", "Loops 128 BPM/Akkorder (A-moll)", "Loops 128 BPM/Bass (A-moll)",
         "Loops 128 BPM/Melodi (A-moll)", "Effekter"]
tree = []
for key in order:
    parts = key.split("/")
    level = tree
    for i, p in enumerate(parts):
        node = next((f for f in level if f["name"] == p), None)
        if node is None:
            node = {"name": p}
            level.append(node)
        if i == len(parts) - 1:
            node["samples"] = folders[key]
        else:
            level = node.setdefault("folders", [])
with open(os.path.join(OUT, "index.json"), "w") as fh:
    json.dump({"version": 1, "updatedAt": "2026-10-28", "folders": tree}, fh, ensure_ascii=False, indent=1)
print(sum(len(v) for v in folders.values()), "samples")
