import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from eyes_core import PHASES, probabilities
from experiments.run import configuration, reference_truth, truth_metrics, summarize
from fit import fit_counts


@pytest.mark.parametrize('suite,count', [('frozen',24),('fresh',20)])
def test_consumed_manifest_contract_and_file_digest(suite,count):
    path=Path('review/manifests')/(suite+'.json')
    args=argparse.Namespace(quick=False,suite=suite,independent_manifest=str(path))
    settings,m=configuration(args,details=True)
    assert len(settings[0])==count
    assert settings==(m['seeds'],m['noise_scales'],m['phase_frame'],m['shots_per_phase'],hashlib.sha256(path.read_bytes()).hexdigest())
    args.independent_manifest=None
    with pytest.raises(ValueError): configuration(args)
    args.independent_manifest='does-not-exist.json'
    with pytest.raises(FileNotFoundError): configuration(args)


@pytest.mark.parametrize('suite', ['frozen','fresh'])
@pytest.mark.parametrize('fault', ['owner','count','seeds','id','sampling_seed','instances','widths','scales','shots','frame','phases','suite','schema','unknown','bool_seed'])
def test_reject_manifest_mutations(monkeypatch,suite,fault):
    m=json.loads((Path('review/manifests')/(suite+'.json')).read_text(encoding='utf-8'))
    if fault=='owner': m['owner']='implementation_author'
    elif fault=='count': m['instance_count']=1
    elif fault=='seeds': m['seeds'][1]=m['seeds'][0]
    elif fault=='id': m['instances'][1]['id']=m['instances'][0]['id']
    elif fault=='sampling_seed': m['instances'][0]['sampling_seed']+=1
    elif fault=='instances': m['instances'].pop()
    elif fault=='widths': m['widths']=[8]
    elif fault=='scales': m['noise_scales']=[99]
    elif fault=='shots': m['shots_per_phase']=1
    elif fault=='frame': m['phase_frame']+=.01
    elif fault=='phases': m['phases_rad'][1]+=.01
    elif fault=='suite': m['suite']='development'
    elif fault=='schema': m['schema']='other'
    elif fault=='unknown': m['layout']='unsupported'
    elif fault=='bool_seed': m['seeds'][0]=True
    monkeypatch.setattr(Path, 'read_bytes', lambda self: json.dumps(m).encode('utf-8'))
    args=argparse.Namespace(quick=False,suite=suite,independent_manifest='mutated-manifest.json')
    with pytest.raises(ValueError): configuration(args)


def test_noisy_population_truth_and_coverage_include_abstentions():
    x=PHASES+np.pi/24
    vectors=[probabilities(2,p,1.0) for p in x]
    truth=reference_truth(2,x,vectors,1.0)
    assert np.array_equal(truth['reference_probabilities'],vectors)
    even=np.asarray(vectors)[:,[0,3]].sum(axis=1)
    assert np.allclose(truth['parity'],2*even-1)
    population=fit_counts(x,[{'0':1000*p,'1':1000*(1-p)} for p in even])
    assert truth['contrast']==population['contrast']
    assert truth['projection']['frequency']==population['frequency']
    scores=truth_metrics(population,truth)
    assert scores['absolute_errors']['contrast']==0
    assert scores['interval_coverage']['contrast']
    assert np.allclose(scores['reference_fit_residuals'],truth['projection']['residuals'])
    population['informative']=False
    row={'seed':1,'truth':truth,'config':{'noise_scale':1},'fit':population,
         'truth_metrics':scores,'checks':{'digital_fidelity':True,'identified':False}}
    summary=summarize([row])
    assert summary['n2/scale1']['empirical_interval_coverage']['contrast']['total']==1
    assert summary['n2/scale1']['empirical_interval_coverage']['contrast']['fraction']==1
    assert 'ci' not in summary['overall']['empirical_interval_coverage']['contrast']
    population['contrast_ci']=[0,truth['contrast']/2]
    population['frequency_ci']=[.5,.6]
    assert not any(truth_metrics(population,truth)['interval_coverage'].values())


def test_ideal_target_is_physical_boundary():
    truth=reference_truth(1,PHASES,[probabilities(1,p) for p in PHASES],0)
    assert truth['contrast']==1 and truth['projection']['frequency']==1
    assert max(abs(v) for v in truth['projection']['residuals'])<1e-12
