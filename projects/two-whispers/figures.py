"""Signal-desk figures: cream background, navy ink, teal signals.

Colour is redundant with text and shape; every cell and ribbon also carries a
plain-symbol or numeric label. Figures are plain text where they are text.
"""

import numpy as np
from matplotlib import colors as _colors
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

CREAM = '#FBF3E2'
NAVY = '#1F2A44'
TEAL = '#0FA3A3'
TEAL_DARK = '#0A7C7C'
FAMILIES = ('collective', 'textbook', 'deferred-sequential')
_CMAP = _colors.LinearSegmentedColormap.from_list('desk', [CREAM, TEAL])


def _style(axis):
    axis.set_facecolor(CREAM)
    for spine in axis.spines.values():
        spine.set_color(NAVY)
    axis.tick_params(colors=NAVY)


def banner():
    """Three square label cards; three receiver routes with paired ribbons."""
    fig, axis = plt.subplots(figsize=(8.4, 1.9))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 2)
    axis.axis('off')
    fig.patch.set_facecolor(CREAM)
    axis.set_facecolor(CREAM)
    axis.set_title('TWO WHISPERS MAKE A WORD - signal desk', color=NAVY, fontweight='bold')
    for x, text in ((0.3, 'LABEL 0'), (2.3, 'LABEL 1'), (4.3, 'LABEL 2')):
        axis.add_patch(Rectangle((x, 0.4), 1.3, 1.3, facecolor=CREAM,
                                 edgecolor=NAVY, lw=2))
        axis.text(x + 0.65, 1.05, text, ha='center', va='center', color=NAVY,
                  fontweight='bold')
    for x, text in ((6.2, 'COLLECTIVE'), (7.6, 'TEXTBOOK'), (9.0, 'SEQUENTIAL')):
        axis.add_patch(Rectangle((x, 0.4), 0.85, 1.3, facecolor=TEAL,
                                 edgecolor=NAVY, lw=2))
        axis.text(x + 0.42, 1.0, text, ha='center', va='center', color='white',
                  fontweight='bold', fontsize=8)
        axis.add_patch(Rectangle((x + 0.12, 1.55), 0.28, 0.3, facecolor=TEAL_DARK))
        axis.add_patch(Rectangle((x + 0.44, 1.55), 0.28, 0.3, facecolor=TEAL_DARK))
    return fig


def confusion_figure(analysis, manifest):
    """Complete 3x3 confusion heatmaps, one per receiver family."""
    families = list(FAMILIES)
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9))
    fig.patch.set_facecolor(CREAM)
    fig.suptitle('Confusion matrices: decoded label vs sent label (complete, '
                 'unused terminal outcomes counted)', color=NAVY, fontweight='bold')
    for axis, family in zip(axes, families):
        matrix = np.asarray(analysis[family]['confusion_matrix'], dtype=float)
        axis.imshow(matrix, vmin=0, vmax=1, cmap=_CMAP, aspect='equal')
        for i in range(3):
            for j in range(3):
                axis.text(j, i, f'{matrix[i, j]:.3f}' if np.isfinite(matrix[i, j]) else 'n/a', ha='center', va='center',
                          color=TEAL_DARK if i == j else NAVY,
                          fontweight='bold' if i == j else 'normal', fontsize=9)
        axis.set_xticks(range(3))
        axis.set_yticks(range(3))
        axis.set_xticklabels(['decoded 0', 'decoded 1', 'decoded 2'])
        axis.set_yticklabels(['sent 0', 'sent 1', 'sent 2'])
        success = analysis[family]['success_probability']
        axis.set_title(f'{family}\nsuccess {success:.4f}' if success is not None
                       else f'{family}\nno counts (zero shots)',
                       color=NAVY, fontweight='bold')
        _style(axis)
    fig.tight_layout()
    return fig


def error_figure(analysis, manifest):
    """Word-error bars with Wilson intervals against the one-way ceiling."""
    families = list(FAMILIES)
    errors = []
    lows = []
    highs = []
    for family in families:
        value = analysis[family]['word_error']
        interval = analysis[family]['word_error_interval_95']
        errors.append(value if value is not None else np.nan)
        lows.append(interval[0] if interval and value is not None else np.nan)
        highs.append(interval[1] if interval and value is not None else np.nan)
    errors = np.asarray(errors, dtype=float)
    lows = np.asarray(lows, dtype=float)
    highs = np.asarray(highs, dtype=float)
    x = np.arange(len(families))
    fig, axis = plt.subplots(figsize=(9, 4.2))
    fig.patch.set_facecolor(CREAM)
    with np.errstate(invalid='ignore'):
        axis.bar(x, errors, yerr=[errors - lows, highs - errors], width=0.5,
                 color=TEAL, edgecolor=NAVY, capsize=6,
                 error_kw={'elinewidth': 1.5})
    reference = manifest.get('reference_probabilities', {})
    ceilings = {reference.get(family, None) for family in families}
    for ceiling in sorted(c for c in ceilings if c is not None):
        axis.axhline(1 - ceiling, linestyle='--', color=NAVY)
    axis.set_xticks(x)
    axis.set_xticklabels(families, rotation=15)
    axis.set_ylabel('word error (mean over 3 labels)', color=NAVY)
    axis.set_title('Word-error estimates with 95% intervals vs ideal ceilings '
                   '(dashed)', color=NAVY, fontweight='bold')
    _style(axis)
    fig.tight_layout()
    return fig


def render(analysis, manifest, *, source='live built-in ideal', shots=None,
           backend=None, noise_model=None):
    """Return the signal-desk figure set for the given analysis and manifest."""
    figs = [banner(), confusion_figure(analysis, manifest),
            error_figure(analysis, manifest)]
    totals = analysis[FAMILIES[0]]['shots_per_label']
    caption = (f'Source: {source} | backend: {backend or "unspecified"} | '
               f'shots/block: {shots if shots is not None else totals} | '
               f'noise: {noise_model or "ideal"}\n'
               'Units: probability; 95% Wilson cells / Bonferroni mean intervals; '
               + manifest['source_assumptions'])
    for fig in figs:
        fig.subplots_adjust(bottom=0.27)
        fig.text(0.02, 0.02, caption, fontsize=7, color=NAVY)
    return figs
