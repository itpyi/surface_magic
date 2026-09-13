# Non-Clifford quantum gate teleportation with generalized lattice surgery

Numerical simulations for Yifei Wang and Yingfei Gu, **Physical Review A 113,
062410 (2026)** ([preprint](https://arxiv.org/abs/2503.19758)). This repository
contains the circuit simulations described in Appendix D, the data used in
Figs. 3 and 11–14, and commands for repeating the numerical experiments.

The online protocol teleports a gate from the 15-qubit QRM code to a distance-3
surface code. The offline protocol adds postselection and surface-code growth.
Both protocols are simulated in the Clifford regime using S in place of T.
The separate S/T comparison and a correction to its probability estimates are
explained in the final section below.

## Installation

Use **Python 3.11**. Run the following commands from the repository directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

Alternatively, create the supplied Conda environment:

```bash
conda env create -f environment.yml
conda activate magic-reproduction
```

The dependencies include Stim 1.15.0, **sinter 1.13.0**, PyMatching 2.3.0 and
NumPy 1.26.4. Keep the specified sinter version: later versions tested with this
code had a postselection error. See the
[postselection discussion](https://quantumcomputing.stackexchange.com/questions/44364/how-to-use-sinter-to-collect-stats-with-postselection/44479#44479).
The supplied environment has been tested on macOS with Apple silicon.

All remaining commands assume that the environment is activated and that the
working directory is this repository. Use a new output directory for each run.

## Replot the paper's data

The tables in [`data-pub/`](data-pub/README.md) contain the data used for the
published figures. To plot them without repeating the simulations:

```bash
python -m reproduction.published --output results/paper-figures
```

This produces five PNG files: `postselection.png`, `grown-comparison.png`,
`distance.png`, `online-decoders.png`, and `ts-historical.png`. They cover the
postselection sweeps, growth comparisons, online decoder comparison and S/T
comparison. The plots use the original tables with a layout adapted for this repository. In particular, `ts-historical.png` retains the original
Fig. 14 values; see the correction note below.

## Run the simulations

For a small-sample check of the simulation and plotting workflows:

```bash
python -m checks.smoke --output results/small-run
```

This uses 128 attempted shots per ordinary circuit task, eight per IP/DEM task,
and two trajectories per S/T gate and parameter point. It also checks growth
through distances 7, 9, 11, 13 and 15 with eight shots each. These small samples
check that the calculations run. Resolving the rare logical errors and scaling
exponents reported in the paper requires much larger samples; a small run will
often record zero logical errors.

To select an experiment, use `python -m reproduction.run` with one of the names
below. Figure and section references follow the published article.

| Experiment | Physical quantity or comparison | Paper |
|---|---|---|
| `online` | Logical error before and after gate teleportation; choose IP, MWPM or BP-OSD | Fig. 3(a), Fig. 11; Appendix D.2 |
| `offline-error` | Error and discard rates after preparation of a distance-7 state | Fig. 3(b), grown curve in Fig. 13(a) |
| `offline-t2` | Postselected rounds after growth, with t1 fixed at 1 | Fig. 12(a) |
| `offline-t1` | Postselected rounds before growth, with t2 fixed at 2 | Fig. 12(b) |
| `no-grow-error` | Preparation without growth, ending at distance 3 | Ungrown curve in Fig. 13(a) |
| `offline-distance` | Further growth from distance 7 to 7, 9, 11, 13 or 15 | Fig. 13(b) |
| `ts` | S/T comparison for the isolated noise source | Fig. 14; Appendix D.4 |

For example, sample the postselection sweep and plot the result:

```bash
python -m reproduction.run offline-t2 --smoke --shots 128 --output results/t2
python -m reproduction.plot results/t2 --output results/t2.png
```

For the online protocol, select a decoder explicitly:

```bash
python -m reproduction.run online --decoder ip --smoke --shots 8 --output results/online-ip
python -m reproduction.run online --decoder pymatching --smoke --shots 128 --output results/online-mwpm
python -m reproduction.run online --decoder bposd --smoke --shots 128 --output results/online-bposd
python -m reproduction.plot results/online-ip results/online-mwpm results/online-bposd --output results/online-comparison.png
```

The online error contribution is the difference between the full-circuit and
pre-teleportation error rates. For newly sampled data, the plotting command uses
the same decoder for both stages of each curve. The published comparison instead
uses a MWPM pre-teleportation baseline for all three decoders, as described in
Appendix D.2; the command for replotting the paper's data preserves that choice.

The supplied IP implementation uses SciPy/HiGHS to minimize the negative
log-likelihood of an error configuration in the undecomposed detector error
model. The published IP data were obtained with TensorQEC. Different solver
tie-breaking can give different predictions for equally weighted corrections.


### Sampling enough shots

`--smoke` selects a reduced parameter grid. Omit it to use the full grid, and
set `--shots` explicitly: the default remains 128 attempts per task. For example,
a longer offline physical-error sweep is:

```bash
python -m reproduction.run offline-error --shots 10000000000 --max-errors 500 --workers 16 --output results/offline-long
```

This is a substantial calculation. It stops each task at its shot limit or
logical-error target; batched sampling can slightly exceed the error target.
`--shots` includes discarded attempts. `--workers` controls the number of
sampling processes. Error sweeps also accept `--p`, followed by one or more
physical error probabilities. The complete grids, round conventions and
additional parameter sweeps are listed in [Experiment parameters](docs/experiments.md).

## Reading the results and finding the code

A circuit run saves `stats.csv`, the sampled circuits (`.stim`), their detector
error models (`.dem`), and `run.json` with the parameters and software versions.
S/T runs save `ts.json` instead of a shot-count table. All outputs are placed in
the directory specified by `--output`.

In `stats.csv`, the logical error rate is `errors / (shots - discards)` and the
discard rate is `discards / shots`. The supplied plots use Wilson intervals for
binomial counts. A run with no accepted shots cannot estimate a conditional
logical error rate. Online differences can be negative within sampling noise.

Sinter collection uses stochastic sampling, so repeated runs give statistically
varying counts. `--seed` controls direct IP/DEM sampling and S/T trajectories.
The S/T variance fields describe variation among trajectories.

The files are grouped by their role in the calculation:

```text
reproduction/         Commands for sampling and plotting
  experiments.py      Parameter grids for the experiments
  ip.py               Integer-programming decoder

data-pub/             Tables used in the published figures
docs/                 Experiment parameters and the S/T derivation

data_collection/src/  Offline protocol with surface-code growth
no_grow/src/          Offline protocol ending at distance 3
online/src/           Online gate-teleportation protocol
TS/qrm_state.py       S/T state-vector calculation

checks/               Small-sample checks and exact S/T calculation
validation/           Saved small-sample results and exact S/T certificate
results/              Outputs created by the commands above
```

The `sweep_*` directories alongside the circuit modules provide individual
experiment scripts; the commands above give a common way to run them.
The published tables include 44 offline task
identifiers that can be checked against the circuit definitions with
`python -m checks.published_ids`.

## Note on the S/T comparison in Fig. 14

The original S/T state-vector calculation used the norm of a projected state
where a probability requires its **squared norm**. It also averaged conditional
error estimates over noise trajectories without weighting them by their
acceptance probabilities. This affects the numerical values in Fig. 14 and
the corresponding auxiliary estimates in Appendix D.4. The separately computed online and offline
full-circuit statistics in the other figures remain unchanged.

For the isolated 15-qubit noise model used in Fig. 14, an exact calculation with
the corrected probabilities preserves both the S/T ordering and the
order-of-magnitude comparison discussed in the article. At physical error
probability 0.001, the corrected S-minus-T logical-error difference is about
3.07e-8, and the discard difference is about 0.00742 (the text quotes approximately
0.004). These differences remain small relative to the
full-protocol rates used in that comparison. The derivation, assumptions and
interval-wide ordering proof are given in [S/T probability estimates](docs/st-ordering-audit.md).
The S/T substitution in the complete teleportation protocol remains supported
by the model comparison described in Appendix D.4.

The repository retains the original tables and provides two explicit modes:
`legacy` (the default) evaluates the original estimator, while `probability`
uses squared norms and acceptance-weighted averaging. To sample the corrected
model, or to evaluate its probabilities exactly without random sampling:

```bash
python -m reproduction.run ts --ts-mode probability --smoke --shots 100 --output results/ts-corrected
python -m checks.st_ordering_audit --statevector-check --output results/ts-exact.json
```
