"""Procedurally synthesised sound effects (numpy -> wav -> ogg via ffmpeg)."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np

from .out import RP, write_json

SR = 32000


def t_(dur):
    return np.arange(int(round(SR * dur))) / SR


def env(n, a=0.01, d=0.1, s=0.6, r=0.2, total=None):
    total = total or n / SR
    t = np.arange(n) / SR
    e = np.ones(n)
    e = np.where(t < a, t / max(a, 1e-6), e)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-6), e)
    e = np.where((t >= a + d), s, e)
    rel_start = total - r
    e = np.where(t >= rel_start, e * np.clip((total - t) / max(r, 1e-6), 0, 1), e)
    return e


def noise(n, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def lowpass(x, cutoff):
    """One-pole low-pass with (possibly varying) cutoff in Hz."""
    cut = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def osc(freq, dur, kind='sine', phase=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (int(round(SR * dur)),))
    ph = np.cumsum(f) / SR + phase
    if kind == 'sine':
        return np.sin(2 * np.pi * ph)
    if kind == 'saw':
        return 2 * (ph % 1.0) - 1
    if kind == 'square':
        return np.sign(np.sin(2 * np.pi * ph))
    return np.abs(4 * (ph % 1.0) - 2) - 1  # triangle


def reverb(x, mix=0.3, decay=0.45):
    out = x.copy()
    for delay_ms, g in ((29.7, decay), (37.1, decay * 0.9), (41.1, decay * 0.85), (43.7, decay * 0.8)):
        d = int(SR * delay_ms / 1000)
        y = np.zeros(len(x) + d * 12)
        y[:len(x)] = x
        for k in range(1, 12):
            y[d * k:d * k + len(x)] += x * (g ** k)
        out = out + y[:len(x)] * mix / 4
    return out


def pad(x, dur):
    n = int(SR * dur)
    return np.pad(x, (0, max(0, n - len(x))))[:n]


def norm(x, peak=0.85):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ------------------------------------------------------------------------------- sounds
def s_cast():
    d = 0.7
    t = t_(d)
    sweep = osc(400 + 1400 * t / d, d, 'sine') * 0.4 + osc(800 + 2400 * t / d, d, 'triangle') * 0.2
    shimmer = sum(osc(f, d) * 0.12 for f in (1760, 2217, 2637, 3520)) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t))
    air = bandpass(noise(len(t), 1), 2000, 7000) * 0.3
    x = (sweep + shimmer + air) * env(len(t), 0.05, 0.2, 0.5, 0.35, d)
    return norm(reverb(x, 0.35))


def s_flip():
    d = 0.35
    x = np.zeros(int(SR * d))
    for k, start in enumerate((0.0, 0.07, 0.15)):
        n = int(SR * 0.09)
        b = bandpass(noise(n, 10 + k), 1500, 6000) * env(n, 0.005, 0.03, 0.3, 0.05, 0.09)
        i = int(SR * start)
        x[i:i + n] += b
    return norm(x, 0.6)


def s_awaken():
    d = 3.2
    t = t_(d)
    chord = sum(osc(f * (1 + 0.003 * np.sin(2 * np.pi * 5 * t)), d, 'saw') * a for f, a in ((130.8, 0.3), (196, 0.25), (261.6, 0.2), (329.6, 0.18), (392, 0.12)))
    chord = lowpass(chord, 300 + 2500 * np.clip(t / 1.6, 0, 1))
    chimes = np.zeros_like(t)
    for k, (f, st) in enumerate(((1046.5, 0.6), (1318.5, 0.9), (1568, 1.2), (2093, 1.5))):
        i = int(SR * st)
        n = len(t) - i
        chimes[i:] += osc(f, n / SR) * np.exp(-np.arange(n) / SR * 2.2) * 0.25
    boom = osc(55 * np.exp(-t * 2), d) * np.exp(-t * 3) * 0.8
    x = chord * env(len(t), 1.2, 0.3, 0.8, 1.0, d) + chimes + boom
    return norm(reverb(x, 0.5, 0.55))


def s_levelup():
    d = 1.4
    x = np.zeros(int(SR * d))
    for k, f in enumerate((523.3, 659.3, 784, 1046.5, 1318.5)):
        st = int(SR * k * 0.09)
        n = len(x) - st
        tt = np.arange(n) / SR
        x[st:] += (osc(f, n / SR) + osc(f * 2, n / SR) * 0.3) * np.exp(-tt * 3.0) * 0.35
    return norm(reverb(x, 0.4))


def s_anti_slash():
    d = 0.75
    t = t_(d)
    whoosh = bandpass(noise(len(t), 3), 120, 300 + 2500 * np.exp(-t * 6)) * env(len(t), 0.02, 0.15, 0.4, 0.4, d) * 2.2
    low = osc(70 * np.exp(-t * 1.5) + 30, d, 'saw') * np.exp(-t * 5) * 0.8
    crunch = np.tanh(bandpass(noise(len(t), 4), 600, 4000) * 6) * np.exp(-t * 18) * 0.35
    return norm(np.tanh((whoosh + low + crunch) * 1.6))


def s_nullify():
    d = 0.8
    t = t_(d)
    rev = bandpass(noise(len(t), 5), 300, 4000)[::-1] * np.clip(t / d, 0, 1) ** 2 * 1.4
    glass = sum(osc(f, d) * np.exp(-np.clip(t - 0.55, 0, None) * 14) * (t > 0.55) * 0.2 for f in (2900, 3700, 4400, 5300))
    thud = osc(60, d) * np.exp(-np.clip(t - 0.55, 0, None) * 10) * (t > 0.55) * 0.9
    return norm(rev + glass + thud)


def s_blackform():
    d = 2.2
    t = t_(d)
    f = 48 + 10 * np.sin(2 * np.pi * 3 * t)
    growl = np.tanh(osc(f, d, 'saw') * 3 + osc(f * 1.5, d, 'saw') * 1.5) * env(len(t), 0.2, 0.4, 0.8, 0.8, d)
    growl = lowpass(growl, 600 + 300 * np.sin(2 * np.pi * 7 * t))
    hiss = bandpass(noise(len(t), 6), 1500, 6000) * env(len(t), 0.4, 0.5, 0.3, 0.8, d) * 0.4
    crack = np.zeros_like(t)
    rng = np.random.default_rng(6)
    for _ in range(18):
        i = rng.integers(0, len(t) - 2000)
        crack[i:i + 1600] += noise(1600, int(i)) * np.exp(-np.arange(1600) / 200) * 0.6
    return norm(reverb(growl + hiss + crack, 0.3))


def s_wind():
    d = 1.0
    t = t_(d)
    x = bandpass(noise(len(t), 7), 200, 800 + 2800 * np.sin(np.pi * t / d)) * np.sin(np.pi * t / d) ** 1.5 * 2.0
    return norm(x)


def s_empty():
    d = 0.5
    t = t_(d)
    x = osc(220 * np.exp(-t * 3), d, 'triangle') * np.exp(-t * 7) + osc(110, d) * np.exp(-t * 9) * 0.6
    return norm(x, 0.6)


def s_impact():
    d = 1.0
    t = t_(d)
    boom = osc(80 * np.exp(-t * 4) + 30, d) * np.exp(-t * 4)
    burst = lowpass(noise(len(t), 8), 1800 * np.exp(-t * 3) + 200) * np.exp(-t * 6) * 1.5
    sparkle = sum(osc(f, d) * np.exp(-t * 8) * 0.1 for f in (1500, 2300, 3100))
    return norm(np.tanh((boom + burst + sparkle) * 1.4))


def s_zap():
    d = 0.6
    t = t_(d)
    rng = np.random.default_rng(9)
    gate = (rng.random(len(t) // 80 + 1) > 0.45).repeat(80)[:len(t)]
    x = highpass(noise(len(t), 9), 1200) * gate * np.exp(-t * 4) * 1.5 + osc(120, d, 'square') * np.exp(-t * 10) * 0.3
    return norm(np.tanh(x * 2))


def s_roar():
    d = 2.0
    t = t_(d)
    f = 70 + 25 * np.sin(np.pi * t / d)
    x = osc(f, d, 'saw') + osc(f * 2.01, d, 'saw') * 0.5 + bandpass(noise(len(t), 11), 200, 1200) * 0.8
    x = lowpass(np.tanh(x * 2.5), 500 + 900 * np.sin(np.pi * t / d))
    return norm(reverb(x * env(len(t), 0.25, 0.3, 0.8, 0.6, d), 0.4))


def s_water():
    d = 1.1
    t = t_(d)
    x = bandpass(noise(len(t), 12), 150, 500 + 2500 * np.sin(np.pi * t / d) ** 2) * np.sin(np.pi * t / d) * 2
    bubbles = np.zeros_like(t)
    rng = np.random.default_rng(12)
    for _ in range(14):
        i = rng.integers(0, len(t) - 3000)
        f0 = rng.uniform(400, 900)
        tt = np.arange(3000) / SR
        bubbles[i:i + 3000] += np.sin(2 * np.pi * (f0 + 2000 * tt) * tt) * np.exp(-tt * 40) * 0.4
    return norm(x + bubbles)


def s_ice():
    d = 1.2
    t = t_(d)
    x = np.zeros_like(t)
    rng = np.random.default_rng(13)
    for k in range(9):
        st = int(SR * k * 0.05)
        f = rng.uniform(2500, 6000)
        n = len(t) - st
        tt = np.arange(n) / SR
        x[st:] += osc(f, n / SR) * np.exp(-tt * 9) * 0.25
    crack = highpass(noise(len(t), 14), 3000) * np.exp(-t * 20) * 0.8
    return norm(reverb(x + crack, 0.3))


def s_shine():
    d = 1.3
    t = t_(d)
    x = sum(osc(f, d) * a for f, a in ((880, 0.3), (1108.7, 0.25), (1318.5, 0.25), (1760, 0.2), (2637, 0.12)))
    x = x * env(len(t), 0.02, 0.2, 0.5, 0.9, d) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t))
    return norm(reverb(x, 0.45))


def s_cannon():
    d = 1.4
    t = t_(d)
    boom = osc(55 * np.exp(-t * 2.5) + 28, d) * np.exp(-t * 3.5) * 1.2
    crack = lowpass(noise(len(t), 21), 4000 * np.exp(-t * 12) + 300) * np.exp(-t * 9) * 1.6
    rumble = lowpass(noise(len(t), 22), 220) * np.exp(-t * 2.0) * 1.5
    return norm(reverb(np.tanh((boom + crack + rumble) * 1.8), 0.25))


def s_bell():
    d = 2.4
    t = t_(d)
    x = sum(osc(440 * r, d) * a * np.exp(-t * dec) for r, a, dec in ((1, 0.5, 1.4), (2.0, 0.3, 2.0), (2.76, 0.22, 2.6), (5.4, 0.12, 4.0), (0.5, 0.25, 1.0)))
    return norm(reverb(x, 0.35))


def s_eat():
    d = 1.6
    t = t_(d)
    crunch = np.zeros_like(t)
    rng = np.random.default_rng(31)
    for k in range(5):
        i = int(SR * (0.05 + k * 0.16))
        n = int(SR * 0.08)
        crunch[i:i + n] += bandpass(noise(n, 40 + k), 800, 5000) * np.exp(-np.arange(n) / SR * 40) * 0.9
    eerie = sum(osc(f * (1 + 0.01 * np.sin(2 * np.pi * 4 * t)), d) for f in (146.8, 207.7, 277.2)) * np.clip((t - 0.8) / 0.4, 0, 1) * np.exp(-np.clip(t - 1.2, 0, None) * 4) * 0.25
    return norm(reverb(crunch + eerie, 0.3))


def s_will():
    d = 1.3
    t = t_(d)
    beat = np.zeros_like(t)
    for st in (0.0, 0.22):
        i = int(SR * st)
        n = len(t) - i
        tt = np.arange(n) / SR
        beat[i:] += osc(50 * np.exp(-tt * 6) + 30, n / SR) * np.exp(-tt * 9)
    whoosh = bandpass(noise(len(t), 41), 150, 300 + 1500 * np.clip((t - 0.3) * 2, 0, 1)) * np.sin(np.pi * np.clip((t - 0.25) / 1.0, 0, 1)) * 1.6
    return norm(np.tanh((beat * 1.4 + whoosh) * 1.3))


def s_rock():
    d = 0.9
    t = t_(d)
    x = lowpass(noise(len(t), 51), 1800 * np.exp(-t * 5) + 150) * np.exp(-t * 5) * 1.5 + osc(70 * np.exp(-t * 3), d) * np.exp(-t * 6)
    grit = np.zeros_like(t)
    rng = np.random.default_rng(52)
    for _ in range(25):
        i = int(rng.integers(0, len(t) - 600))
        grit[i:i + 600] += highpass(noise(600, int(i)), 2000) * np.exp(-np.arange(600) / 90) * 0.35
    return norm(np.tanh((x + grit) * 1.5))


def s_gravity():
    d = 1.4
    t = t_(d)
    f = 60 + 40 * np.sin(np.pi * t / d)
    x = osc(f, d, 'saw') * 0.6 + osc(f * 1.01, d, 'saw') * 0.6
    x = lowpass(x, 300 + 600 * np.sin(np.pi * t / d)) * np.sin(np.pi * t / d)
    return norm(reverb(x, 0.3))


def s_coins():
    d = 0.9
    x = np.zeros(int(SR * d))
    rng = np.random.default_rng(61)
    for k in range(7):
        st = int(SR * rng.uniform(0, 0.4))
        n = len(x) - st
        tt = np.arange(n) / SR
        f = rng.uniform(2500, 4200)
        x[st:] += (osc(f, n / SR) + osc(f * 1.47, n / SR) * 0.5) * np.exp(-tt * 18) * 0.3
    return norm(x, 0.7)


def s_lev_roar():
    d = 2.6
    t = t_(d)
    f = 38 + 14 * np.sin(np.pi * t / d)
    x = osc(f, d, 'saw') + osc(f * 1.5, d, 'saw') * 0.6 + bandpass(noise(len(t), 71), 100, 900) * 0.9
    x = lowpass(np.tanh(x * 2.2), 380 + 500 * np.sin(np.pi * t / d))
    bubbles = np.zeros_like(t)
    rng = np.random.default_rng(72)
    for _ in range(20):
        i = int(rng.integers(0, len(t) - 2500))
        tt = np.arange(2500) / SR
        f0 = rng.uniform(250, 600)
        bubbles[i:i + 2500] += np.sin(2 * np.pi * (f0 + 1500 * tt) * tt) * np.exp(-tt * 35) * 0.35
    return norm(reverb(x * env(len(t), 0.3, 0.4, 0.8, 0.8, d) + bubbles, 0.45))


def s_pistol():
    d = 0.9
    t = t_(d)
    crack = highpass(noise(len(t), 81), 900) * np.exp(-t * 40) * 1.6
    body = lowpass(noise(len(t), 82), 1200 * np.exp(-t * 8) + 150) * np.exp(-t * 7) * 1.2 + osc(90 * np.exp(-t * 5), d) * np.exp(-t * 12)
    return norm(reverb(np.tanh((crack + body) * 2), 0.3))


def s_howl():
    d = 2.2
    t = t_(d)
    f = 380 + 160 * np.sin(np.pi * np.clip(t / 1.6, 0, 1)) - 120 * np.clip((t - 1.4) / 0.8, 0, 1)
    v = 1 + 0.02 * np.sin(2 * np.pi * 6 * t)
    x = osc(f * v, d) * 0.7 + osc(f * 2 * v, d) * 0.2 + bandpass(noise(len(t), 83), 600, 2400) * 0.12
    return norm(reverb(x * env(len(t), 0.25, 0.3, 0.8, 0.6, d), 0.5))


def s_portal():
    d = 1.3
    t = t_(d)
    sweep = osc(200 + 900 * (t / d) ** 2, d, 'triangle') * 0.4
    swirl = bandpass(noise(len(t), 84), 300 + 2000 * (t / d), 800 + 4000 * (t / d)) * 0.8
    x = (sweep + swirl) * np.sin(np.pi * t / d) * (0.7 + 0.3 * np.sin(2 * np.pi * 14 * t))
    return norm(reverb(x, 0.45))


def s_mirror():
    d = 1.2
    t = t_(d)
    x = sum(osc(f, d) * np.exp(-t * dec) * a for f, a, dec in ((2093, 0.3, 4), (2637, 0.25, 5), (3136, 0.2, 6), (4186, 0.15, 7)))
    x += highpass(noise(len(t), 85), 5000) * np.exp(-t * 30) * 0.4
    return norm(reverb(x, 0.4))


def s_fanfare():
    d = 1.8
    x = np.zeros(int(round(SR * d)))
    for k, (f, st, ln) in enumerate(((392, 0.0, 0.18), (523.3, 0.18, 0.18), (659.3, 0.36, 0.18), (784, 0.54, 1.1))):
        i = int(SR * st)
        n = int(SR * ln)
        tt = np.arange(n) / SR
        tone = (osc(f, n / SR, 'saw')[:n] * 0.4 + osc(f * 2, n / SR)[:n] * 0.2) * np.minimum(1, tt * 40) * np.exp(-tt * (1.5 if k == 3 else 6))
        x[i:i + n] += lowpass(tone, 2500)
    return norm(reverb(x, 0.35))


def s_slam():
    d = 1.2
    t = t_(d)
    thud = osc(45 * np.exp(-t * 3) + 25, d) * np.exp(-t * 4) * 1.4
    rubble = lowpass(noise(len(t), 86), 1500 * np.exp(-t * 4) + 120) * np.exp(-t * 3) * 1.2
    return norm(np.tanh((thud + rubble) * 1.6))


SOUNDS = {
    'bc.pistol': (s_pistol, 'player', 1.0),
    'bc.howl': (s_howl, 'player', 1.0),
    'bc.portal': (s_portal, 'neutral', 1.0),
    'bc.mirror': (s_mirror, 'neutral', 1.0),
    'bc.fanfare': (s_fanfare, 'player', 0.9),
    'bc.golem.slam': (s_slam, 'hostile', 1.0),
    'bc.cannon': (s_cannon, 'neutral', 1.0),
    'bc.ship.bell': (s_bell, 'neutral', 0.9),
    'bc.fruit.eat': (s_eat, 'player', 1.0),
    'bc.will.pulse': (s_will, 'player', 1.0),
    'bc.stone.crack': (s_rock, 'neutral', 1.0),
    'bc.gravity.hum': (s_gravity, 'neutral', 1.0),
    'bc.coins': (s_coins, 'player', 0.9),
    'bc.leviathan.roar': (s_lev_roar, 'hostile', 1.0),
    'bc.cast': (s_cast, 'player', 1.0),
    'bc.grimoire.flip': (s_flip, 'player', 0.8),
    'bc.grimoire.awaken': (s_awaken, 'block', 1.0),
    'bc.levelup': (s_levelup, 'player', 1.0),
    'bc.anti.slash': (s_anti_slash, 'player', 1.0),
    'bc.anti.nullify': (s_nullify, 'player', 1.0),
    'bc.blackform': (s_blackform, 'player', 1.0),
    'bc.wind.gust': (s_wind, 'player', 1.0),
    'bc.mana.empty': (s_empty, 'player', 0.8),
    'bc.spell.impact': (s_impact, 'neutral', 1.0),
    'bc.lightning.zap': (s_zap, 'neutral', 1.0),
    'bc.devil.roar': (s_roar, 'hostile', 1.0),
    'bc.water.surge': (s_water, 'neutral', 1.0),
    'bc.ice.form': (s_ice, 'neutral', 1.0),
    'bc.light.shine': (s_shine, 'neutral', 1.0),
}


def _write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build():
    defs = {}
    os.makedirs(os.path.join(RP, 'sounds', 'bc'), exist_ok=True)
    have_ffmpeg = shutil.which('ffmpeg') is not None
    with tempfile.TemporaryDirectory() as tmp:
        for key, (fn, cat, vol) in SOUNDS.items():
            name = key.replace('bc.', '').replace('.', '_')
            x = fn()
            wav = os.path.join(tmp, name + '.wav')
            _write_wav(wav, x)
            dst = os.path.join(RP, 'sounds', 'bc', name + '.ogg')
            if have_ffmpeg:
                subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libvorbis', '-q:a', '4', dst], check=True)
            elif not os.path.exists(dst):
                raise RuntimeError('ffmpeg is required to encode sounds')
            defs[key] = {'category': cat, 'min_distance': 1.0, 'max_distance': 32.0,
                         'sounds': [{'name': f'sounds/bc/{name}', 'volume': vol, 'load_on_low_memory': True}]}
    write_json(RP, 'sounds/sound_definitions.json', {'format_version': '1.20.20', 'sound_definitions': defs})
