# Saved verification results

The small-sample suite completed all **35 commands** in **157.26 seconds** on
macOS with Apple silicon, using the pinned Python environment. It covered
simulation, decoding and plotting, and all five circuit-invariant tests passed.
Ordinary circuit tasks used 128 attempted shots, IP/DEM tasks used eight, and
S/T calculations used two trajectories per gate and probability. The additional
code-growth check used eight attempts at each distance 7, 9, 11, 13 and 15.
These sample sizes verify that each calculation runs. Estimating the rare logical
error rates in the article requires larger samples.

[`smoke-results.json`](smoke-results.json) is a portable summary of that recorded
run. It includes the 35 commands, exit codes, timings and numerical outputs.
Per-run records contain the parameters, package versions and source checksums.
Paths are expressed relative to the repository directory. Generated circuit,
detector-model and plot files can be recreated by running the suite:

```bash
python -m checks.smoke --output results/recheck --evidence results/recheck-evidence.json
```

The [published-data check](../data-pub/README.md) additionally compares the
44 saved offline task identifiers with the supplied circuit definitions.

## Exact S/T probabilities

[`st-ordering/result.json`](st-ordering/result.json) contains exact probability
polynomials, the positive Bernstein coefficients establishing the S/T ordering,
and evaluations at the ten physical error probabilities used in Fig. 14.
The calculation enumerates all 32768 physical X-error patterns. Sixteen patterns
are also checked with the full state-vector implementation to absolute tolerance
10^-12. Recreate the result with:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m checks.st_ordering_audit --statevector-check --output results/st-ordering.json
```

See the [derivation and interpretation](../docs/st-ordering-audit.md) for the
model assumptions and the correction to the original probability estimates.
