"""Mono PCM fallback; no normalization or compression."""
import io
import wave
import numpy as np

RATE = 48000
DURATION = 2.0
FADE = 0.05
CARRIER = 220.0


def samples(estimate):
    f, c = float(estimate["frequency"]), float(estimate["contrast"])
    if not (0.5 <= f <= 4.5 and 0 <= c <= 1):
        raise ValueError("invalid measured estimate")
    t = np.arange(int(RATE*DURATION))/RATE
    envelope = np.ones(len(t))
    size = int(RATE*FADE)
    envelope[:size] = np.linspace(0, 1, size)
    envelope[-size:] = np.linspace(1, 0, size)
    return 0.5*c*np.sin(2*np.pi*CARRIER*f*t)*envelope


def wav_bytes(estimate):
    pcm = np.round(samples(estimate)*32767).astype("<i2")
    stream = io.BytesIO()
    with wave.open(stream, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    return stream.getvalue()
