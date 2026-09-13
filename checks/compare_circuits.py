"""Compare every smoke circuit byte-for-byte with pre-refactor d816424 sources."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from reproduction.experiments import EXPERIMENTS, cases

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'd816424'

def main():
    count = 0
    with tempfile.TemporaryDirectory(prefix='magic-baseline-') as tmp:
        tmp = Path(tmp)
        for family in ['data_collection', 'no_grow', 'online']:
            folder = tmp/family/'src'
            folder.mkdir(parents=True)
            names = ['__init__.py', 'magic.py', 'surface_code.py', 'surgery.py', 'qrm.py']
            if family == 'data_collection':
                names.append('magicd2.py')
            for name in names:
                data = subprocess.check_output(['git', 'show', f'{BASELINE}:{family}/src/{name}'], cwd=ROOT)
                (folder/name).write_bytes(data)
        for experiment in EXPERIMENTS:
            if experiment == 'ts':
                continue
            for case in cases(experiment, smoke=True):
                kw = {k:v for k,v in case.metadata.items() if k not in ['experiment', 'stage']}
                family = 'data_collection' if experiment.startswith('offline') else (
                    'no_grow' if experiment.startswith('no-grow') else 'online')
                module = 'magicd2' if experiment == 'offline-distance' else 'magic'
                script = 'import json,sys; from src import '+module+' as m; print(m.magic_preparation(**json.loads(sys.argv[1])))'
                original = subprocess.check_output([sys.executable, '-c', script, json.dumps(kw)], cwd=tmp/family, text=True)
                if original.strip() != str(case.circuit).strip():
                    raise AssertionError(case.metadata)
                count += 1
    print(f'PASS: {count} circuits identical to {BASELINE}; only imports/entry points changed.')

if __name__ == '__main__':
    main()
