from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
CSS = (ROOT / "main.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def luminance(hex_color):
    values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))


def ratio(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def test_required_readability_theme():
    assert "color-scheme: light" in CSS
    assert "prefers-color-scheme" not in CSS
    assert "<html" not in HTML.lower() and "<head " not in HTML.lower()
    assert "#FAFAF7" in CSS and "#FFFFFF" in CSS and "#D4D4CF" in CSS
    assert ratio("#111111", "#FAFAF7") >= 7
    assert ratio("#3F3F3B", "#FAFAF7") >= 7
    assert ratio("#111111", "#ECEBE6") >= 7
    assert ratio("#FFFFFF", "#4B2E83") >= 4.5
    assert ratio("#111111", "#FFFFFF") >= 7
