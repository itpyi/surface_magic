# Data for the published figures

These tables contain the numerical data used in Figs. 3 and 11–14 of
*Non-Clifford quantum gate teleportation with generalized lattice surgery*,
Physical Review A 113, 062410 (2026). Figure numbers are encoded in the filenames.

| File | Quantity | Format |
|---|---|---|
| `fig3a&11.csv` | Online full-circuit IP, MWPM and BP-OSD counts, with the MWPM pre-teleportation baseline | One row per physical error probability |
| `fig3b&13a_grown.csv` | Offline physical-error sweep with output distance 7 | Sinter statistics, 10 rows |
| `fig12a.csv` | Postselected rounds after growth | Sinter statistics, 10 rows |
| `fig12b.csv` | Postselected rounds before growth | Sinter statistics, 9 rows |
| `fig13a_ungrown.csv` | Offline physical-error sweep with output distance 3 | Sinter statistics, 10 rows |
| `fig13b.csv` | Further growth to larger distances | Sinter statistics, 5 rows |
| `fig14.csv` | S/T comparison in the isolated noise model | Original rounded estimates |

From the repository directory, run:

```bash
python -m reproduction.published --output results/paper-figures
```

In the sinter tables, `shots` counts all attempts, `discards` counts rejected
attempts, and `errors` counts logical failures among the accepted attempts.
Thus the conditional logical error rate is `errors / (shots - discards)`.
`json_metadata` identifies the scanned parameter. The online table contains
separate shot and error columns for each decoder and for the baseline.

The 44 sinter rows also contain task identifiers. To check that they match the
circuit, detector error model, postselection mask, decoder and metadata used by
the supplied code, run `python -m checks.published_ids`. Matching identifiers
establish agreement of the task definitions for these 44 rows.

In `fig14.csv`, `err_phy` is the physical error probability, `T_ps` and `S_ps`
are the original discard estimates, and `T_err` and `S_err` are the original
conditional logical-error estimates. These values are retained for reproducing
the published figure. They use the original norm-based estimator; see the
[correction note](../README.md#note-on-the-st-comparison-in-fig-14) and
[corrected calculation](../docs/st-ordering-audit.md). The table provides point estimates.
