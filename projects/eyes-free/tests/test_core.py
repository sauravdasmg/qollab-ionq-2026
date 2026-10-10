import numpy as np
import pytest
from eyes_core import WIDTHS, PHASES, circuit, probabilities, fringe, sample_counts
from fit import fit_counts
from sonify import wav_bytes, samples
from experiments.decode import decode
from circuit_pack import pack, unpack, smoke_pack


def synthetic(f=2.0, c=.8, offset=.05, phase=.13, shots=2000):
    y = offset+c*np.cos(f*PHASES+phase)
    return [{"0": int(round(shots*(1+v)/2)), "1": shots-int(round(shots*(1+v)/2))} for v in y]


def test_exact_fringe_and_controls():
    for n in WIDTHS:
        for control in ("ghz", "product", "incoherent"):
            for phi in (.0, .31, 1.1):
                p = probabilities(n, phi, control=control)
                parity = sum((-1)**k.bit_count()*v for k,v in enumerate(p))
                assert parity == pytest.approx(fringe(n,phi,control), abs=1e-12)
    assert fringe(4,np.pi/4) == pytest.approx(-1)
    assert fringe(4,np.pi/2) == pytest.approx(1)


def test_unknown_frequency_and_alias():
    e = fit_counts(PHASES, synthetic(2.37))
    assert abs(e["frequency"]-2.37)<.01
    assert e["contrast"] == pytest.approx(.8,abs=.01)
    assert e["phase_rad"] == pytest.approx(.13,abs=.02)
    assert e["offset"] == pytest.approx(.05,abs=.01)
    e4 = fit_counts(PHASES, synthetic(4, .8, 0, 0))
    assert abs(e4["frequency"]-4)<.01
    assert e4["frequency_ci"][0]>3.5
    assert e4["frequency_ci"][1]<4.5
    assert e4["informative"]


def test_zero_contrast_inconclusive():
    e=fit_counts(PHASES,[{"0":500,"1":500}]*12)
    assert not e["informative"]
    assert e["flag"]=="inconclusive"
    assert e["contrast_ci"][0]==0
    assert e["diagnostics"]["low_signal"]


def test_pack_little_endian_asymmetry_and_totals():
    q,m=pack()
    assert q.num_qubits==21
    assert [b["offset"] for b in m]==[0,1,3,7,8,10,14,15,17]
    counts={format((1<<0)|(1<<4)|(1<<18),"021b"):71,"0"*21:29}
    parts=unpack(counts,m)
    assert parts[0]=={"1":71,"0":29}
    assert parts[2]=={"0010":71,"0000":29}
    assert parts[8]=={"0010":71,"0000":29}
    assert all(sum(p.values())==100 for p in parts)
    q,m=smoke_pack()
    from qiskit.quantum_info import Statevector
    p=Statevector.from_instruction(q.remove_final_measurements(inplace=False)).probabilities_dict()
    key=max(p,key=p.get)
    assert [next(iter(c)) for c in unpack({key:100},m,19)]==[b["expected"] for b in m]


def test_samples_only_audio():
    estimate={"frequency":2.371,"contrast":.643}
    raw=wav_bytes(estimate)
    d=decode(raw)
    assert abs(d["frequency"]-estimate["frequency"])<.02
    assert abs(d["contrast"]-estimate["contrast"])<.01
    x=samples(estimate)
    assert len(x)==96000
    assert np.max(abs(x))<=.5*estimate["contrast"]
    assert x[0]==x[-1]==0


def test_noise_is_normalized_and_reduces_contrast():
    p=probabilities(4,0,1)
    assert p.sum()==pytest.approx(1)
    assert np.min(p)>=0
    parity=sum((-1)**k.bit_count()*v for k,v in enumerate(p))
    assert 0<parity<1
