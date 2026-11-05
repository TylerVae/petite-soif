"""Sons générés par synthèse (aucun fichier externe requis).

Les .wav sont créés dans /sons au premier lancement. Pour utiliser tes propres sons,
remplace simplement le fichier du même nom. Pour régénérer un son, supprime son fichier.
"""
import math
import random
import sys
import wave
from array import array

SR = 44100
NAMES = ["soif_1", "soif_2", "soif_3", "glouglou", "valide", "poof"]


def _buf(seconds):
    return [0.0] * int(SR * seconds)


def _tone(buf, start, dur, f0, f1=None, vol=0.4, attack=0.01, release=None,
          vibrato=(0.0, 0.0), partials=((1, 1.0), (2, 0.25), (3, 0.08)), decay=0.0, expo=True):
    f1 = f0 if f1 is None else f1
    n = int(dur * SR)
    s0 = int(start * SR)
    release = dur * 0.4 if release is None else release
    phases = [0.0] * len(partials)
    for i in range(n):
        if s0 + i >= len(buf):
            break
        t = i / SR
        k = t / dur
        f = f0 * (f1 / f0) ** k if expo else f0 + (f1 - f0) * k
        if vibrato[0]:
            f *= 1 + vibrato[1] * math.sin(2 * math.pi * vibrato[0] * t)
        env = min(1.0, t / attack) if attack > 0 else 1.0
        if t > dur - release:
            env *= max(0.0, (dur - t) / release)
        if decay:
            env *= math.exp(-t * decay)
        v = 0.0
        for j, (mult, amp) in enumerate(partials):
            phases[j] += 2 * math.pi * f * mult / SR
            v += amp * math.sin(phases[j])
        buf[s0 + i] += v * env * vol


def _noise(buf, start, dur, vol=0.4, cutoff=0.1, decay=10.0):
    s0 = int(start * SR)
    y = 0.0
    for i in range(int(dur * SR)):
        if s0 + i >= len(buf):
            break
        t = i / SR
        y += cutoff * (random.uniform(-1, 1) - y)
        env = min(1.0, t / 0.004) * math.exp(-t * decay)
        buf[s0 + i] += y * env * vol * 3


def _save(path, buf, peak):
    m = max(1e-9, max(abs(x) for x in buf))
    g = peak / m
    data = array("h", (int(max(-1.0, min(1.0, x * g)) * 32767) for x in buf))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


BELL = ((1, 1.0), (2.76, 0.22), (5.4, 0.06))


def _make(name):
    random.seed(name)
    if name == "soif_1":  # petit "ding-dong" doux
        b = _buf(0.9)
        _tone(b, 0.00, 0.30, 784, vol=0.5, partials=BELL, decay=5)
        _tone(b, 0.20, 0.65, 659, 620, vol=0.5, partials=BELL, decay=4)
        return b, 0.50
    if name == "soif_2":  # trois notes plaintives
        b = _buf(1.2)
        _tone(b, 0.00, 0.18, 880, vol=0.45, partials=BELL, decay=4)
        _tone(b, 0.17, 0.18, 740, vol=0.45, partials=BELL, decay=4)
        _tone(b, 0.34, 0.80, 587, 494, vol=0.5, vibrato=(5.5, 0.012), release=0.35)
        return b, 0.68
    if name == "soif_3":  # gémissement qui monte puis supplie
        b = _buf(1.7)
        _tone(b, 0.00, 0.45, 523, 880, vol=0.45, vibrato=(6.5, 0.02), release=0.08)
        _tone(b, 0.48, 0.13, 988, vol=0.45, partials=BELL, decay=3)
        _tone(b, 0.62, 0.13, 1175, vol=0.45, partials=BELL, decay=3)
        _tone(b, 0.76, 0.85, 988, 740, vol=0.5, vibrato=(5.0, 0.018), release=0.4)
        return b, 0.88
    if name == "glouglou":  # bulles
        b = _buf(0.95)
        t = 0.0
        while t < 0.78:
            f0 = random.uniform(230, 360)
            _tone(b, t, random.uniform(0.06, 0.09), f0, f0 * random.uniform(2.2, 2.9),
                  vol=random.uniform(0.35, 0.5), attack=0.004, release=0.035, partials=((1, 1.0),))
            t += random.uniform(0.08, 0.14)
        _noise(b, 0.0, 0.9, vol=0.03, cutoff=0.05, decay=2)
        return b, 0.70
    if name == "valide":  # arpège clochette
        b = _buf(1.0)
        for i, f in enumerate((1047, 1319, 1568, 2093)):
            _tone(b, i * 0.07, 0.7, f, vol=0.3, partials=BELL, decay=5, release=0.2)
        return b, 0.70
    if name == "poof":  # petit nuage de fumée
        b = _buf(0.4)
        _noise(b, 0.0, 0.38, vol=0.5, cutoff=0.18, decay=11)
        _tone(b, 0.0, 0.16, 190, 85, vol=0.35, partials=((1, 1.0),), attack=0.004, release=0.08)
        return b, 0.45
    raise KeyError(name)


def ensure_sounds(folder):
    folder.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        path = folder / f"{name}.wav"
        if not path.exists():
            buf, peak = _make(name)
            _save(path, buf, peak)


class SoundPlayer:
    """Lecture via winsound (intégré à Windows, aucune dépendance externe).

    Le volume est appliqué en pré-calculant une copie atténuée de chaque .wav dans
    sons/.cache/. Une seule piste joue à la fois (un nouveau son remplace le précédent).
    """

    def __init__(self, folder, volume=0.6):
        self.folder = folder
        self.cache = folder / ".cache"
        ensure_sounds(folder)
        self.volume = float(volume)
        self._paths = {}
        self._current = None
        self._build_cache()

    def _build_cache(self):
        self.cache.mkdir(parents=True, exist_ok=True)
        vol = max(0.0, min(1.0, self.volume))
        for name in NAMES:
            src = self.folder / f"{name}.wav"
            dst = self.cache / f"{name}.wav"
            try:
                with wave.open(str(src), "rb") as r:
                    params = r.getparams()
                    frames = r.readframes(params.nframes)
                if params.sampwidth != 2:  # format non 16 bits : lu tel quel, sans volume
                    self._paths[name] = src
                    continue
                data = array("h")
                data.frombytes(frames)
                if sys.byteorder == "big":
                    data.byteswap()
                scaled = array("h", (int(x * vol) for x in data))
                if sys.byteorder == "big":
                    scaled.byteswap()
                with wave.open(str(dst), "wb") as w:
                    w.setparams(params)
                    w.writeframes(scaled.tobytes())
                self._paths[name] = dst
            except Exception:
                self._paths[name] = src

    def set_volume(self, volume):
        self.volume = float(volume)
        self._build_cache()

    def play(self, name):
        if sys.platform != "win32" or self.volume <= 0:
            return
        import winsound

        path = self._paths.get(name)
        if path is None:
            return
        self._current = name
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)

    def stop(self, name):
        if sys.platform == "win32" and self._current == name:
            import winsound

            winsound.PlaySound(None, 0)
            self._current = None
