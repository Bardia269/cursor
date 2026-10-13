"""Synthèse des sons du film Fastamp (numpy uniquement) : effets + musique originale.

Tout est généré ici, donc sans problème de droits pour un usage commercial.
Usage : python3 scripts/make-audio.py <durée_musique_en_secondes> [cues.json]
"""
import json
import sys
import wave

import numpy as np

SR = 48000
OUT = "public/audio/"
rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, cutoff):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    resp = 1 / np.sqrt(1 + (f / cutoff) ** 4)
    if X.ndim == 2:
        resp = resp[:, None]
    return np.fft.irfft(X * resp, n=x.shape[0], axis=0)


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def env(n, a, d, sustain_curve=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    e[na:] = np.exp(-np.arange(n - na) / (d * SR))
    return e


def save(name, x, stereo_width=0.0):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        if stereo_width:
            d = int(0.011 * SR)
            r = np.concatenate([np.zeros(d), x[:-d]])
            x = np.stack([x, x * (1 - stereo_width) + r * stereo_width], axis=1)
        else:
            x = np.stack([x, x], axis=1)
    peak = np.max(np.abs(x)) or 1
    x = x / peak * 0.89
    data = (x * 32767).astype("<i2")
    with wave.open(OUT + name + ".wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ---------- Effets ----------

def sfx_stamp():
    # Tampon encreur : corps grave + claquement papier, sans agressivité.
    t = t_axis(0.45)
    body = np.sin(2 * np.pi * (58 + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 14)
    knock = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 40) * 0.35
    paper = bandpass(rng.standard_normal(len(t)), 900, 4500) * np.exp(-t * 60) * 0.5
    return body + knock + paper


def sfx_pop():
    t = t_axis(0.5)
    f = 660 + 240 * np.exp(-t * 40)
    tone = np.sin(2 * np.pi * f * t) * np.exp(-t * 9)
    tone += 0.35 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 14)
    click = bandpass(rng.standard_normal(len(t)), 2000, 7000) * np.exp(-t * 200) * 0.3
    return tone + click


def sfx_click():
    t = t_axis(0.12)
    x = bandpass(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 120)
    x += np.sin(2 * np.pi * 1300 * t) * np.exp(-t * 90) * 0.5
    return x


def sfx_tick():
    t = t_axis(0.06)
    return bandpass(rng.standard_normal(len(t)), 2500, 8000) * np.exp(-t * 250)


def sfx_whoosh():
    dur = 0.9
    t = t_axis(dur)
    n = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    # balayage de filtre par segments
    segs = 18
    for i in range(segs):
        a, b = int(i * len(t) / segs), int((i + 1) * len(t) / segs)
        c = 300 + 3200 * (i / segs) ** 1.6
        seg = bandpass(n, c * 0.6, c * 1.6)[a:b]
        out[a:b] = seg
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return lowpass(out * shape, 6000)


def sfx_swipe():
    t = t_axis(0.5)
    n = bandpass(rng.standard_normal(len(t)), 500, 2600)
    return n * np.sin(np.pi * t / 0.5) ** 2 * 0.8


def sfx_chime():
    t = t_axis(1.4)
    a = np.sin(2 * np.pi * 987.8 * t) * np.exp(-t * 4)
    b = np.concatenate([np.zeros(int(0.12 * SR)), (np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 3.5))[: len(t) - int(0.12 * SR)]])
    harm = 0.2 * np.sin(2 * np.pi * 987.8 * 3 * t) * np.exp(-t * 9)
    return (a + b * 0.9 + harm) * np.minimum(1, t / 0.004)


def sfx_scan():
    t = t_axis(0.6)
    f = 700 + 500 * t / 0.6
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.6) * 0.5
    return x


# ---------- Musique ----------

