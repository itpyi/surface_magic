"""Compare the 44 published offline task identifiers with the supplied circuits."""
import sinter
import stim
from reproduction.experiments import cases
from reproduction.run import ROOT

MAPPING = [
    ('fig3b&13a_grown.csv', 'offline-error', 'p', 'error_rate'),
    ('fig12a.csv', 'offline-t2', 'T_PS_GROW', 'T_ps_grow'),
    ('fig12b.csv', 'offline-t1', 'T_BEFORE_GROW', 'T_before_grow'),
    ('fig13b.csv', 'offline-distance', 'd', 'd2'),
    ('fig13a_ungrown.csv', 'no-grow-error', 'p', 'error_rate'),
]

def main():
    total = 0
    for filename, experiment, old_key, new_key in MAPPING:
        rows = sinter.read_stats_from_csv_files(ROOT/'data-pub'/filename)
        for row in rows:
            value = row.json_metadata[old_key]
            grid = cases(experiment, probabilities=[value]) if old_key == 'p' else cases(experiment)
            case = next(c for c in grid if abs(c.metadata[new_key]-value) < 1e-14)
            # Original sinter collection serialized the circuit before DEM creation.
            circuit = stim.Circuit(str(case.circuit))
            task = sinter.Task(circuit=circuit, decoder='pymatching',
                detector_error_model=circuit.detector_error_model(decompose_errors=True),
                postselection_mask=sinter.post_selection_mask_from_4th_coord(circuit),
                json_metadata=row.json_metadata)
            if task.strong_id() != row.strong_id:
                raise AssertionError((filename, row.json_metadata, task.strong_id(), row.strong_id))
            total += 1
        print(f'PASS: {filename}: {len(rows)} strong IDs')
    print(f'PASS: all {total} published offline task IDs match the supplied task definitions.')

if __name__ == '__main__':
    main()
