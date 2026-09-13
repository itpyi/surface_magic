# Experiment parameters

These parameters specify the numerical experiments in Appendix D of
*Non-Clifford quantum gate teleportation with generalized lattice surgery*,
Physical Review A 113, 062410 (2026). All commands are run from the repository
directory after activating the environment described in the [README](../README.md).

## Online gate teleportation

`python -m reproduction.run online --decoder ip --output results/online`
constructs both the pre-teleportation circuit and the full circuit. Choose
`pymatching`, `bposd` or `ip` for MWPM, BP-OSD or integer-programming decoding.
All attempted shots are retained in this experiment. The full probability grid contains
six logarithmically spaced points from 10^-2.5 to 10^-3.

The surface-code initialization includes its first syndrome round. The parameter
`T=1` adds one further round before teleportation. The `before` circuit ends with
an X-logical readout; the `after` circuit includes three rounds of lattice
surgery, QRM readout, one additional surface-code round and ideal logical Y
readout, as described in Appendix D.2. The circuit argument `t_round` is 1 for
`before` and 2 for `after`.

Each run records the two stages separately. The published comparison subtracts
a MWPM estimate for the pre-teleportation stage from each full-circuit estimate.
`reproduction.published` uses those published counts. `reproduction.plot` applied
to a newly sampled run uses that run's decoder for both stages.

MWPM uses a graph-like decomposition of the detector error model. BP-OSD and
IP retain its higher-order detector correlations. The supplied IP solver requires
an optimal minimum-weight error configuration and checks its syndrome. It stops
with an error if optimality is not established within `--ip-timeout` seconds
per shot (default 30). The decoder optimizes the probability of an individual error configuration.

## Offline preparation and code growth

The fixed physical error probability in the round and distance sweeps is 0.001.
The QRM state is teleported to a distance-3 surface code using three lattice-surgery
rounds. Except for `no-grow-error`, the state is then grown to distance 7.
The round variables in Fig. 12 correspond to:

| Article notation | Circuit argument | Meaning |
|---|---|---|
| t1 | `T_before_grow` | Postselected rounds before growth |
| t2 | `T_ps_grow` | Postselected rounds after the growth round |
| — | `T_sc_pre` | Additional initial surface-code rounds after initialization |
| — | `T_maintain` | Unselected rounds after postselection ends |

| Experiment | Full scan | Other parameters |
|---|---|---|
| `offline-error` | Ten equally spaced probabilities from 0.0001 to 0.001 | t1=1, t2=2, `T_sc_pre=0`, `T_maintain=0`, distance 7 |
| `offline-t1` | t1=1,…,9 | t2=2, `T_sc_pre=0`, `T_maintain=0`, distance 7 |
| `offline-t2` | t2=0,…,9 | t1=1, `T_sc_pre=0`, `T_maintain=0`, distance 7 |
| `no-grow-error` | Ten equally spaced probabilities from 0.0001 to 0.001 | t1=1, `T_sc_pre=0`, distance 3 |
| `offline-distance` | Final distances 7, 9, 11, 13, 15 | t1=1, t2=2, `T_sc_pre=1`, `T_maintain=0` before the second growth |

The distance sweep includes an extra initial surface-code round compared with
the physical-error and t1/t2 sweeps. This is part of the circuit used for the
Fig. 13(b) data. All shots surviving the first growth stage are retained during further growth.
Logical Y readout and the final syndrome round are ideal, as in the article.

All these experiments use MWPM by default. A detector's fourth coordinate marks
whether it is included in postselection. Shots are discarded when a marked
detector fires; the reported logical-error frequency is conditional on acceptance.

## S/T comparison

`ts` uses the 15-qubit state-vector model of Appendix D.4, with independent
X noise between mutually inverse transversal gate layers. The full grid has ten
physical error probabilities from 0.001 to 0.01. Both S and T are evaluated at
each point. Here `--shots` is the number of random-rotation trajectories, rather
than a number of sampled binary measurement outcomes.

`--ts-mode legacy` retains the original estimator; `--ts-mode probability` uses
the corrected probabilities. The distinction and its effect on Fig. 14 are
explained in the final section of the [README](../README.md#note-on-the-st-comparison-in-fig-14).
The [exact derivation](st-ordering-audit.md) also provides a calculation without
random sampling.

## Sampling controls

The default limit is 128 attempted shots **per circuit and decoder**, including
discarded attempts. Set `--shots` to increase it and `--workers` to choose the
number of sinter sampling processes. `--max-errors` sets an additional stopping
target for logical errors. Sinter collects batches, so the error target can be
slightly exceeded. Direct IP sampling is sequential; `--workers` controls sinter collection.

For `online`, `offline-error`, `no-grow-error`, `online-legacy-error` and `ts`,
`--p` replaces the default physical-error grid. For example:

```bash
python -m reproduction.run offline-error --p 0.0005 0.001 --shots 1000 --output results/two-probabilities
```

`--smoke` uses a small selection of the same circuits: one physical probability
(0.001), t1 values 1 and 2, t2 values 0 and 2, or final distances 7 and 9,
as appropriate. The separate full-distance check in `checks.smoke` also tests
11, 13 and 15. Circuit geometry is retained while the sample counts are reduced.

## Additional scans

These commands explore variations of the protocols beyond the figure-producing
scans above:

| Experiment | Scan and fixed parameters |
|---|---|
| `offline-maintain` | 0–9 unselected maintenance rounds; t1=1, t2=2, `T_sc_pre=1`, p=0.001 |
| `no-grow-t1` | t1=1–9 without growth; `T_sc_pre=1`, p=0.001 |
| `online-time` | `t_round=1–9`, `T=10`, p=0.001; all circuits end before teleportation |
| `online-legacy-error` | `T=6`, before/after at `t_round=6,7`; ten log-spaced probabilities from 10^-6 to 10^-3 |

Their names are accepted by the same `reproduction.run` command.
