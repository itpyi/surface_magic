# Non-Clifford quantum gate teleportation with generalized lattice surgery

Numerical simulations for Yifei Wang and Yingfei Gu, [**Physical Review A 113,
062410 (2026)**](https://journals.aps.org/pra/abstract/10.1103/1xq4-856m)
(also see [preprint](https://arxiv.org/abs/2503.19758)). This repository
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

The data used for the published figures are available on
[Zenodo (DOI: 10.5281/zenodo.20019943)](https://doi.org/10.5281/zenodo.20019943).
Copies of these tables are included in [`published_data/`](published_data/README.md).
To plot them without repeating the simulations:

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
simulations/                     Physical models and circuit construction
  offline/
    with_growth/                 Postselected preparation and code growth
      preparation.py             Preparation through the first growth stage
      further_growth.py          Further growth to larger code distances
    without_growth/              Postselected preparation at distance 3
      preparation.py
  online/
    teleportation.py             Online gate teleportation and its baseline
  st_comparison/
    statevector.py               Isolated S/T noise model

reproduction/                    Commands for running and plotting experiments
  experiments.py                 Parameter grids and circuit selection
  ip.py                          Integer-programming decoder
  dem.py                         Direct detector-model sampling

published_data/                  Tables used in the published figures
docs/                            Experiment parameters and S/T analysis
checks/                          Small-sample checks and exact S/T calculation
validation/                      Saved check results and S/T certificate
results/                         Outputs created by the commands above
```

Each circuit package contains `qrm_code.py`, `surface_code.py` and
`lattice_surgery.py` for its QRM checks, surface-code operations and surgery
sequence. The `build_circuit` functions assemble these components into the
protocols selected by `reproduction.experiments`.

The published tables include 44 offline task identifiers that can be checked
against the circuit definitions with `python -m checks.published_ids`.

## Acknowledgments

This repository was organized and its reproducibility checks were carried out
with assistance from OpenAI’s GPT-6 Astra.

## Note on the S/T comparison in Fig. 14

While organizing the code, we identified a minor error in the S/T comparison
in Appendix D.4 (Fig. 14) of the supplementary material. The calculation used
norms instead of squared norms and averaged noise trajectories without the
appropriate acceptance weights. Correcting these estimates preserves the S/T
ordering of both logical-error and discard probabilities, as well as the
order-of-magnitude comparisons used in the argument. The paper's core
conclusions therefore remain unchanged. See the
[detailed analysis](docs/st-ordering-audit.md) for the derivation and corrected
estimates.
