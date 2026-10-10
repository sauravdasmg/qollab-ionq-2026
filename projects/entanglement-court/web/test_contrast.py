"""WCAG contrast checks for web/main.css.

Parses the single light theme's hex colour pairs (resolving var() references
from :root) for body, panel, table header, button and footer and asserts
WCAG contrast >= 7:1 for body-text pairs and >= 4.5:1 otherwise. Also asserts
the stylesheet has no prefers-color-scheme: dark rule and uses an explicit
light color-scheme on the page root.
"""
import re
from pathlib import Path

CSS = Path(__file__).with_name("main.css").read_text(encoding="utf-8")

# --- helpers ---------------------------------------------------------------


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_rgb):
    hex_rgb = hex_rgb.strip().lstrip("#")
    assert re.fullmatch(r"[0-9a-fA-F]{6}", hex_rgb), f"not a hex colour: {hex_rgb!r}"
    r = int(hex_rgb[0:2], 16)
    g = int(hex_rgb[2:4], 16)
    b = int(hex_rgb[4:6], 16)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(hex_a, hex_b):
    la, lb = luminance(hex_a), luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# --- minimal CSS parsing ----------------------------------------------------

def split_rules(css_text):
    css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    rules = []
    i, n = 0, len(css_text)
    while i < n:
        j = css_text.find("{", i)
        if j == -1:
            break
        selector = css_text[i:j].strip()
        depth = 1
        k = j + 1
        while depth > 0 and k < n:
            if css_text[k] == "{":
                depth += 1
            elif css_text[k] == "}":
                depth -= 1
            k += 1
        rules.append((selector, css_text[j + 1 : k - 1]))
        i = k
    return rules


def parse_decls(body):
    props = {}
    for name, value in re.findall(r"([a-zA-Z-]+)\s*:\s*([^;]+);?", body):
        props[name.strip().lower()] = value.strip()
    return props


def normalize(selector):
    return " ".join(selector.split())


def matches(selector_list, fragment):
    """True when the selector list contains the fragment as an exact entry."""
    target = normalize(fragment)
    for entry in re.split(r"\s*,\s*", selector_list):
        if entry.strip().startswith("@"):
            continue
        if normalize(entry) == target:
            return True
    return False


def prop_text(rules, selector_fragment):
    """Merge, in order, every top-level rule whose selector list exactly contains the fragment."""
    merged = {}
    for selector, body in rules:
        if selector.startswith("@") or not matches(selector, selector_fragment):
            continue
        merged.update(parse_decls(body))
    return merged


def var_table(rules):
    vars_map = {}
    for selector, body in rules:
        if normalize(selector) not in (":root", "html"):
            continue
        for name, value in parse_decls(body).items():
            if name.startswith("--"):
                vars_map[name] = value
    return vars_map


def resolve(value, vars_map, depth=0):
    m = re.match(r"var\((--[a-zA-Z0-9-]+)(?:,\s*([^)]*))?\)", value or "")
    if not m or depth > 10:
        return value
    if m.group(1) in vars_map:
        return resolve(vars_map[m.group(1)], vars_map, depth + 1)
    return resolve(m.group(2) or "", vars_map, depth + 1) if m.group(2) else value


def colour(props, name, vars_map):
    raw = props.get(name)
    if raw is None:
        return None
    val = resolve(raw, vars_map)
    if val.startswith("#"):
        return val
    return None


# --- assertions --------------------------------------------------------------

def test_no_dark_scheme_rule():
    assert "prefers-color-scheme: dark" not in CSS.lower()


def test_explicit_light_scheme():
    rules = split_rules(CSS)
    vs = var_table(rules)
    root = prop_text(rules, ":root")
    body = prop_text(rules, "body")
    assert root.get("color-scheme") == "light"
    assert body.get("color-scheme") == "light"
    assert colour(root, "background", vs) == "#FBF6EA"
    assert colour(root, "color", vs) == "#1F1A14"
    assert colour(body, "background", vs) == "#FBF6EA"
    assert colour(body, "color", vs) == "#1F1A14"


def test_pairs():
    rules = split_rules(CSS)
    vs = var_table(rules)

    def bg_of(sel, fallback=None):
        return colour(prop_text(rules, sel), "background", vs) or fallback

    pairs = [
        # label, fg selector, bg selector, threshold
        ("body text on page", "body", "body", 7.0),
        ("panel text on white", "body", ".sidebar-panel", 7.0),
        ("table header", ".histogram-table th", ".histogram-table th", 7.0),
        ("button", ".verdict-btn", ".verdict-btn", 7.0),
        ("button hover", ".verdict-btn", ".verdict-btn:hover", 7.0),
        ("selected verdict (large)", ".verdict-btn.selected", ".verdict-btn.selected", 4.5),
        ("footer", "footer", "footer", 7.0),
        ("footer attribution", "footer .attribution", "footer", 7.0),
        ("heading on panel", ".docket-header h2", ".docket-header", 7.0),
        ("secondary text", ".docket-header .case-id", ".docket-header", 7.0),
        ("stamp heading (copper)", ".evidence-stamp h3", ".evidence-stamp", 4.5),
    ]

    failures = []
    for label, fg_sel, bg_sel, threshold in pairs:
        fg = colour(prop_text(rules, fg_sel), "color", vs)
        bg = bg_of(bg_sel, "#FFFFFF")
        assert fg is not None, f"{label}: no fg colour for {fg_sel}"
        assert bg is not None, f"{label}: no bg colour for {bg_sel}"
        cr = contrast(fg, bg)
        if cr < threshold:
            failures.append(f"{label}: {fg} on {bg} = {cr:.2f} < {threshold}")

    assert not failures, "\n".join(failures)


def test_footer_attribution_readable():
    rules = split_rules(CSS)
    vs = var_table(rules)
    attr = prop_text(rules, "footer .attribution")
    assert "font-style" not in attr or attr.get("font-style") == "normal"
    assert "opacity" not in attr
    assert colour(attr, "color", vs) == "#1F1A14"
    footer = prop_text(rules, "footer")
    assert colour(footer, "background", vs) == "#EFE6D2"


def test_hidden_attribute_wins_for_loading_overlay():
    css = CSS.lower()
    assert re.search(r"\[hidden\]\s*{[^}]*display\s*:\s*none", css)