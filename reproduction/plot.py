"""Plot fresh run outputs; zero-error samples get Wilson intervals, not log fits."""
import argparse
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/magic-reproduction-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sinter


def interval(errors, total):
    if total <= 0:
        return np.nan, np.nan, np.nan
    rate = errors/total
    z = 1.96
    den = 1+z*z/total
    center = (rate+z*z/(2*total))/den
    half = z*np.sqrt(rate*(1-rate)/total+z*z/(4*total*total))/den
    return rate, min(rate, max(0, center-half)), max(rate, min(1, center+half))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inputs', type=Path, nargs='+', help='run directories of the same experiment')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(argv)
    if args.output.exists():
        p.error('output already exists')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    names = set()
    for folder in args.inputs:
        record = json.loads((folder/'run.json').read_text())
        if record['status'] != 'completed':
            raise ValueError(f'Incomplete run: {folder}')
        name = record['arguments']['experiment']
        names.add(name)
        if len(names) != 1:
            raise ValueError('Compare only runs of the same experiment in one plot')
        if name == 'ts':
            rows = json.loads((folder/'ts.json').read_text())
            for gate in ['S', 'T']:
                rs = sorted([r for r in rows if r['gate'] == gate], key=lambda r:r['p'])
                for ax, key in zip(axes, ['logical_error', 'discard']):
                    ax.plot([r['p'] for r in rs], [r[key] for r in rs], 'o-', label=f"{gate} ({rs[0]['mode']})")
            xkey = 'p'
        else:
            rows = sinter.read_stats_from_csv_files(folder/'stats.csv')
            decoder = record['arguments']['decoder']
            xkey = {'offline-t1':'T_before_grow', 'offline-t2':'T_ps_grow',
                    'offline-maintain':'T_maintain', 'offline-distance':'d2',
                    'no-grow-t1':'T_before_grow', 'online-time':'t_round'}.get(name, 'error_rate')
            if name in ['online', 'online-legacy-error']:
                by_p = {}
                for r in rows:
                    by_p.setdefault(r.json_metadata['error_rate'], {})[r.json_metadata['stage']] = r
                xs, ys, lows, highs = [], [], [], []
                for x, stages in sorted(by_p.items()):
                    before, after = [interval(stages[s].errors, stages[s].shots) for s in ['before', 'after']]
                    xs.append(x); ys.append(after[0]-before[0])
                    lows.append(after[1]-before[2]); highs.append(after[2]-before[1])
                axes[0].errorbar(xs, ys, yerr=[np.array(ys)-lows, np.array(highs)-ys], fmt='o-', label=decoder)
                axes[0].axhline(0, color='gray', lw=.5)
                axes[1].text(.5, .5, 'Online: no postselection\nDifference = after − before', ha='center', va='center', transform=axes[1].transAxes)
            else:
                rows = sorted(rows, key=lambda r:r.json_metadata[xkey])
                xs = [r.json_metadata[xkey] for r in rows]
                for ax, discards in zip(axes, [False, True]):
                    vals = [interval(r.discards if discards else r.errors,
                                     r.shots if discards else r.shots-r.discards) for r in rows]
                    y, lo, hi = np.array(vals).T
                    ax.errorbar(xs, y, yerr=[y-lo, hi-y], fmt='o-', label=f'{name}/{decoder}')
        for ax in axes:
            ax.set_xlabel(xkey)
    axes[0].set_ylabel('Logical error rate (conditional if postselected)')
    axes[1].set_ylabel('Discard fraction')
    for ax in axes:
        ax.grid(alpha=.2)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=8)
    fig.suptitle(' / '.join(names)+' — finite samples; no scaling fit')
    fig.tight_layout()
    fig.savefig(args.output, dpi=160)
    plt.close(fig)
    print(f'Plot: {args.output}')

if __name__ == '__main__':
    main()
