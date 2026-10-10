"""The Noise Tax: injected Qollab backend; short ideal default, cached evidence.

This effort is supported by Qollab & IonQ.
Enable Qiskit/NumPy/SciPy/Matplotlib. No provider credentials or input prompts.
Qollab calls main itself. No experiments/optimization/bootstrap at startup.
"""
import nt_curves
from cloud_slots import resolve_slot
import math
import numbers
from qiskit import transpile
import whispers_core as w
import hedging_core as n
from circuit_pack import pack_circuits, unpack_counts
from receipt import utc_now, make_record, format_record, digest
import recorded_ionq
from recorded_parser import summarize_record

def analyze_demo(counts, manifests):
    wa = w.analyze_counts(counts[:3], manifests['W'])
    na = n.analyze_probabilities(counts[3:], manifests['N'])
    return {'W': wa, 'N': na}

def _print_summary(summary, label):
    wa, na = summary['W'], summary['N']
    print(f"{label} W joint error={wa['joint']['word_error']:.5f}; signed advantage vs ideal one-way={wa['advantage']:+.5f}")
    for arm in n.BLOCKS:
        a = na[arm]
        print(f"{label} N {arm}: FF={a['double_failure']:.5f}, mean passes={a['mean_passes']:.5f}, loss={a['loss']:.5f}")
    print(f"{label} N signed advantage product-loss minus hedge-loss={na['advantage']:+.5f}; prize penalty=0.02")

def main(shots: int = 512, noise_model: str = 'aria-1', slot: str = '', retry_of: str = ''):
    if isinstance(shots, bool) or not isinstance(shots, numbers.Integral) or not 1 <= shots <= 4000:
        raise ValueError('shots must be an integer in 1..4000')
    active = globals().get('backend')
    if active is None:
        raise RuntimeError('Qollab must inject backend before main()')
    if slot:
        return run_slot(active, slot, retry_of)
    if retry_of:
        raise ValueError('retry_of requires a retry slot')
    name = active.name() if callable(active.name) else active.name
    cloud = name == 'ionq_simulator'
    if cloud:
        if noise_model not in ('aria-1', 'aria-2', 'forte-1', 'forte-enterprise-1'):
            raise ValueError('unknown IonQ simulator model')
        active.set_options(noise_model=noise_model)
    print('LIVE progress 1/3: preparing three 2-qubit double-trine labels and two 4-qubit hedging arms')
    wc, wm = w.make_demo(); nc, nm = n.make_instance_demo()
    manifests = {'W': wm, 'N': nm}
    # Portable abstract gate interface; no huge ideal statevector pack.
    circuits = transpile(wc+nc, basis_gates=['rx', 'ry', 'rz', 'cx'],
                         optimization_level=1, seed_transpiler=1234)
    started = utc_now()
    if cloud:
        packed, layout = pack_circuits(circuits, max_qubits=25)  # 14q, one job
        for entry, block in zip(layout, wm['ordered_blocks'] + [{'arm': a} for a in n.BLOCKS]):
            entry['manifest_hash'] = digest(block)
        print(f'LIVE IonQ simulator progress 2/3: one packed 14-qubit job, model={noise_model}, shots={shots}')
        job = active.run(packed, shots=int(shots))
        result = job.result()  # exactly one result fetch
        raw = result.get_counts()
        counts = unpack_counts(raw, layout)
        label = 'LIVE IonQ simulator'
    else:
        print(f'LIVE progress 2/3: five small circuit blocks, shots per block={shots}')
        job = active.run(circuits, shots=int(shots))
        result = job.result()
        counts = [result.get_counts(i) for i in range(len(circuits))]
        label = 'LIVE selected simulator (built-in default ideal)'
    ended = utc_now(); summary = analyze_demo(counts, manifests)
    _print_summary(summary, label)
    print(f'LIVE ideal theory W joint success={w.P_JOINT:.8f}, one-way ideal reference={w.P_SEQ:.8f}, advantage={w.P_JOINT-w.P_SEQ:+.8f}')
    product_ff = (1-math.cos(math.pi/8)**2)**2
    ideal_product_loss = product_ff+.02*(2-2*math.cos(math.pi/8)**2)
    print(f'LIVE ideal theory N hedge FF=0; product FF={product_ff:.8f}; fixed-prize ideal advantage={ideal_product_loss-.02:+.8f}')
    records, statuses = recorded_ionq.parse_records()
    print(f'RECORDED progress 3/3: {len(records)} validated historical receipts; {sum(not s["ok"] for s in statuses)} receipt issues')
    for record in records:
        for anchor in summarize_record(record):
            print(f"RECORDED CLOUD SAMPLING {anchor['game']} {anchor['model']}: 95% binomial component bounds, propagated advantage interval={anchor['cloud_sampling']['advantage_interval']}")
            if anchor['game'] == 'W':
                print(f"RECORDED IonQ simulator W {anchor['model']}: shots={anchor['shots']}/label, textbook joint error={anchor['word_error']:.5f}, advantage={anchor['advantage']:+.5f}")
            else:
                a = anchor['metrics']
                print(f"RECORDED IonQ simulator N {anchor['model']}: shots={anchor['shots']}/arm, hedge FF={a['published_hedge']['double_failure']:.5f}, product FF={a['attained_product']['double_failure']:.5f}, fixed-prize advantage={anchor['advantage']:+.5f}")
    for s in statuses:
        if not s['ok']:
            print(f'RECORDED receipt issue line {s["line"]}: {s["error"]}')
    print_curves()
    if cloud:
        job_id = job.job_id() if callable(getattr(job, 'job_id', None)) else getattr(job, 'job_id', None)
        record = make_record(packed, layout, raw, manifests, int(shots), noise_model, started, ended, job_id)
        # The only raw console JSON is the mandated pasteable cloud receipt.
        print(format_record(record))
    return summary


