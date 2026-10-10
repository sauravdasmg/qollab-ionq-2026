"""Frozen frequency-blind binomial profile fit (no width/truth input)."""
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import chi2
from eyes_core import parity_counts

ALPHA = 0.05 / 6
GRID = np.linspace(0.5, 4.5, 161)
SPEC = {"grid_step": 0.025, "range": [0.5, 4.5], "alpha": ALPHA,
        "ties": "lowest frequency; separated profile components are inconclusive",
        "interval": "profile LR chi-square(1); grid envelope plus one-step conservative padding",
        "contrast": "profile-component union of joint Wald radii; grid-Bonferroni LR null required",
        "offset": "abs(offset)+hypot(cos,sin)<=1-1e-8 (numerical guard)", "reselection": "entire grid profiled every fit"}


def fit_counts(phases, counts):
    x = np.asarray(phases, float)
    if len(x) < 8 or len(x) != len(counts) or not np.all(np.isfinite(x)):
        raise ValueError("at least eight finite matched phases required")
    pairs = np.array([parity_counts(c) for c in counts], float)
    k, m = pairs.T
    y = 2 * k / m - 1
    def design(f):
        return np.column_stack((np.ones(len(x)), np.cos(f*x), np.sin(f*x)))
    def objective(b, a):
        p = np.clip((1 + a @ b) / 2, 1e-10, 1 - 1e-10)
        return float(-np.sum(k * np.log(p) + (m-k) * np.log1p(-p)))
    def profile(f):
        a = design(f)
        start = np.linalg.lstsq(a, y, rcond=None)[0]
        limit = 1-1e-8
        start *= min(1, limit / max(abs(start[0])+np.hypot(start[1],start[2]), 1e-12))
        def fun(b):
            return objective(b,a)/m.sum()
        def jac(b):
            p = np.clip((1+a@b)/2, 1e-10, 1-1e-10)
            return a.T @ ((m-k)/(1-p)-k/p)/(2*m.sum())
        def constraint(b):
            c = np.hypot(b[1],b[2])
            return np.array([limit-b[0]-c,limit+b[0]-c])
        def constraint_jac(b):
            c = max(np.hypot(b[1],b[2]),1e-12)
            return np.array([[-1.,-b[1]/c,-b[2]/c],[1.,-b[1]/c,-b[2]/c]])
        result = minimize(fun, start, jac=jac, method="SLSQP",
                          bounds=[(-limit,limit)]*3,
                          constraints={"type":"ineq", "fun":constraint, "jac":constraint_jac},
                          options={"maxiter":100, "ftol":1e-11})
        if not result.success:
            retry = minimize(fun, np.zeros(3), jac=jac, method="SLSQP",
                             bounds=[(-limit,limit)]*3,
                             constraints={"type":"ineq", "fun":constraint, "jac":constraint_jac},
                             options={"maxiter":150, "ftol":1e-10})
            if retry.success or retry.fun < result.fun:
                result = retry
        b = result.x.copy()
        b *= min(1, limit / max(abs(b[0])+np.hypot(b[1],b[2]),1e-12))
        return objective(b,a), b, bool(result.success)
    prof = [profile(f) for f in GRID]
    losses = np.array([v[0] for v in prof])
    candidates = [i for i in range(len(GRID)) if
                  (i == 0 or losses[i] <= losses[i-1]) and
                  (i == len(GRID)-1 or losses[i] <= losses[i+1])]
    refined = []
    for i in candidates:
        lo, hi = GRID[max(0, i-1)], GRID[min(len(GRID)-1, i+1)]
        r = minimize_scalar(lambda f: profile(f)[0], bounds=(lo, hi), method="bounded",
                            options={"xatol": 1e-6, "maxiter": 30})
        refined.append((float(r.fun), float(r.x)))
    best_loss = min(v[0] for v in refined)
    loss, f = min((v for v in refined if v[0] <= best_loss + 1e-6), key=lambda v: v[1])
    loss, b, converged = profile(f)
    cutoff = chi2.ppf(1-ALPHA, 1)
    accepted = 2 * (losses-loss) <= cutoff
    # Include the refined minimum even when a narrow peak falls between grid points.
    accepted[np.argmin(abs(GRID-f))] = True
    ix = np.flatnonzero(accepted)
    components = np.split(ix, np.where(np.diff(ix) > 1)[0]+1)
    interval = [max(0.5, float(GRID[ix[0]] - 0.025)),
                min(4.5, float(GRID[ix[-1]] + 0.025))]
    a = design(f)
    pred = a @ b
    c = float(np.hypot(b[1], b[2]))
    p = np.clip((1+pred)/2, 1e-8, 1-1e-8)
    selected = [(f, b)] + [(float(GRID[i]), prof[i][1]) for i in ix]
    contrast_intervals = []
    for frequency, coefficients in selected:
        matrix = design(frequency)
        pp = np.clip((1+matrix@coefficients)/2, 1e-8, 1-1e-8)
        df = x*(-coefficients[1]*np.sin(frequency*x)+coefficients[2]*np.cos(frequency*x))
        full = np.column_stack((matrix,df))
        information = full.T @ ((m/(4*pp*(1-pp)))[:,None]*full)
        cov = np.linalg.pinv(information)
        radius = float(np.sqrt(chi2.ppf(1-ALPHA/len(GRID),4) *
                               max(0,np.linalg.eigvalsh(cov[1:3,1:3]).max())))
        cc = float(np.hypot(coefficients[1],coefficients[2]))
        contrast_intervals.append((max(0.,cc-radius),min(1.,cc+radius)))
    ci_c = [min(v[0] for v in contrast_intervals),max(v[1] for v in contrast_intervals)]
    null = objective([float(np.sum(m*y)/m.sum()), 0, 0], a)
    lr = max(0.0, 2*(null-loss))
    signal = ci_c[0] > 0 and lr > chi2.ppf(1-ALPHA/len(GRID), 3)
    ambiguous = len(components) != 1 or interval[1]-interval[0] >= 1 or interval[0] == 0.5 or interval[1] == 4.5
    informative = bool(signal and not ambiguous and converged and all(v[2] for v in prof))
    return {"frequency": f, "frequency_ci": interval, "contrast": c, "contrast_ci": ci_c,
            "phase_rad": float(np.arctan2(-b[2], b[1])), "offset": float(b[0]),
            "cos_coefficient": float(b[1]), "sin_coefficient": float(b[2]),
            "residuals": (y-pred).tolist(), "parity": y.tolist(), "shots": m.astype(int).tolist(),
            "counts": [{str(key):int(value) for key,value in row.items()} for row in counts],
            "phases_rad": x.tolist(), "alpha": ALPHA, "informative": informative,
            "flag": "informative" if informative else "inconclusive",
            "diagnostics": {"profile_grid": GRID.tolist(), "profile_lr": (2*(losses-loss)).tolist(),
                            "components": len(components), "converged": converged,
                            "all_grid_converged": all(v[2] for v in prof), "null_lr": lr,
                            "low_signal": not bool(signal), "ambiguous": bool(ambiguous), "spec": SPEC}}
