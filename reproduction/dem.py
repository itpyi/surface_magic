"""Generate or sample online DEMs without manually coordinating filenames."""
import argparse
import json
from pathlib import Path
import numpy as np
import stim
from .experiments import cases
from .ip import IPDecoder

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True, help='new directory')
    p.add_argument('--input', type=Path, help='optional existing .dem file to sample')
    p.add_argument('--shots', type=int, default=8)
    p.add_argument('--seed', type=int, default=20260913)
    p.add_argument('--decoder', choices=['ip', 'pymatching', 'bposd'], default='ip')
    p.add_argument('--smoke', action='store_true')
    args = p.parse_args(argv)
    if args.shots <= 0:
        p.error('--shots must be positive')
    args.output.mkdir(parents=True, exist_ok=False)
    entries = []
    if args.input:
        entries = [(args.input.stem, stim.DetectorErrorModel.from_file(args.input))]
    else:
        for i, case in enumerate(cases('online', args.smoke)):
            entries.append((f'{i:03}-{case.metadata["stage"]}', stim.Circuit(str(case.circuit)).detector_error_model(
                decompose_errors=args.decoder == 'pymatching')))
    rows = []
    for i, (name, dem) in enumerate(entries):
        dem.to_file(args.output/f'{name}.dem')
        if args.decoder == 'ip':
            decoder = IPDecoder(dem)
        elif args.decoder == 'pymatching':
            import pymatching
            decoder = pymatching.Matching.from_detector_error_model(dem)
        else:
            from stimbposd import BPOSD
            decoder = BPOSD(dem, max_bp_iters=20)
        det, obs, _ = dem.compile_sampler(seed=args.seed+i).sample(shots=args.shots)
        predicted = decoder.decode_batch(det)
        if predicted.shape != obs.shape:
            raise RuntimeError('Decoder returned wrong observable shape')
        rows.append(dict(name=name, decoder=args.decoder, shots=args.shots, seed=args.seed+i,
                         errors=int(np.count_nonzero(np.any(predicted != obs, axis=1)))))
    (args.output/'dem-stats.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(f'Generated and decoded {len(rows)} DEMs: {args.output}')

if __name__ == '__main__':
    main()
