"""Conditional T01..T10 plan slots (plan NT01..NT10); no automatic submissions.

Orchestrator audits account allowance and retired W/N allocations before use.
Eight science attempts total 20,000 shots; two exact retries reserve <=8,000.
Failed attempts are charged; at most one retry per failed science case.
"""
SLOTS = {}
for index, model in ((1, 'aria-2'), (3, 'aria-1'), (5, 'forte-1'), (7, 'aria-1')):
    for offset, game, shots in ((0, 'W', 1000), (1, 'N', 4000)):
        fresh = index == 7
        SLOTS[f'T{index + offset:02d}'] = {
            'games': [game], 'noise_model': model, 'shots': shots,
            'seed': (2026104100 if game == 'W' else 2026104300) if fresh else None,
            'purpose': 'fixed fresh corroboration' if fresh else 'standard-frame/analytic-anchor corroboration',
        }
for index in (9, 10):
    SLOTS[f'T{index:02d}'] = {
        'games': [], 'noise_model': 'inherit exact failed slot', 'shots': 4000,
        'purpose': 'exact failed science attempt retry, or unused; ceiling 4000 shots',
    }


def resolve_slot(slot, retry_of=''):
    if slot not in SLOTS:
        raise ValueError('slot must be T01..T10')
    if slot in ('T09', 'T10'):
        if retry_of not in tuple(f'T{i:02d}' for i in range(1, 9)):
            raise ValueError('retry slot requires retry_of=T01..T08 for an audited failed attempt')
        config = dict(SLOTS[retry_of])
        config['retry_of'] = retry_of
    else:
        if retry_of:
            raise ValueError('retry_of applies only to T09/T10')
        config = dict(SLOTS[slot])
    config['slot'] = slot
    return config
