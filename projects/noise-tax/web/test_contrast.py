"""WCAG contrast checks for the Noise Tax light theme; no dark-scheme rules allowed."""
import re
from pathlib import Path

CSS = Path(__file__).with_name('main.css').read_text(encoding='utf-8')
HTML = Path(__file__).with_name('index.html').read_text(encoding='utf-8')


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


BODY_PAIRS = [
    ('#0F172A', '#F7F9FC'), ('#0F172A', '#FFFFFF'), ('#334155', '#FFFFFF'),
    ('#334155', '#F7F9FC'), ('#0F172A', '#E2E8F0'),
]
OTHER_PAIRS = [
    ('#0B5CAD', '#FFFFFF'), ('#0B5CAD', '#F7F9FC'), ('#FFFFFF', '#0B5CAD'),
    ('#1F6B3A', '#E8F5EC'), ('#9B1C1C', '#FDECEC'), ('#0F172A', '#FDECEC'),
    ('#C2410C', '#FFFFFF'),
]


def test_body_text_contrast_at_least_7():
    for fg, bg in BODY_PAIRS:
        assert ratio(fg, bg) >= 7, (fg, bg, ratio(fg, bg))


def test_other_pairs_contrast_at_least_4_5():
    for fg, bg in OTHER_PAIRS:
        assert ratio(fg, bg) >= 4.5, (fg, bg, ratio(fg, bg))


def test_declared_theme_tokens():
    for token in ('color-scheme: light', '#F7F9FC', '#CBD5E1', '#0F172A', '#334155', '#0B5CAD',
                  '#1F6B3A', '#E8F5EC', '#9B1C1C', '#FDECEC', '#E2E8F0',
                  'outline: 3px solid #C2410C'):
        assert token in CSS, token
    assert re.search(r'body\s*\{[^}]*font-size:\s*16px', CSS)


def test_root_container_light_theme():
    assert 'class="nt-root"' in HTML
    assert re.search(r'\.nt-root\s*\{[^}]*color-scheme:\s*light[^}]*background:\s*#F7F9FC', CSS)
    assert not re.search(r'<html[\s>]|<head[\s>]', HTML)  # '<header' is allowed


def test_no_dark_scheme_rules():
    assert 'prefers-color-scheme' not in CSS
    assert 'color-scheme: dark' not in CSS
    assert 'data-theme' not in CSS


def test_reduced_motion_and_footer_line():
    assert 'prefers-reduced-motion' in CSS
    assert 'This effort is supported by Qollab &amp; IonQ.' in HTML or \
        'This effort is supported by Qollab & IonQ.' in HTML
    assert '<script' not in HTML
    assert 'aria-live' in HTML
