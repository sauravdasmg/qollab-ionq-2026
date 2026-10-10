"""Samples-only decoder. No counts, fit metadata, sidecar or truth accepted."""
import io
import wave
import numpy as np
from scipy.optimize import minimize_scalar


def decode(data):
    with wave.open(io.BytesIO(data), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2 or w.getframerate() != 48000:
            raise ValueError("protocol requires mono 48 kHz 16-bit PCM")
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)/32767
    if len(x) != 96000:
        raise ValueError("protocol requires 2 seconds")
    x = x[4800:-4800]  # Central segment excludes both fades.
    t = np.arange(len(x))/48000
    size = 1 << (len(x)-1).bit_length()
    spectrum = abs(np.fft.rfft(x, n=size))
    freq = np.fft.rfftfreq(size, 1/48000)
    valid = (freq >= 110) & (freq <= 990)
    peak = float(freq[np.flatnonzero(valid)[np.argmax(spectrum[valid])]])
    def solve(hz):
        a = np.column_stack((np.cos(2*np.pi*hz*t), np.sin(2*np.pi*hz*t), np.ones(len(t))))
        b = np.linalg.lstsq(a, x, rcond=None)[0]
        return float(np.mean((x-a@b)**2)), b
    r = minimize_scalar(lambda hz: solve(hz)[0], bounds=(max(110, peak-0.8), min(990, peak+0.8)),
                        method="bounded", options={"xatol": 1e-7})
    loss, b = solve(r.x)
    return {"frequency": float(r.x/220), "contrast": float(2*np.hypot(b[0], b[1])), "mse": loss}
