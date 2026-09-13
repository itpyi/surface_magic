"""Replot the data tables used in the published figures."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from .plot import plt, interval
import sinter

DATA = Path(__file__).resolve().parents[1]/'published_data'

def stat_plot(ax, filename, key, label):
    rows = sorted(sinter.read_stats_from_csv_files(DATA/filename), key=lambda r:r.json_metadata[key])
    xs = [r.json_metadata[key] for r in rows]
    vals = np.array([interval(r.errors, r.shots-r.discards) for r in rows])
    y, lo, hi = vals.T
    ax.errorbar(xs, y, yerr=[y-lo, hi-y], fmt='o-', label=label)
    ax.set_yscale('log')
    ax.set_xlabel(key)
    ax.set_ylabel('Conditional logical error rate')
    twin = ax.twinx()
    twin.plot(xs, [r.discards/r.shots for r in rows], 's--', color='tab:orange', label='Discard')
    twin.set_ylabel('Discard fraction', color='tab:orange')
    ax.legend(fontsize=8, loc='upper left')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(args.output/(name+'.png'), dpi=180)
        plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    stat_plot(ax[0], 'fig12a.csv', 'T_PS_GROW', 't2 sweep')
    stat_plot(ax[1], 'fig12b.csv', 'T_BEFORE_GROW', 't1 sweep')
    save(fig, 'postselection')
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for filename, label in [('fig13a_ungrown.csv', 'Ungrown'), ('fig3b&13a_grown.csv', 'Grown')]:
        rows = sorted(sinter.read_stats_from_csv_files(DATA/filename), key=lambda r:r.json_metadata['p'])
        x = [r.json_metadata['p'] for r in rows]
        for a, discard in zip(ax, [False, True]):
            values = np.array([interval(r.discards if discard else r.errors,
                              r.shots if discard else r.shots-r.discards) for r in rows])
            y, lo, hi = values.T
            a.errorbar(x, y, yerr=[y-lo, hi-y], fmt='o-', label=label)
            a.set_xlabel('Physical error rate'); a.set_xscale('log'); a.legend()
    ax[0].set_yscale('log'); ax[0].set_ylabel('Conditional logical error rate')
    ax[1].set_ylabel('Discard fraction')
    save(fig, 'grown-comparison')
    fig, ax = plt.subplots(figsize=(6, 4))
    stat_plot(ax, 'fig13b.csv', 'd', 'Second growth')
    save(fig, 'distance')
    with (DATA/'fig3a&11.csv').open() as f:
        rows = list(csv.DictReader(f))
    fig, ax = plt.subplots(figsize=(7, 4))
    for decoder in ['ip', 'matching', 'bposd']:
        xs, ys, lower, upper = [], [], [], []
        for r in rows:
            before = interval(int(r['errors_before']), int(r['shots_before']))
            after = interval(int(r['errors_'+decoder]), int(r['shots_'+decoder]))
            xs.append(float(r['p'])); ys.append(after[0]-before[0])
            lower.append(after[1]-before[2]); upper.append(after[2]-before[1])
        ax.errorbar(xs, ys, yerr=[np.array(ys)-lower, np.array(upper)-ys], fmt='o-', label=decoder)
    ax.set_xscale('log'); ax.set_yscale('log'); ax.legend()
    ax.set_xlabel('Physical error rate'); ax.set_ylabel('Logical error rate: after − before')
    save(fig, 'online-decoders')
    with (DATA/'fig14.csv').open() as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for gate in ['S', 'T']:
        x = [float(r['err_phy']) for r in rows]
        ax[0].plot(x, [float(r[gate+'_err']) for r in rows], 'o-', label=gate)
        ax[1].plot(x, [float(r[gate+'_ps']) for r in rows], 'o-', label=gate)
    for a in ax:
        a.set_xscale('log'); a.set_xlabel('Physical error rate'); a.legend()
    ax[0].set_yscale('log'); ax[0].set_ylabel('Original logical error estimate')
    ax[1].set_ylabel('Original discard estimate')
    fig.suptitle('S/T comparison: original Fig. 14 estimates')
    save(fig, 'ts-historical')
    (args.output/'sources.json').write_text(json.dumps({
        'operation':'Replot the published data tables',
        'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob('*.csv'))}
    }, indent=2)+'\n')
    print(f'Replotted five figures from the published data in {args.output}')

if __name__ == '__main__':
    main()
