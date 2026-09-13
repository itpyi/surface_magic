# Magic teleportation with generalized lattice surgery — numerics

Supplementary simulations for **Physical Review A 113(6), 062410**
([preprint](https://arxiv.org/abs/2503.19758)). The reference for this organization
is `67e2bd967ff14df0f46f7620/supp.tex` in the parent research directory: Supplement
D, “A numeric simulation of the QRM-surface code example”. That source is the
author's last Overleaf export; final publication proof edits are not included.
The repository itself runs independently of the parent directory.

## Install

Use Python **3.11**, in a fresh environment. From this repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

Alternatively, `conda env create -f environment.yml`, then
`conda activate magic-reproduction`. The lock includes all installed Python
dependencies; the tested platform is macOS arm64. Other platforms are not
certified by this run.

**Keep sinter 1.13.0**, with Stim 1.15.0, PyMatching 2.3.0 and NumPy 1.26.4.
Sinter 1.13 requires NumPy below 2. The sampling entry point checks the sinter
version before running. This intentionally preserves the working postselection
path, as described in the author's
[StackExchange report](https://quantumcomputing.stackexchange.com/questions/44364/how-to-use-sinter-to-collect-stats-with-postselection/44479#44479).
Do not upgrade sinter as part of ordinary dependency maintenance without testing
accepted and discarded shots together. This is a project compatibility pin,
not a statement that every later release has the same defect.

## Small-scale reproduction

```bash
python -m checks.smoke --output results/my-smoke
```

This runs all 12 maintained historical Python entry points, the canonical online
BP-OSD/IP paths, both S/T estimator modes, invariant checks, and fresh-data plots.
Each ordinary circuit task attempts **128 shots**, IP/DEM tasks **8 shots**,
and each S/T gate uses **2 trajectories** per physical error rate. One worker
is used. Smoke grids retain both postselection boundary values and both online
stages; circuit sizes are not artificially reduced. Growth smoke covers distances
7 and 9; an additional eight-shot full-grid check covers 7, 9, 11, 13 and 15.
Each command has a 240-second timeout; numeric thread settings are
cooperative limits. A failed command fails the suite; inspect its `.log` file.

Small samples verify execution, detector construction, decoding, postselection,
statistics and plotting. They do **not** estimate the published rare logical
error rates or verify quadratic/cubic scaling. Zero observed errors is expected.
See [validation details](docs/reproduction-audit.md).

## Experiment map

All commands below use `python -m reproduction.run EXPERIMENT --output NEW_DIR`.
Without `--smoke`, the full parameter grid is constructed, but the shot cap
still defaults to 128 per task. Choose the shot budget explicitly for production.

| Experiment | Supplement / purpose | Full grid and fixed parameters |
|---|---|---|
| `online` | D.2; Fig. 11 / main Fig. 3(a) | Six log-spaced probabilities from 10^-2.5 to 10^-3; T=1; paired before/after stages |
| `offline-error` | D.3; main Fig. 3(b), Fig. 13(a) grown | Ten probabilities 0.0001–0.001; t1=1, t2=2; output d=7 |
| `offline-t2` | Fig. 12(a) | t2=0–9; t1=1; p=0.001 |
| `offline-t1` | Fig. 12(b) | t1=1–9; t2=2; p=0.001 |
| `offline-distance` | Fig. 13(b) | second growth to d=7,9,11,13,15; p=0.001 |
| `no-grow-error` | Fig. 13(a) ungrown | Ten probabilities 0.0001–0.001; t1=1; output d=3 |
| `ts` | D.4; Fig. 14 | S and T, ten probabilities 0.001–0.01; 15-qubit state vectors |
| `offline-maintain` | Additional historical sweep | 0–9 unselected maintenance cycles |
| `no-grow-t1` | Additional historical sweep | t1=1–9 without growth |
| `online-time` | Additional historical sweep | t_round=1–9, T=10; pre-teleportation circuit only |
| `online-legacy-error` | Additional historical sweep | T=6; t_round=6,7; ten probabilities 10^-6–10^-3 |

Here t1 is `T_before_grow`, t2 is `T_ps_grow`. The initialization circuit
already includes its first syndrome cycle. `T_sc_pre` counts **additional**
cycles: 0 for the main offline error/t1/t2 sweeps, but 1 in the historical
maintenance, distance and ungrown-t1 sweeps. These differences were retained.
For `online`, t_round=T gives the pre-circuit and t_round=T+1 gives the full
teleportation circuit with one additional post-cycle. Online masks are deliberately
not applied, despite the constructors' fourth-coordinate tags.

Examples:

```bash
python -m reproduction.run offline-t2 --smoke --shots 128 --output results/t2
python -m reproduction.run online --decoder ip --smoke --shots 8 --output results/ip
python -m reproduction.run online --decoder bposd --smoke --shots 128 --output results/bposd
python -m reproduction.run ts --smoke --shots 2 --ts-mode legacy --output results/ts
python -m reproduction.run ts --smoke --shots 2 --ts-mode probability --output results/ts-corrected
python -m reproduction.plot results/t2 --output results/t2.png
```

For longer offline sampling, e.g. `--shots 10000000000 --max-errors 500 --workers 16`,
start a new output directory. Sinter's batched error stopping can slightly exceed
`--max-errors`. `--shots` counts attempts, including discards. Conditional error
rates divide by accepted shots; discard rates divide by attempts. `--p` overrides
probabilities in error sweeps and S/T runs. No automatic resume or merging is
performed: saved results are never overwritten or mixed with historical data.

Each run saves `.stim`, `.dem`, sinter `stats.csv` (or `ts.json`), and `run.json`
with arguments, package versions, commit/dirty state, source hashes, output hashes,
counts and elapsed time. Sinter 1.13 exposes no seed in this collection API;
its runs are statistically reproducible, not bitwise reproducible. `--seed`
controls the direct IP/DEM sampler and S/T trajectories only. Even seeded Stim
streams can differ across hardware/library versions or shot batching.

## Decoders and estimator conventions

- Offline: PyMatching and the existing fourth-coordinate postselection mask.
- Online: choose `--decoder pymatching`, `bposd`, or `ip`. PyMatching uses a
  decomposed DEM; BP-OSD and IP retain hyperedges. Fresh online plots subtract
  the matching pre-stage **for that run's decoder**, so an IP run uses an IP
  baseline. The published-data plot instead uses the historical MWPM baseline
  for all three curves, as in the paper.
- IP: portable SciPy/HiGHS minimum-weight **error configuration** decoding,
  preserving each undecomposed DEM mechanism. This is not degenerate logical
  maximum-likelihood decoding. Optimality and syndrome consistency are checked;
  a per-shot timeout (`--ip-timeout`, default 30 seconds) fails the run. The
  original unpinned TensorQEC/Julia loop is retained in `archive/sweep.jl`.
  We do not claim the new solver reproduces its tie breaking or published counts.
- S/T: `legacy` (default) retains the historical norm-based estimator.
  `probability` uses Born probabilities (squared norms) and weights conditional
  error estimates by acceptance probability. These are **different estimators**;
  do not replace the historical figure with corrected data without a new study.
  `trajectory_variance` is a trajectory diagnostic, not an error bar on the
  conditional mean. Plots do not use it as a confidence interval.

## Historical data and replotting

The seven existing, unmodified `data-pub/*.csv` tables are now tracked explicitly.
They contain published-figure data, not outputs of the smoke tests:

```bash
python -m reproduction.published --output results/published-replot
```

This regenerates five PNG figures (postselection, grown comparison, second growth,
online decoder comparison, historical S/T) plus input checksums. It does not
rerun simulations. Binomial tables use Wilson intervals; S/T tables have no
recorded uncertainty and receive no invented error bars. The online interval
is constructed from before/after interval endpoints. Layout is regenerated;
this is not a pixel-identical copy of the paper's figures.

## Code layout and historical entry points

- `reproduction/`: common CLI, experiment grids, IP decoder, fresh/historical plots.
- `data_collection/src/`, `no_grow/src/`, `online/src/`: original circuit
  constructors with package-relative imports; distinct circuit variants retained.
- `TS/qrm_state.py`: original state-vector implementation plus explicit estimator
  mode and RNG support.
- `checks/`: bounded suite, invariants, original-circuit comparison.
- `archive/`: early circuit designs, exploratory checks and unmaintained decoders.
  These are historical records and are explicitly excluded from reproduction.
- Existing notebooks and PDFs are historical interactive records. They may refer
  to local untracked output files; the supported workflow does not execute them.

The five `data_collection/sweep_*` scripts, two `no_grow/sweep_*` scripts and two
`online/sweep_*` scripts now delegate to the common runner. Their direct paths
work from any working directory and accept `--help`, `--smoke`, `--shots`,
`--workers`, and required `--output`. `online/ip_decoder/sweept1.py` now runs the
paired T=1 benchmark; `dem_gen.py` and `sweep_dem.py` both generate and decode
consistently named online DEMs (or use `--input existing.dem`). This replaces the
old mismatched T1/T2/T7 filenames and floating-point filename formatting.

For a source-preservation check against the pre-organization commit:

```bash
python -m checks.compare_circuits
```

This needs Git history containing `d816424`. It compares all 18 smoke circuits,
not merely their logical outputs. Default reproduction needs no historical Git
checkout. No remote push is part of this organization.
