#!/usr/bin/env bash
set -euo pipefail

# Where to store results
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="results/$STAMP"
mkdir -p "$OUT_DIR"

# Edit these lists to your needs
circuits=(circuits/qrm_flag_nogate_0.00032.stim circuits/qrm_flag_nogate_0.00046.stim circuits/qrm_flag_nogate_0.00068.stim circuits/qrm_flag_nogate_0.00100.stim circuits/qrm_flag_nogate_0.00147.stim circuits/qrm_flag_nogate_0.00215.stim circuits/qrm_flag_nogate_0.00316.stim circuits/qrm_flag_nogate_0.00464.stim circuits/qrm_flag_nogate_0.00681.stim circuits/qrm_flag_nogate_0.01000.stim)
params=(0.00031622776601683794 0.00046415888336127773 0.0006812920690579615 0.001 0.0014677992676220691 0.002154434690031882 0.0031622776601683794 0.004641588833612777 0.006812920690579608 0.01)
shots=10000000  # example; replace with your real flag(s)

# Main sweep
for c in "${circuits[@]}"; do
  base="$(basename "${c%.*}")"
  for p in "${params[@]}"; do
    out="$OUT_DIR/${base}_p${p}.csv"
    echo "Running $c p=$p -> $out"
    # Replace the command below with your actual sinter CLI invocation and flags.
    # Keep using the CLI; we are not using the Python API.
    sinter collect \
      --circuit $c \
      --processes 16 \
      --max_shots "$shots" \
      --decoders pymatching \
      --postselected_detectors_predicate "index >= 0" \
      # add your usual flags to control noise/decoder/etc, using $p where appropriate
  done
done

# Optional: combine CSVs (assuming identical header)
{
  head -n1 "$OUT_DIR"/*.csv | head -n1
  tail -n +2 -q "$OUT_DIR"/*.csv
} > "$OUT_DIR/all.csv"

echo "Done. Results in $OUT_DIR"