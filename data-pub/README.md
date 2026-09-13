# Historical publication tables

These seven files already existed locally before the reproducibility cleanup.
They have been added to Git without changing their contents. They are historical
inputs, not measurements produced or independently re-sampled by the new suite.
Figure numbers follow the existing publication filenames.

| File | Figure / meaning | Provenance available |
|---|---|---|
| `fig3a&11.csv` | Online full-circuit IP/MWPM/BP-OSD and MWPM baseline counts | Same counts embedded in `plot/plot.ipynb`; no task IDs/seeds |
| `fig3b&13a_grown.csv` | Offline grown physical-error sweep | 10 sinter task IDs |
| `fig12a.csv` | Postselected rounds after growth | 10 sinter task IDs |
| `fig12b.csv` | Postselected rounds before growth | 9 sinter task IDs |
| `fig13a_ungrown.csv` | Ungrown physical-error sweep | 10 sinter task IDs |
| `fig13b.csv` | Second growth to larger distances | 5 sinter task IDs |
| `fig14.csv` | S/T state-vector comparison | Rounded historical estimates, no trajectory seeds/counts |

Run `python -m checks.published_ids` to reproduce all 44 offline strong IDs
using historical metadata. The constructor output must pass through Stim text
serialization before computing the DEM, matching the original sinter 1.13 worker
path. This matters at the floating-point representation level for four
probabilities in each error sweep. It does not change the intended noise model.
New run metadata is more complete, so new tasks intentionally have different IDs.
An ID match authenticates the circuit/DEM/mask/decoder/metadata combination;
it does not independently validate the accumulated error counts.

S/T values retain the historical norm-based convention. See the estimator caveat
in the main README; no correction has been applied to these tables.
