import argparse
import numpy as np
import pytest
from eyes_core import PHASES, WIDTHS, sample_counts
from experiments.run import evaluate, configuration, summarize, binomial_interval
from main import analyze


def test_harness_reproduces_main_identical_counts():
    counts=[sample_counts(n,p,100,np.random.default_rng(812+j)) for n in WIDTHS for j,p in enumerate(PHASES)]
    assert evaluate(counts)==analyze(counts)


def test_quick_bounds_and_fresh_requires_manifest():
    a=argparse.Namespace(quick=True,suite=None,independent_manifest=None)
    seeds,scales,shift,shots,h=configuration(a)
    assert len(seeds)<=2 and seeds[0]==2026100400
    assert scales==[0.,1.]
    assert shots<=1000
    a.quick=False;a.suite="fresh"
    with pytest.raises(ValueError): configuration(a)


def test_full_denominator_abstention():
    rows=[]
    for seed,info in [(1,True),(2,False)]:
        rows.append({"seed":seed,"truth":{"width":4},"config":{"noise_scale":1},
                     "fit":{"informative":info},"checks":{"digital_fidelity":True,"identified":True}})
    s=summarize(rows)["n4/scale1"]
    assert s["availability"]==.5
    assert s["abstentions"]==1
    assert s["audio_success_full_denominator"]==.5
    assert not s["thresholds_met"]
    assert binomial_interval(0,0)==[0.,1.]
