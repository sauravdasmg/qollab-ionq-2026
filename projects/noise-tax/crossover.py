"""Preregistered paired-instance crossover and simultaneous-band inference.

Exact probabilities define the curve. Synthetic counts are a separate display.
97.5% per game provides nominal >=95% two-game Bonferroni coverage under
bootstrap assumptions; calibration uncertainty is excluded.
"""
import numpy as np

def _inputs(grid, curves):
    x = np.asarray(grid, float); y = np.asarray(curves, float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all() or np.any(np.diff(x) <= 0):
        raise ValueError('finite increasing grid required')
    if y.shape[-1] != len(x) or not np.isfinite(y).all():
        raise ValueError('finite curves matching grid required')
    return x, y

def crossing(grid, curve, atol=1e-12):
    x, y = _inputs(grid, curve)
    if y.ndim != 1:
        raise ValueError('one mean curve required')
    signs = np.where(np.abs(y) <= atol, 0, np.sign(y)).astype(int)
    roots, zero_segments = [], []
    i = 0
    while i < len(x):
        if signs[i] == 0:
            j = i
            while j+1 < len(x) and signs[j+1] == 0:
                j += 1
            if j > i:
                zero_segments.append([float(x[i]), float(x[j])])
            roots.append(float(x[i]))
            i = j+1
        else:
            if i+1 < len(x) and signs[i]*signs[i+1] < 0:
                roots.append(float(x[i] - y[i]*(x[i+1]-x[i])/(y[i+1]-y[i])))
            i += 1
    persistent = [r for r in roots if np.all(y[x > r+atol] <= atol)]
    first = min(persistent) if persistent else None
    if np.all(signs == 0):
        status = 'constant-zero'
    elif np.all(signs > 0):
        status = 'right-censored'
    elif np.all(signs < 0):
        status = 'left-censored'
    elif zero_segments or len(roots) > 1:
        status = 'nonunique'
    elif first is None:
        status = 'no-persistent-crossing'
    elif not x[0] < first < x[-1]:
        status = 'boundary'
    elif y[0] > atol and y[-1] < -atol:
        status = 'resolved'
    else:
        status = 'unresolved'
    return {'estimate': first, 'roots': roots, 'zero_segments': zero_segments,
            'status': status, 'right_censored': status == 'right-censored',
            'grid_resolution': float(np.max(np.diff(x)))}

def invert_band(grid, lower, upper):
    """Every piecewise-linear zero permitted by band; outward grid brackets.

    Taking all feasible roots is conservative for first-persistent roots.
    Disjoint feasible sets and unidentifiable endpoints are kept explicit.
    """
    x, lo = _inputs(grid, lower); _, hi = _inputs(grid, upper)
    if np.any(lo > hi):
        raise ValueError('inverted confidence band')
    feasible, brackets = [], []
    for i in range(len(x)-1):
        start, end = 0., 1.
        # lo(t)<=0 and -hi(t)<=0; intersect both affine half intervals.
        for a, b in ((lo[i], lo[i+1]), (-hi[i], -hi[i+1])):
            slope = b-a
            if abs(slope) < 1e-15:
                if a > 0:
                    start, end = 1., 0.
            elif slope > 0:
                end = min(end, -a/slope)
            else:
                start = max(start, -a/slope)
        if start <= end and end >= 0 and start <= 1:
            a = float(x[i]+max(0., start)*(x[i+1]-x[i]))
            b = float(x[i]+min(1., end)*(x[i+1]-x[i]))
            if feasible and a <= feasible[-1][1]+1e-12:
                feasible[-1][1] = max(feasible[-1][1], b)
            else:
                feasible.append([a, b])
            brackets.append([float(x[i]), float(x[i+1])])
    expanded = []
    for a, b in brackets:
        if expanded and a <= expanded[-1][1]+1e-12:
            expanded[-1][1] = max(expanded[-1][1], b)
        else:
            expanded.append([a, b])
    endpoints = bool(lo[0] > 0 and hi[-1] < 0)
    hull = [expanded[0][0], expanded[-1][1]] if expanded and endpoints else None
    return {'confidence_interval': hull, 'feasible_sets': feasible,
            'outward_grid_sets': expanded, 'endpoint_signs_resolved': endpoints,
            'status': 'resolved' if hull is not None else 'unresolved',
            'includes_right_boundary': bool(hi[-1] >= 0),
            'method': 'invert simultaneous band, all feasible roots, hull expanded to grid brackets'}

def analyze(grid, instance_curves, draws=4000, seed=2026104401, confidence=.975):
    x, curves = _inputs(grid, instance_curves)
    if curves.ndim != 2 or len(curves) < 2 or draws < 1 or not 0 < confidence < 1:
        raise ValueError('>=2 whole instance curves and positive draws required')
    mean = curves.mean(axis=0)
    rng = np.random.default_rng(seed)
    deviations = np.empty(draws)
    statuses = {}; finite_roots = []
    for i in range(draws):
        sampled = curves[rng.integers(len(curves), size=len(curves))].mean(axis=0)
        deviations[i] = np.max(np.abs(sampled-mean))
        root = crossing(x, sampled)
        statuses[root['status']] = statuses.get(root['status'], 0)+1
        if root['status'] == 'resolved':
            finite_roots.append(root['estimate'])
    radius = float(np.quantile(deviations, confidence, method='higher'))
    lower, upper = mean-radius, mean+radius
    point = crossing(x, mean)
    inversion = invert_band(x, lower, upper)
    ci = inversion['confidence_interval']
    valid = point['status'] == 'resolved' and inversion['endpoint_signs_resolved'] and ci is not None
    # No conditional finite-root percentile interval: censored/nonunique draws
    # are counted, never dropped to manufacture a finite interval.
    return {'mean_advantage': mean.tolist(), 'lower_band': lower.tolist(), 'upper_band': upper.tolist(),
            'point': point, 'inversion': inversion, 'confidence': confidence, 'draws': draws,
            'analysis_seed': seed, 'n_instances': len(curves), 'band_radius': radius,
            'bootstrap_status_counts': statuses, 'valid_interior_crossing': bool(valid),
            'ci_width': float(ci[1]-ci[0]) if ci else None,
            'precision_target_met': bool(valid and ci[1]-ci[0] <= .30),
            'inference_adequate': bool(draws >= 4000 and len(curves) >= 24),
            'limitations': ['paired whole-curve nonparametric bootstrap approximation',
                           'small-n uncertainty', 'excludes calibration/model uncertainty',
                           'disjoint root sets retained; no monotonicity imposed',
            'mean curve uses exact probabilities, not synthetic shots'],
            'uncertainty_source': 'N INSTANCE BOOTSTRAP; excludes calibration/model uncertainty'}

def deterministic(grid, instance_curves):
    """Conditional W root and numerical bracket, without a sampling CI."""
    x, curves = _inputs(grid, instance_curves)
    if curves.ndim != 2 or not len(curves):
        raise ValueError('whole W curves required')
    spread = float(np.max(np.abs(curves-curves[0])))
    if spread > 1e-12:
        raise ValueError('W frame invariance failed; revise deterministic estimand')
    mean = curves.mean(axis=0)
    point = crossing(x, mean)
    inverted = invert_band(x, mean, mean)
    bracket = inverted.pop('confidence_interval')
    inverted['numerical_grid_bracket'] = bracket
    inverted['method'] = 'deterministic piecewise-linear root; outward numerical grid bracket'
    valid = point['status'] == 'resolved' and bracket is not None
    width = float(bracket[1]-bracket[0]) if bracket else None
    return {'reporting': 'DETERMINISTIC', 'uncertainty_source': 'NUMERICAL GRID RESOLUTION',
            'mean_advantage': mean.tolist(), 'point': point, 'inversion': inverted,
            'n_instances': len(curves), 'max_frame_curve_difference': spread,
            'valid_interior_crossing': bool(valid), 'grid_bracket_width': width,
            'precision_target_met': bool(valid and width <= .30),
            'limitations': ['conditional on specified depolarizing model and frame family',
                            'grid bracket is not a sampling confidence interval',
                            'model mismatch is not quantified']}

def compare_fresh(frozen, fresh, tolerance=.10):
    a, b = frozen['point']['estimate'], fresh['point']['estimate']
    key = 'numerical_grid_bracket' if frozen.get('reporting') == 'DETERMINISTIC' else 'confidence_interval'
    ca, cb = frozen['inversion'][key], fresh['inversion'][key]
    valid = frozen['valid_interior_crossing'] and fresh['valid_interior_crossing']
    delta = abs(a-b) if a is not None and b is not None else None
    # Combined interval bounds for the difference, and absolute tolerance.
    difference_interval = [ca[0]-cb[1], ca[1]-cb[0]] if ca and cb else None
    agrees = bool(valid and delta <= tolerance and difference_interval[0] <= 0 <= difference_interval[1])
    return {'pass': agrees, 'absolute_difference': delta, 'tolerance': tolerance,
            'difference_interval': difference_interval, 'both_interior': bool(valid),
            'frozen_estimate': a, 'fresh_estimate': b}
