"""Verify the shipped fresh receipt against the saved full suite, without simulation."""
import json
from pathlib import Path

import nt_curves
import recorded_local


def test_fresh_receipt_exactly_matches_saved_metadata():
    root = Path(__file__).resolve().parents[1]
    source = json.loads((root / 'results/fresh.json').read_text(encoding='utf-8'))
    receipt = recorded_local.FRESH
    configuration = source['manifest']['configuration']
    for key in ('suite', 'label', 'started_utc', 'ended_utc',
                'consumed_manifest_sha256', 'analysis_config', 'fresh_comparison'):
        assert receipt[key] == source[key]
    for key in ('machine', 'simulator', 'versions'):
        assert receipt[key] == configuration[key]
    for key, value in receipt['settings'].items():
        assert value == configuration[key]
    assert receipt['configuration_sha256'] == source['manifest']['configuration_sha256']
    assert receipt['instance_ids'] == source['manifest']['instance_ids']
    assert receipt['fresh_comparison']['N']['pass'] is False


def test_shipped_decisions_disclose_failed_precision_and_agreement():
    expected = 'LOCAL_CONDITIONS_ONLY; N precision and frozen/fresh agreement gates not met'
    assert recorded_local.LOCAL['gate']['decision'] == expected
    for suite in ('frozen', 'fresh'):
        assert nt_curves.CURVES['suites'][suite]['gate']['decision'] == expected
    n = nt_curves.CURVES['suites']['frozen']['analysis']['N']['aria-1']
    assert n['precision_target_met'] is False
    assert abs(n['ci_width'] - 0.325) < 1e-12
