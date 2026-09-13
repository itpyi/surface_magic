# Bounded reproduction evidence

The corrected suite completed all **35 commands** in **157.73 seconds** on the
recorded macOS arm64 environment. All five invariant tests passed. Each of the
five second-growth distances received exactly eight attempts (40 total).
The v2 manifest passed structural validation and current-source/output hash
validation. These are execution results, not published-rate estimates.

- `contract.json`: finite assertion, numerical conventions, exact declared source
  inputs, software versions, sampling budgets and non-claims.
- `reference.json`: SHA-256 of the user-designated Overleaf supplemental source.
- `circuit-comparison.txt`: output of `python -m checks.compare_circuits`;
  all 18 smoke circuits match the pre-organization `d816424` sources.
- `verified/manifest.json`: final computation-audit v2 execution manifest.
- `verified/evidence.json`: exact command list, individual run provenance, raw
  sinter CSV/TS/DEM results, and logs for the successful bounded suite.
- `final/manifest.json`: earlier failed attempt. It caught the sinter 1.13 default
  initial batch overshooting an eight-shot limit. The fix is committed as
  `85e6afb`; historical failure records intentionally refer to earlier inputs.

The successful manifest pins the computation source revision and hashes. Later
commits adding this evidence or documentation do not alter that tested source.
`verified/evidence.json` embeds raw finite statistics, not only a pass label.
Large regenerated circuit/DEM dumps and rendered PNGs remain under ignored
`results/verified-smoke/`; their hashes are in the individual run JSON records.

Reproduce with a new output directory:

```bash
python -m checks.smoke --output results/recheck --evidence results/recheck-evidence.json
```

The optional v2 manifest was recorded and validated using the installed
`mathbox:computation-audit` skill's `run_experiment.py` and `validate_manifest.py`.
Those helpers are not required to run this repository. The manifest itself
records the exact simulation invocation, source inputs, resource limits, timestamps
and output checksum. The failed manifest remains structurally valid evidence of
failure, but its input hashes naturally differ after applying the fix; use the
successful manifest for current-source validation.
