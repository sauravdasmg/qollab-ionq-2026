import json
import numpy as np
import pytest
import main as app
from circuit_pack import pack
from receipt import make_record, parse_records, transcript


class Result:
    def __init__(self, counts):
        self.counts=counts
        self.fetches=0
    def get_counts(self):
        self.fetches+=1
        assert self.fetches==1
        return self.counts


class Job:
    def __init__(self, counts):
        self.value=Result(counts)
        self.fetches=0
    def result(self):
        self.fetches+=1
        assert self.fetches==1
        return self.value


class Backend:
    name="ionq_simulator"
    def __init__(self):
        self.calls=0
        self.options=type("Options",(),{"noise_model":"aria-1"})()
    def set_options(self, **kwargs):
        assert kwargs=={"noise_model":"aria-1"}
        self.options.noise_model=kwargs["noise_model"]
    def run(self, q, shots):
        assert not isinstance(q,list)
        assert q.num_qubits<=25
        self.calls+=1
        assert self.calls==1
        self.job=Job({"0"*q.num_qubits:shots})
        return self.job


@pytest.mark.parametrize("frame",[0.,np.pi/2,np.pi/24,np.pi/2+np.pi/24,-1.,2*np.pi])
def test_one_job_fetch(monkeypatch,frame):
    b=Backend()
    monkeypatch.setattr(app,"backend",b,raising=False)
    record=app.main(100 if frame==-1 else 1000,frame)
    assert b.calls==b.job.fetches==b.job.value.fetches==1
    records,errors=parse_records("RECORD_JSON "+json.dumps(record))
    assert len(records)==1 and errors==[]


def test_empty_malformed_and_hash():
    assert parse_records("")[0]==[]
    assert parse_records("RECORD_JSON not json")[1]
    assert parse_records("[]")[1]
    assert parse_records("null")[1]
    q,m=pack()
    r=make_record({"0"*21:1000},m,1000,0,"aria-1")
    assert len(parse_records(json.dumps(r))[0])==1
    r["counts"]["0"*21]=999
    assert not parse_records(json.dumps(r))[0]
    r["noise_model"]="unknown"
    assert parse_records(json.dumps(r))[1]


def test_text_preserves_identical_fit():
    fit={"frequency":2.12345678901234,"contrast":.67890123456789,
         "frequency_ci":[2.,2.25],"contrast_ci":[.5,.8],"flag":"informative"}
    text=transcript(fit,"live built-in ideal")
    decoded=json.loads(text.splitlines()[2])
    assert decoded==fit
    assert "radians" in text


def test_builtin_list_and_download(monkeypatch):
    from eyes_core import sample_counts, PHASES, WIDTHS
    counts=[sample_counts(n,p,256,np.random.default_rng(73+j)) for n in WIDTHS for j,p in enumerate(PHASES)]
    class Ideal:
        name="basic_simulator"
        def run(self,qs,shots):
            assert len(qs)==36 and max(q.num_qubits for q in qs)==4
            self.job=Job(counts)
            return self.job
    b=Ideal()
    downloads=[]
    monkeypatch.setattr(app,"backend",b,raising=False)
    monkeypatch.setattr(app,"sendFile",lambda name,content_type,data:downloads.append((name,content_type,data)),raising=False)
    monkeypatch.setattr("matplotlib.pyplot.show",lambda:None)
    estimates=app.main()
    assert b.job.fetches==b.job.value.fetches==1
    assert len(estimates)==3
    assert {n for n,t,d in downloads}=={"eyes-free.wav","eyes-free-receipt.txt"}
    assert {n:t for n,t,d in downloads} == {"eyes-free.wav":"audio/wav", "eyes-free-receipt.txt":"text/plain"}
    assert {n:d for n,t,d in downloads}["eyes-free.wav"].startswith(b"RIFF")
    assert isinstance({n:d for n,t,d in downloads}["eyes-free-receipt.txt"], bytes)


def test_slots_and_single_ionq_submission(monkeypatch):
    from cloud_slots import SLOTS, build_slot
    for slot in SLOTS:
        q, _ = build_slot(slot)
        assert q.num_qubits <= 25
    b=Backend()
    monkeypatch.setattr(app,"backend",b,raising=False)
    record=app.main(100,"ignored",slot="E01")
    assert record["slot"] == "E01" and record["suite"] == "smoke"
    parsed, errors = parse_records("RECORD_JSON " + json.dumps(record))
    assert len(parsed) == 1 and not errors
    assert {"manifest_hash","shots","effective_noise_model"} <= record.keys()
    assert b.calls==b.job.fetches==b.job.value.fetches==1
