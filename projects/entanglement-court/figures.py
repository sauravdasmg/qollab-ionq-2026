"""Courtroom exhibits: redundant text, symbols and color; no implicit trust."""
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta

ASSUMPTIONS = 'Conditional on trusted measurement rotations/readout; systematic error unbounded unless supplied.'


def parity_interval(successes, shots, alpha=.05):
    if shots <= 0 or not 0 <= successes <= shots:
        raise ValueError('invalid parity counts')
    lo = 0. if successes == 0 else float(beta.ppf(alpha / 2, successes, shots - successes + 1))
    hi = 1. if successes == shots else float(beta.ppf(1 - alpha / 2, successes + 1, shots - successes))
    return 2 * lo - 1, 2 * hi - 1


def present(marginals, analysis, source, shots, trusted=False):
    print('ENTANGLEMENT COURT | ' + source + ' | ' + str(shots) + ' shots per block', flush=True)
    print(ASSUMPTIONS + ' Trust flag: ' + str(trusted), flush=True)
    print('Mathematical reference: both Z distributions are exactly uniform (probability 1/16); exact TV distance 0.', flush=True)
    if 'target_Z' not in marginals:
        print('Witness-only reference mode: Z histograms were not measured; the reference above is mathematical, not saved cloud Z evidence.', flush=True)
    for name, hist in marginals.items():
        print('Exhibit ' + name + ' | outcome: count | ' + json.dumps(hist, sort_keys=True), flush=True)
    print('Complete primitive analysis: ' + json.dumps(analysis, sort_keys=True), flush=True)
    print('Intervals: two-sided 95% parity intervals; simultaneous bound uses the stated per-round union allocation. Units: dimensionless.', flush=True)
    print('Finite-shot estimates can cross theoretical witness bounds; use intervals. Abstention does not establish separability.', flush=True)
    print('This exhibit shows its labeled source only; campaign availability and legacy deviations are reported by the receipt loader.', flush=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))
    fig.patch.set_facecolor('#f4ecd9')
    for ax in axes:
        ax.set_facecolor('#f4ecd9')
        ax.spines[['top', 'right']].set_visible(False)
    x = np.arange(16)
    for name, color, shift in [('target_Z', '#28345a', -.18), ('impostor_Z', '#ad6334', .18)]:
        if name in marginals:
            hist = marginals[name]
            axes[0].bar(x + shift, [hist.get(format(i, '04b'), 0) / sum(hist.values()) for i in x], .36, label=name, color=color)
    axes[0].axhline(1 / 16, color='black', linestyle='--', label='exact reference 1/16')
    axes[0].set(xlabel='Z outcome (integer encoding)', ylabel='Probability', title='[EXHIBIT Z] Matched reference')
    axes[0].legend(fontsize=7)
    index = 0
    for name, rows in analysis['blocks'].items():
        for row in rows:
            lo, hi = parity_interval(row['successes'], row['shots'])
            value = row['estimate']
            axes[1].errorbar(index, value, yerr=[[value-lo], [hi-value]], fmt='o' if 'target' in name else 's', color='#28345a' if 'target' in name else '#ad6334')
            axes[1].text(index, -.95, name + '\nK' + str(row['generator']), rotation=90, fontsize=6)
            print(name + ' K' + str(row['generator']) + ': parity ' + format(value, '.4f') + ', 95% interval [' + format(lo, '.4f') + ', ' + format(hi, '.4f') + '] (dimensionless)', flush=True)
            index += 1
    axes[1].set(title='[EXHIBITS A/B] Two colors', ylabel='Signed parity with 95% interval', ylim=(-1.05, 1.05))
    bound = analysis['simultaneous_witness']
    if 'F_lower' in bound:
        axes[2].bar([0], [bound['F_lower']], color='#28345a', label='target simultaneous lower bound')
        axes[2].axhline(.5, linestyle='--', color='#ad6334', label='GME threshold 0.5')
        axes[2].text(.02, .03, bound['receipt'] + '\n' + ASSUMPTIONS, transform=axes[2].transAxes, wrap=True, fontsize=7)
    axes[2].set(title='[EVIDENCE STAMP] Per-round bound', ylabel='Fidelity lower bound (dimensionless)', xticks=[])
    axes[2].legend(fontsize=7)
    fig.suptitle(source + ' | ' + str(shots) + ' shots/block | trust=' + str(trusted))
    fig.text(.02, .01, ASSUMPTIONS, fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, .92))
    plt.show()
    plt.close(fig)
    return fig