def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def music(total):
    bpm = 120.0
    beat = 60 / bpm
    n = int(total * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    # Progression chaleureuse : Fmaj9 – Am7 – Dm9 – Bbmaj9 (2 mesures chacune).
    chords = [
        [41, 53, 57, 60, 64, 67],
        [45, 52, 55, 60, 64, 67],
        [38, 53, 57, 60, 64, 69],
        [46, 53, 57, 62, 65, 69],
    ]
    bar = beat * 4
    chord_len = bar * 2

    def add(sig, start, pan=0.0, gain=1.0):
        a = int(start * SR)
        if a >= n:
            return
        b = min(n, a + len(sig))
        s = sig[: b - a] * gain
        L[a:b] += s * (1 - pan) * 0.5 * 2 ** 0.5
        R[a:b] += s * (1 + pan) * 0.5 * 2 ** 0.5

    # Nappe
    ci = 0
    t0 = 0.0
    while t0 < total:
        ch = chords[ci % 4]
        dur = chord_len + 0.6
        t = t_axis(dur)
        e = np.minimum(1, t / 0.9) * np.minimum(1, (dur - t) / 0.7)
        for j, m in enumerate(ch[1:]):
            f = note_hz(m)
            for det, pan in ((-0.12, -0.5), (0.12, 0.5)):
                ff = f * 2 ** (det / 12 / 4)
                sig = (np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(2 * np.pi * 2 * ff * t)) * e * 0.05
                add(sig, t0, pan)
        # basse
        f = note_hz(ch[0])
        sig = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * e * 0.16
        add(sig, t0)
        t0 += chord_len
        ci += 1

    # Arpège pluck (croches), entre après l'ouverture
    step = beat / 2
    k = 0
    tt = bar * 2
    pattern = [0, 2, 4, 3, 1, 4, 2, 5]
    while tt < total - 1:
        ch = chords[int(tt // chord_len) % 4]
        m = ch[1 + pattern[k % 8] % 5] + 12
        t = t_axis(0.6)
        f = note_hz(m)
        sig = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 12)) * np.exp(-t * 7) * 0.07
        vel = 0.75 + 0.25 * ((k % 4) == 0)
        add(sig, tt, pan=0.35 * np.sin(k * 0.9), gain=vel)
        tt += step
        k += 1

    # Rythme doux : grosse caisse feutrée (temps 1 et 3) + shaker en contretemps, à partir de 8 s
    tt = bar * 4
    i = 0
    end_beats = total - bar * 2
    while tt < end_beats:
        t = t_axis(0.4)
        if i % 2 == 0:
            kick = np.sin(2 * np.pi * (48 + 60 * np.exp(-t * 35)) * t) * np.exp(-t * 9) * 0.32
            add(kick, tt)
        sh = highpass(rng.standard_normal(int(0.08 * SR)), 6000) * np.exp(-np.arange(int(0.08 * SR)) / SR * 60) * 0.03
        add(sh, tt + beat / 2, pan=0.3)
        tt += beat
        i += 1

    mix = np.stack([L, R], axis=1)
    mix = lowpass(mix, 9000)
    # réverbération courte (échos décroissants), discrète
    for d, g in ((0.093, 0.22), (0.171, 0.16), (0.263, 0.11), (0.377, 0.07)):
        s = int(d * SR)
        mix[s:, 0] += mix[:-s, 1] * g
        mix[s:, 1] += mix[:-s, 0] * g
    # fondu d'entrée/sortie
    t = t_axis(total)
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (total - t) / 3.0)
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.4) / 1.4
    return mix


if __name__ == "__main__":
    total = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
    save("stamp", sfx_stamp())
    save("pop", sfx_pop(), 0.3)
    save("click", sfx_click())
    save("tick", sfx_tick())
    save("whoosh", sfx_whoosh(), 0.5)
    save("swipe", sfx_swipe(), 0.4)
    save("chime", sfx_chime(), 0.4)
    save("scan", sfx_scan(), 0.3)
    save("music", music(total))
    print("audio ok", total)
