# Reproduction contract and audit

Reference: the author's `67e2bd967ff14df0f46f7620/supp.tex`, Supplement D;
publication PRA 113(6), 062410. Pre-organization numerics commit: `d816424`.

The finite assertion is that maintained simulation entry points construct the
intended circuit families, sample bounded workloads, apply the specified decoder
and postselection, save valid statistics, and replot their outputs. Arithmetic
is GF(2) for syndromes/observables, IEEE float64 for noise probabilities and
optimization weights, and complex128 for 15-qubit S/T state vectors. The noise
placement, gate sequence, qubit indexing, flag/meta-check logic and readout
conventions are preserved from the original constructors.

## Checks and their interpretation

- `checks.compare_circuits`: all 18 smoke-grid circuits match the text emitted by
  the original `d816424` constructors. This checks exact gate/measurement ordering,
  not merely the ideal logical action. Requires the old commit in local Git.
- Noiseless variants: detector models compile and 32 seeded samples per circuit
  have no detector events or observable flips. This is a finite consistency test.
- `checks.published_ids`: all 44 offline historical sinter task IDs are recreated.
  Stim text roundtripping before DEM construction reproduces the original
  sinter-worker floating-point normalization. Online count tables and S/T rounded
  tables have no task IDs, so no equivalent authentication is possible.
- IP: all eight syndromes of an independent, four-mechanism toy hypergraph are
  compared to exhaustive enumeration. The test also checks parity cancellation
  across separator components, and verifies that solver timeout raises an error.
  Real online smoke runs exercise both pre- and post-teleportation hypergraphs.
- S/T: normalized ideal QRM states and zero noise; a known 25% rejected component;
  a known 25% logical-error component; and explicit acceptance-weighted averaging.
  The legacy estimator returns `1-sqrt(0.75)` for the 25% rejection example, while
  the Born-probability mode returns 0.25. The original estimator remains default
  to prevent silently changing the interpretation of the published S/T figure.
- End-to-end suite: historical wrapper paths and new canonical paths, 128 attempted
  shots per ordinary smoke task, 8 per IP/DEM task, two S/T trajectories per gate
  and estimator mode; 8 attempts at each second-growth distance 7,9,11,13,15.
  Each online run includes before and after. Stats satisfy count bounds.
  Postselection runs contain both accepted and discarded samples in the recorded
  validation. Fresh plots handle zero errors with Wilson intervals, without
  fitting under-resolved scaling laws. Historical-data plots do not mix new data.

Sinter 1.13 defaults to a 100-shot initial batch even when the requested cap is
smaller. The maintained runner explicitly bounds its initial and maximum batch
sizes; the eight-shot full-distance test checks this regression. The first
final-suite attempt detected this overshoot and is retained as failed evidence
in `validation/final/`; successful corrected evidence is in `validation/verified/`.

Each script has a 240-second smoke-suite timeout, one sinter worker, and cooperative
one-thread settings for standard numeric runtimes. IP has a 30-second timeout per
shot and requires proven solver optimality. Production workloads are explicitly
chosen by command-line shot/error caps; the smoke suite never launches the
historical billion-shot jobs. Seeded direct DEM/IP and S/T paths record their seeds;
sinter 1.13's collection path remains unseeded. Failed and successful execution
are distinguished in run JSON and suite logs.

## Deliberate changes and limits

The original fixed-budget sweep files are now compatibility entry points. Circuit
variants are kept separate and import relatively to avoid the competing `src`
packages. Generated outputs require a new directory. Existing data is preserved.
Exploratory scripts, early circuit designs, and the unused/incomplete hypergraph
wrapper are retained under `archive/`, and are not advertised as certified runs.
Historical notebooks are not fresh-run dependencies.

The unpinned Julia/TensorQEC IP loop was replaced in the maintained workflow by a
SciPy/HiGHS implementation of minimum-weight error-configuration decoding on the
undecomposed DEM. It is a solver substitution, not a reconstruction of the exact
historical Julia environment. Logical degeneracy and solver tie-breaking can
change predictions even with the same optimal weight. Exhaustive toy checks and
small real-circuit runs cannot establish bitwise equivalence to the historical
IP implementation. The old loop is retained unchanged in `archive/sweep.jl`.

S/T has a substantive estimator defect in its historical code: norms were used
instead of squared norms, and conditional errors were averaged without acceptance
weights. Both are corrected only in the explicit `probability` mode. This audit
has not recomputed the scientific conclusions of D.4 under that mode. Historical
S/T values and plots are labeled accordingly. The recorded trajectory variance
is not a confidence interval for the conditional estimator.

Small samples establish execution and stated finite invariants only. They do not
reproduce the published logical rates, uncertainty, scaling exponents, or the
claimed circuit distance. Historical task-ID matches establish input provenance,
not an independent validation of large-run statistics. No universal fault-tolerance
claim follows from this run.

## Evidence

See `validation/` for the final bounded-run manifest, logs, suite command list and
checksummed finite outputs. Large circuit/DEM dumps can be regenerated by the
commands in the main README; per-run JSON also records their hashes. The local
`results/` directory contains complete working outputs and is ignored by Git.