def print_curves():
    print(nt_curves.LABEL)
    for suite, data in nt_curves.CURVES['suites'].items():
        for game, models in data['analysis'].items():
            for model, a in models.items():
                point, inv = a['point'], a['inversion']
                uncertainty = (f"DETERMINISTIC; numerical bracket={inv['numerical_grid_bracket']}; "
                               f"CALIBRATION SENSITIVITY s* range={a['calibration_sensitivity']['s_star_range']} (not a CI)"
                               if game == 'W' else
                               f"97.5% instance-bootstrap simultaneous-band CI={inv['confidence_interval']}; precision target met={a['precision_target_met']}")
                print(f"LOCAL MODEL {suite} n=24 {game} {model}: s*={point['estimate']}; {point['status']}; {uncertainty}")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    colors = ['#007a78', '#bc4328', '#555555']
    for ax, game in zip(axes, ('W', 'N')):
        for suite, data in nt_curves.CURVES['suites'].items():
            for color, (model, a) in zip(colors, data['analysis'][game].items()):
                grid = data['grid']
                ax.plot(grid, a['mean_advantage'], color=color,
                        linestyle='-' if suite == 'frozen' else '--', label=f'{suite} {model}')
                if game == 'N':
                    ax.fill_between(grid, a['lower_band'], a['upper_band'], color=color, alpha=.08)
                else:
                    for edge in a['calibration_sensitivity']['edges']:
                        ax.plot(grid, edge['mean_advantage'], color=color, linewidth=.5, alpha=.3)
        ax.axhline(0, color='black', linewidth=.8)
        ax.set(xlabel='Modeled noise scale s', ylabel='Signed advantage', title=game)
        ax.legend(fontsize=6)
    fig.suptitle(nt_curves.LABEL, fontsize=9)
    fig.tight_layout()
    plt.show()
    plt.close(fig)


def run_slot(active, slot, retry_of=''):
    config = resolve_slot(slot, retry_of)
    name = active.name() if callable(active.name) else active.name
    if name != 'ionq_simulator':
        raise ValueError('cloud slots require the free IonQ simulator; use empty slot for built-in default')
    model, shots = config['noise_model'], config['shots']
    active.set_options(noise_model=model)
    game = config['games'][0]
    if game == 'W':
        circuits, manifest = w.make_demo(w.make_instance(config['seed']), include_oneway=True)
        blocks = manifest['ordered_blocks']
    else:
        circuits, manifest = n.make_instance_demo(n.make_instance(config['seed']))
        blocks = [{'arm': arm} for arm in manifest['ordered_blocks']]
    circuits = transpile(circuits, basis_gates=['rx', 'ry', 'rz', 'cx'],
                         optimization_level=1, seed_transpiler=1234)
    packed, layout = pack_circuits(circuits, max_qubits=25)
    for entry, block in zip(layout, blocks):
        entry['manifest_hash'] = digest(block)
    print(f"LIVE {slot} {game}: {config['purpose']}; model={model}; shots={shots}; one {packed.num_qubits}-qubit packed job")
    started = utc_now()
    job = active.run(packed, shots=shots)
    result = job.result()
    raw = result.get_counts()
    counts = unpack_counts(raw, layout)
    ended = utc_now()
    analysis = w.analyze_counts(counts, manifest) if game == 'W' else n.analyze_probabilities(counts, manifest)
    if game == 'W':
        print(f"LIVE {slot} W joint error={analysis['joint']['word_error']:.5f}; advantage vs ideal one-way={analysis['advantage']:+.5f}; physical one-way error={analysis['oneway']['word_error']:.5f}")
    else:
        for arm in n.BLOCKS:
            a = analysis[arm]
            print(f"LIVE {slot} N {arm}: FF={a['double_failure']:.5f}; mean passes={a['mean_passes']:.5f}; loss={a['loss']:.5f}")
        print(f"LIVE {slot} N fixed-prize advantage={analysis['advantage']:+.5f}")
    job_id = getattr(job, 'job_id', None)
    record = make_record(packed, layout, raw, {game: manifest}, shots, model, started, ended,
                         job_id() if callable(job_id) else job_id)
    record.update({'slot': slot, 'slot_config': config})
    print(format_record(record))
    return {game: analysis}
