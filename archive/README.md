# Historical experiments

These files are preserved for provenance, not supported reproduction entry points.
They include early circuit designs, exploratory circuit checks, and an unused
Python hypergraph decoder (incomplete sinter interface, unsafe solver fallback).
`sweep.jl` is the original TensorQEC IP loop. No Julia Project/Manifest was
committed; it has hardcoded filenames and an unbounded error-count stopping rule.
The maintained, bounded IP path is `python -m reproduction.run online --decoder ip`.
This uses SciPy/HiGHS minimum-weight error configurations on the undecomposed DEM;
solver version and tie breaking differ from the original TensorQEC implementation.
Nothing in this archive has been certified by the smoke suite.

Old notebooks elsewhere are likewise historical interactive records, not CLI
entry points. Prefer the documented reproduction modules. Git history at d816424
preserves original locations and code before organization.
