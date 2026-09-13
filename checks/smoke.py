"""Bounded end-to-end suite. Run: python -m checks.smoke --output results/smoke."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--evidence', type=Path, help='optional new compact evidence JSON')
    args = p.parse_args()
    if args.evidence and args.evidence.exists():
        p.error('--evidence already exists')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               MKL_NUM_THREADS='1', MPLCONFIGDIR=str(args.output/'mplconfig'))
    jobs = [
        ('offline-t2', ['-m', 'reproduction.run', 'offline-t2']),
        ('offline-t1', ['-m', 'reproduction.run', 'offline-t1']),
        ('offline-maintain', ['-m', 'reproduction.run', 'offline-maintain']),
        ('offline-distance', ['-m', 'reproduction.run', 'offline-distance']),
        ('offline-error', ['-m', 'reproduction.run', 'offline-error']),
        ('no-grow-t1', ['-m', 'reproduction.run', 'no-grow-t1']),
        ('no-grow-error', ['-m', 'reproduction.run', 'no-grow-error']),
        ('online-time', ['-m', 'reproduction.run', 'online-time']),
        ('online-legacy-bposd', ['-m', 'reproduction.run', 'online-legacy-error', '--decoder', 'bposd']),
        ('online-mwpm', ['-m', 'reproduction.run', 'online', '--decoder', 'pymatching']),
        ('online-bposd', ['-m', 'reproduction.run', 'online', '--decoder', 'bposd']),
        ('online-ip', ['-m', 'reproduction.run', 'online', '--decoder', 'ip']),
        ('ts-legacy', ['-m', 'reproduction.run', 'ts']),
        ('ts-probability', ['-m', 'reproduction.run', 'ts', '--ts-mode', 'probability']),
        ('dem-gen', ['-m', 'reproduction.dem']),
        ('dem-sweep', ['-m', 'reproduction.dem', '--decoder', 'bposd']),
    ]
    records = []
    def execute(name, command):
        start = time.monotonic()
        print('RUN', name, flush=True)
        with (args.output/f'{name}.log').open('w') as log:
            try:
                result = subprocess.run([sys.executable, *command], cwd=ROOT, env=env,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=240)
                status = result.returncode
            except subprocess.TimeoutExpired:
                status = 'timeout'
        records.append(dict(name=name, command=[sys.executable, *command],
                            exit_code=status, seconds=time.monotonic()-start))
        (args.output/'suite.json').write_text(json.dumps(records, indent=2)+'\n')
        if status != 0:
            raise RuntimeError(f'{name} failed ({status}); see {args.output/name}.log')
    execute('invariants', ['-m', 'unittest', 'discover', '-s', 'checks', '-v'])
    execute('published-ids', ['-m', 'checks.published_ids'])
    for name, command in jobs:
        shots = 2 if name.startswith('ts-') else (8 if name in ['online-ip', 'dem-gen', 'dem-sweep'] else 128)
        execute(name, command+['--smoke', '--shots', str(shots), '--output', str(args.output/name)])
        if not name.startswith('dem-'):
            execute(name+'-plot', ['-m', 'reproduction.plot', str(args.output/name),
                                  '--output', str(args.output/(name+'.png'))])
    execute('online-comparison', ['-m', 'reproduction.plot',
        *[str(args.output/n) for n in ['online-mwpm', 'online-bposd', 'online-ip']],
        '--output', str(args.output/'online-comparison.png')])
    execute('distance-full-grid', ['-m', 'reproduction.run', 'offline-distance',
        '--shots', '8', '--output', str(args.output/'distance-full-grid')])
    execute('published-replot', ['-m', 'reproduction.published',
        '--output', str(args.output/'published-replot')])
    if args.evidence:
        evidence = {'commands': records, 'runs': {}, 'logs': {}}
        for folder in sorted(args.output.iterdir()):
            if folder.is_dir():
                files = {}
                for filename in ['run.json', 'stats.csv', 'ts.json', 'dem-stats.json', 'sources.json']:
                    file = folder/filename
                    if file.exists():
                        files[filename] = file.read_text()
                if files:
                    evidence['runs'][folder.name] = files
            elif folder.suffix == '.log':
                evidence['logs'][folder.name] = folder.read_text()
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2)+'\n')
    print(f'PASS: {len(records)} commands. Evidence: {args.output}')

if __name__ == '__main__':
    main()
