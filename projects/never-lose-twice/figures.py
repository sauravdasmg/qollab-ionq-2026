"""figures.py: printable tables and the slate/amber/sky-blue two-door trial board for Never Lose Twice.

Every number is labelled with its source, shot count, intervals, units and assumptions; colour is never
the only channel (each outcome cell also carries a code and a hatch pattern). This module is presentation-only:
it never submits jobs and never reads the network.
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from receipt import mean_pass_interval

PALETTE = {
    "slate": "#39424E",
    "amber": "#E8A33D",
    "sky": "#5FA8D3",
    "ink": "#10151C",
    "paper": "#F5F7FA",
    "muted": "#6B7684",
}
OUTCOME_ORDER = ("FF", "FP", "PF", "PP")
OUTCOME_HINTS = {
    "FF": "both tests fail",
    "FP": "test 1 fails / test 2 passes",
    "PF": "test 1 passes / test 2 fails",
    "PP": "both tests pass",
}
OUTCOME_FILL = {"FF": PALETTE["slate"], "FP": PALETTE["amber"], "PF": PALETTE["amber"], "PP": PALETTE["sky"]}
OUTCOME_HATCH = {"FF": "////", "FP": "\\\\\\", "PF": "\\\\\\", "PP": "...."}
DEFAULT_FROZEN_LAMBDA = 0.02


def _fmt(value, width=7) -> str:
    return f"{float(value):.{5}f}".rjust(width)


def _interval_text(interval) -> str:
    low, high = interval
    if low is None or high is None:
        return "n/a"
    return f"[{_fmt(low, 6)} , {_fmt(high, 9)}]"


def plain_report(block_results, *, source_label, shots, lambda_star, prize_label, winner_label,
                 lambda_value, p_bound=None, product_tail=None, record_status="") -> str:
    """Human-readable full table; the printable artefact that accompanies the trial-board figure."""
    lines = [
        "================================================================================",
        "NEVER LOSE TWICE - two-question game",
        f"SOURCE: {source_label}",
        f"shots: {int(shots)}   prize rule: {prize_label}   frozen lambda*: {_fmt(lambda_star)}"
        f"   reward lambda for this table: {_fmt(lambda_value)}   best strategy: {winner_label}",
        f"recorded evidence: {record_status or 'no recorded IonQ runs yet'}",
        "--------------------------------------------------------------------------------",
        "block" + "          FF     FP     PF     PP   double-fail     mean passes      loss",
    ]
    for entry in block_results:
        counts = entry["outcome_counts"]
        line = (f"{entry['block'][:24]:<24}"
                + "".join(f"{counts[key]:>7}" for key in OUTCOME_ORDER)
                + f"{entry['f']:>15.5f}{entry['m']:>16.5f}{entry['loss']:>13.5f}")
        lines.append(line)
        p1, p2 = entry["marginal_pass"]
        (p1_low, p1_high), (p2_low, p2_high) = entry["uncertainties"]["marginal_pass_intervals"]
        lines.append(f"    test 1 pass p1 = {p1:.5f}  (95% CI [{p1_low:.5f}, {p1_high:.5f}])")
        lines.append(f"    test 2 pass p2 = {p2:.5f}  (95% CI [{p2_low:.5f}, {p2_high:.5f}])")
        ff_low, ff_high = entry["uncertainties"]["ff_interval"]
        lines.append(f"    double-failure f = {entry['f']:.5f}  (95% CI [{ff_low:.5f}, {ff_high:.5f}])")
        mean_interval = mean_pass_interval(entry)
        lo, hi = mean_interval["interval"]
        lines.append(f"    mean passes = {entry['m']:.5f}  "
                     f"(at least {100*mean_interval['coverage_at_least']:.0f}% CI [{lo:.5f}, {hi:.5f}], "
                     "union bound on marginal intervals; no test independence assumed)")
        if entry.get("double_failure_upper_if_zero") is not None:
            lines.append(f"    zero observed double failures: exact 95% upper bound "
                         f"1-0.05^(1/{int(entry['shots'])}) = {entry['double_failure_upper_if_zero']:.6f} "
                         f"(zero observed never means zero risk)")
    if p_bound is not None:
        lines.append("--------------------------------------------------------------------------------")
        lines.append("Mathematical reference (independent of shots): maximal legal product-channel pass "
                     + (f"p = {p_bound:.6f}" if p_bound is not None else "n/a"))
        if product_tail is not None:
            lines.append(f"    ideal product double-failure lower bound (1-p)^2 = {product_tail:.6f}; "
                         "applies to independent ideal product arms; no noisy-tail bound is claimed")
    lines += [
        "--------------------------------------------------------------------------------",
        "Finite-shot note: estimates are finite-shot samples and may cross theoretical bounds; "
        "the 95% intervals are exact per-block binomial intervals (IID shots assumed).",
        "Units: probabilities in [0,1], counts in shots, loss L = f + lambda*(2 - mean passes).",
        "Assumptions: " + "; ".join(block_results[0].get("assumptions", [])) if block_results else "Assumptions: n/a",
        "================================================================================",
    ]
    return "\n".join(lines)


def figure_text(figure) -> str:
    """Concatenate every text artist of a figure (for labelling tests and text alternatives)."""
    parts = []
    if figure.texts:
        parts.extend(text.get_text() for text in figure.texts)
    for axes in figure.axes:
        if axes.get_title():
            parts.append(axes.get_title())
        parts.extend(text.get_text() for text in axes.texts)
        parts.extend(text.get_text() for text in axes.get_xticklabels() + axes.get_yticklabels())
    return " ".join(part for part in parts if part)


def _pick_star_block(block_results, winner_label):
    for entry in block_results:
        if entry["block"] == winner_label:
            return entry
    return block_results[0] if block_results else None


def build_trial_board(block_results, *, source_label, shots, lambda_star, prize_label, winner_label,
                      lambda_value, record_status="", p_bound=None, product_tail=None):
    """Two-door trial board: four rounded outcome tokens, per-test meters and the prize ticket."""
    star = _pick_star_block(block_results, winner_label)
    figure = plt.figure(figsize=(11.5, 6.4), facecolor=PALETTE["paper"])
    grid = figure.add_gridspec(2, 6)
    board_ax = figure.add_subplot(grid[0, 0:3])
    ticket_ax = figure.add_subplot(grid[0, 3:6])
    meters_ax = figure.add_subplot(grid[1, :])

    figure.text(0.02, 0.965, "Never Lose Twice - two-question trial", fontsize=16, weight="bold",
                color=PALETTE["ink"])
    figure.text(0.02, 0.93,
                f"SOURCE: {source_label}   |   shots: {int(shots)}   |   prize: {prize_label}   |   "
                f"frozen lambda*: {_fmt(lambda_star)}   |   best: {winner_label}",
                fontsize=9.5, color=PALETTE["muted"])

    board_ax.set_xlim(0, 4)
    board_ax.set_ylim(0, 4)
    board_ax.axis("off")
    board_ax.set_title("Outcome tokens - two doors, two tests", fontsize=10, color=PALETTE["ink"])
    if star is not None:
        counts = star["outcome_counts"]
        total = int(star["shots"])
        for index, key in enumerate(OUTCOME_ORDER):
            x = index % 2
            y = 1 - index // 2
            patch = FancyBboxPatch((x * 2 + 0.15, y * 2 + 0.15), 1.7, 1.7, boxstyle="round,pad=0.05,rounding_size=0.12",
                                   linewidth=1.2, edgecolor=PALETTE["ink"], facecolor=OUTCOME_FILL[key],
                                   hatch=OUTCOME_HATCH[key], alpha=0.9)
            board_ax.add_patch(patch)
            value = counts.get(key, 0)
            percent = value / total if total else 0.0
            board_ax.text(x * 2 + 1.0, y * 2 + 1.45, key, ha="center", va="center", fontsize=15,
                          weight="bold", color="white")
            board_ax.text(x * 2 + 1.0, y * 2 + 1.05, OUTCOME_HINTS[key], ha="center", va="center",
                          fontsize=8, color="white")
            board_ax.text(x * 2 + 1.0, y * 2 + 0.65, f"{value} / {percent:.1%}", ha="center", va="center",
                          fontsize=9, color="white")
    board_ax.text(2.0, 0.06, "star block: " + (star["block"] if star else "n/a"),
                  ha="center", fontsize=8, color=PALETTE["muted"])

    ticket_ax.set_xlim(0, 10)
    ticket_ax.set_ylim(0, 10)
    ticket_ax.axis("off")
    ticket_ax.set_title("Prize ticket", fontsize=10, color=PALETTE["ink"])
    ticket_ax.add_patch(FancyBboxPatch((0.3, 0.3), 9.4, 9.4, boxstyle="round,pad=0.05,rounding_size=0.35",
                                       linewidth=2, edgecolor=PALETTE["amber"], facecolor="#FFF8E7"))
    ticket_lines = [
        ("Prize rule", prize_label),
        ("Frozen lambda*", _fmt(lambda_star)),
        ("Reward lambda (table)", _fmt(lambda_value)),
        ("Best strategy", winner_label),
        ("Recorded evidence", record_status or "no recorded IonQ runs yet"),
        ("Product tail promise", "never zero"),
    ]
    for row, (label, value) in enumerate(ticket_lines):
        ticket_ax.text(0.8, 8.6 - row * 1.15, f"{label}:", fontsize=9, color=PALETTE["muted"])
        ticket_ax.text(5.6, 8.6 - row * 1.15, value, fontsize=9, weight="bold", color=PALETTE["ink"])
    if p_bound is not None:
        ticket_ax.text(0.8, 1.4, f"ideal product pass bound p = {p_bound:.6f}", fontsize=8,
                       color=PALETTE["slate"])
        if product_tail is not None:
            ticket_ax.text(0.8, 0.7, f"ideal product double-failure floor (1-p)^2 = {product_tail:.6f}",
                           fontsize=8, color=PALETTE["slate"])

    meters_ax.set_title("Per-test pass rates (star block), 95% exact binomial intervals",
                        fontsize=10, color=PALETTE["ink"])
    meters_ax.set_xlim(0, 1)
    meters_ax.set_xlabel("probability of a test pass", fontsize=9, color=PALETTE["ink"])
    if star is not None:
        p1, p2 = star["marginal_pass"]
        (p1_low, p1_high), (p2_low, p2_high) = star["uncertainties"]["marginal_pass_intervals"]
        bars = meters_ax.barh(["test 1 (reference/prover pair)", "test 2 (reference/prover pair)"], [p1, p2],
                              color=[PALETTE["sky"], PALETTE["amber"]], xerr=[[p1 - p1_low, p2 - p2_low],
                                                                              [p1_high - p1, p2_high - p2]],
                              capsize=5)
        for bar, value in zip(bars, (p1, p2)):
            meters_ax.text(value + 0.015, bar.get_y() + bar.get_height() / 2, f"{value:.4f}",
                           va="center", fontsize=8, color=PALETTE["ink"])
    meters_ax.grid(axis="x", linestyle=":", color=PALETTE["muted"])

    figure.text(0.02, 0.035,
                "Intervals: exact per-block binomial, 95%, IID shots assumed; finite-shot samples may cross "
                "theoretical bounds. Units: probabilities in [0,1], counts in shots, "
                "loss L = f + lambda*(2 - mean passes). Double failures are never promised zero.",
                fontsize=8, color=PALETTE["muted"])
    return figure
