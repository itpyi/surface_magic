"""Run from the repository root: python -m reproduction.run --help."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import sinter
import stim
from .experiments import EXPERIMENTS, cases

ROOT = Path(__file__).resolve().parents[1]

def positive(s):
    v = int(s)
    if v <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return v

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('experiment', choices=EXPERIMENTS)
    p.add_argument('--smoke', action='store_true', help='small grid; retains physical circuit sizes')
    p.add_argument('--shots', type=positive, default=128, help='attempted shots per task (TS: trajectories)')
    p.add_argument('--max-errors', type=positive, default=None)
    p.add_argument('--workers', type=positive, default=1)
    p.add_argument('--decoder', choices=['pymatching', 'bposd', 'ip'], default='pymatching')
    p.add_argument('--p', type=float, nargs='+', help='physical error probabilities for error sweeps')
    p.add_argument('--seed', type=int, default=20260913, help='IP/TS seed; sinter 1.13 does not expose a seed')
    p.add_argument('--ip-timeout', type=float, default=30, help='per-shot solve seconds; nonoptimal result fails')
    p.add_argument('--ts-mode', choices=['legacy', 'probability'], default='legacy')
    p.add_argument('--output', type=Path, required=True, help='new output directory; never overwrites prior runs')
    return p

def provenance(args):
    def git(*argv):
        return subprocess.check_output(['git', '-C', str(ROOT), *argv], text=True).strip()
    return dict(arguments=vars(args) | {'output': str(args.output)},
                python=sys.version, platform=platform.platform(),
                packages={p: importlib.metadata.version(p) for p in
                          ['numpy', 'scipy', 'stim', 'sinter', 'pymatching', 'galois', 'stimbposd', 'ldpc']},
                git_commit=git('rev-parse', 'HEAD'), git_status=git('status', '--short'),
                source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for folder in ['reproduction', 'data_collection/src', 'no_grow/src', 'online/src', 'TS']
                    for p in sorted((ROOT/folder).glob('*.py'))},
                randomness='NumPy PCG64/Stim seeded' if args.decoder == 'ip' or args.experiment == 'ts'
                           else 'sinter 1.13 sampling is unseeded; statistical reproducibility only',
                non_claim='Smoke execution does not reproduce rare-event rates, error bars, or scaling exponents.')

def run(args):
    if importlib.metadata.version('sinter') != '1.13.0':
        raise RuntimeError('This reproduction requires sinter==1.13.0 (postselection regression guard)')
    if args.p is not None and any(not 0 < p < 0.5 for p in args.p):
        raise ValueError('--p must be strictly between zero and 0.5')
    if args.ip_timeout <= 0:
        raise ValueError('--ip-timeout must be positive')
    if args.decoder == 'ip' and args.experiment.startswith(('offline', 'no-grow')):
        raise ValueError('Use pymatching for offline postselection; IP is provided for online DEMs')
    args.output.mkdir(parents=True, exist_ok=False)
    record = provenance(args)
    start = time.monotonic()
    try:
        if args.experiment == 'ts':
            from TS.qrm_state import experiment
            rows = []
            ps = args.p or ([1e-3] if args.smoke else np.linspace(1e-3, 1e-2, 10).tolist())
            for i, p in enumerate(ps):
                for gate in ['S', 'T']:
                    d, e, v = experiment(args.shots, p, gate, seed=args.seed+i, mode=args.ts_mode)
                    rows.append(dict(p=p, gate=gate, mode=args.ts_mode, trajectories=args.shots,
                                     discard=float(d), logical_error=float(e), trajectory_variance=float(v)))
            (args.output/'ts.json').write_text(json.dumps(rows, indent=2)+'\n')
        else:
            tasks, stats = [], []
            for i, case in enumerate(cases(args.experiment, args.smoke, args.p)):
                # Match sinter 1.13 worker serialization and the saved .stim input.
                circuit = stim.Circuit(str(case.circuit))
                circuit.to_file(args.output/f'{i:03}.stim')
                if args.decoder == 'ip':
                    from .ip import IPDecoder
                    dem = circuit.detector_error_model()
                    dem.to_file(args.output/f'{i:03}.dem')
                    decoder = IPDecoder(dem, timeout=args.ip_timeout)
                    sampler = dem.compile_sampler(seed=args.seed+i)
                    n = errors = 0
                    t0 = time.monotonic()
                    while n < args.shots and (args.max_errors is None or errors < args.max_errors):
                        det, obs, _ = sampler.sample(shots=1)
                        prediction = decoder.decode_batch(det)
                        errors += int(np.any(prediction != obs))
                        n += 1
                    task = sinter.Task(circuit=circuit, detector_error_model=dem, decoder='ip', json_metadata=case.metadata)
                    stats.append(sinter.TaskStats(strong_id=task.strong_id(), decoder='ip',
                        json_metadata=case.metadata, shots=n, errors=errors, seconds=time.monotonic()-t0))
                else:
                    dem = circuit.detector_error_model(decompose_errors=args.decoder == 'pymatching')
                    dem.to_file(args.output/f'{i:03}.dem')
                    mask = sinter.post_selection_mask_from_4th_coord(circuit) if case.postselect else None
                    tasks.append(sinter.Task(circuit=circuit, detector_error_model=dem,
                                             postselection_mask=mask, json_metadata=case.metadata))
            if tasks:
                custom = {}
                if args.decoder == 'bposd':
                    from stimbposd import sinter_decoders
                    custom = sinter_decoders()
                stats = sinter.collect(num_workers=args.workers, tasks=tasks, decoders=[args.decoder],
                    custom_decoders=custom, max_shots=args.shots, max_errors=args.max_errors,
                    start_batch_size=min(100, args.shots), max_batch_size=min(100000, args.shots),
                    print_progress=False)
            for s in stats:
                if not (0 < s.shots <= args.shots and 0 <= s.discards <= s.shots and 0 <= s.errors <= s.shots-s.discards):
                    raise AssertionError(f'Invalid sampling counts: {s}')
            with (args.output/'stats.csv').open('w') as f:
                print(sinter.CSV_HEADER, file=f)
                for s in sorted(stats, key=lambda s: json.dumps(s.json_metadata, sort_keys=True)):
                    print(s.to_csv_line(), file=f)
            record['tasks'] = len(stats)
            record['shots'] = sum(s.shots for s in stats)
            record['discards'] = sum(s.discards for s in stats)
            record['errors'] = sum(s.errors for s in stats)
        record['status'] = 'completed'
    except BaseException as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic()-start
        record['outputs_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(args.output.iterdir()) if p.is_file()}
        (args.output/'run.json').write_text(json.dumps(record, indent=2)+'\n')
    print(f"Completed {args.experiment}: {args.output}")

def main(argv=None):
    run(parser().parse_args(argv))

if __name__ == '__main__':
    main()
