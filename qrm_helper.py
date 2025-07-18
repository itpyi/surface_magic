import stim

def add_detectors_between_measurements(circuit: stim.Circuit, qubits_to_detect: list[int]):
    """
    Adds DETECTOR instructions to the circuit for specified qubits,
    comparing their first measurement result with their second.

    This function assumes:
    1. For each qubit in `qubits_to_detect`, there are exactly two
       measurements (`M` or `MR`) performed on it within the circuit.
    2. The detectors are to be appended *after* all existing operations
       in the circuit.

    Args:
        circuit: The Stim circuit object to modify.
        qubits_to_detect: A list of qubit indices (e.g., [0, 1, 2]) for
                          which to add comparison detectors.
    """

    # Get all measurement results in the circuit, ordered chronologically.
    # Each item is (record_index, qubit_index).
    # record_index is the absolute position in the flat list of all measurement results.
    all_measurements = circuit.measurements()

    # Dictionary to store the first and second measurement record index for each qubit
    first_meas_record_idx = {}  # {qubit_index: record_index_of_first_measurement}
    second_meas_record_idx = {} # {qubit_index: record_index_of_second_measurement}
    
    # Temporarily track how many times each qubit has been measured
    qubit_meas_count = {q: 0 for q in qubits_to_detect}

    for record_idx, q_idx in all_measurements:
        if q_idx in qubits_to_detect:
            qubit_meas_count[q_idx] += 1
            if qubit_meas_count[q_idx] == 1:
                first_meas_record_idx[q_idx] = record_idx
            elif qubit_meas_count[q_idx] == 2:
                second_meas_record_idx[q_idx] = record_idx
            # If a qubit is measured more than twice, we only consider the first two.

    # Validate that all target qubits have exactly two measurements recorded
    for q in qubits_to_detect:
        if q not in first_meas_record_idx or q not in second_meas_record_idx:
            raise ValueError(
                f"Qubit {q} does not have exactly two measurements "
                "recorded in the provided circuit's measurement operations."
            )

    # Total number of measurements in the circuit *before* adding the detectors.
    total_measurements_so_far = len(all_measurements)

    # Now, append a DETECTOR for each specified qubit
    for q_idx in qubits_to_detect:
        # Get the absolute record indices for the two measurements of this qubit
        abs_idx1 = first_meas_record_idx[q_idx]
        abs_idx2 = second_meas_record_idx[q_idx]

        # Convert absolute indices to relative indices for `stim.target_rec()`
        # `stim.target_rec(-k)` refers to the k-th measurement result counting backwards
        # from the end of the current measurement record.
        # So, if total_measurements_so_far = N, and an absolute index is `abs_idx`,
        # its relative index is `-(N - abs_idx)`.
        
        rel_idx1 = -(total_measurements_so_far - abs_idx1)
        rel_idx2 = -(total_measurements_so_far - abs_idx2)
        
        # Append the DETECTOR instruction
        # A DETECTOR with two targets implies it's comparing their results.
        # You can also add coordinates to the DETECTOR if you wish, e.g.,
        # for a specific (x, y, z) location for the detector itself.
        # For simplicity, we just add it to the end of the circuit with no explicit coords.
        circuit.append("DETECTOR", [], [stim.target_rec(rel_idx1), stim.target_rec(rel_idx2)])

        # Optional: Add a COORDINATE to the detector for visualization in 3D.
        # For example, placing it at the qubit's X/Y coord, and a 'time' Z-coord.
        # This requires the qubits to have been assigned QUBIT_COORDS earlier.
        # If QUBIT_COORDS were (x_q, y_q) for q_idx:
        # try:
        #     q_x, q_y = circuit.get_final_qubit_coords(q_idx)
        #     circuit.append("DETECTOR", [], [stim.target_rec(rel_idx1), stim.target_rec(rel_idx2)],
        #                    coords=[q_x, q_y, 0.5]) # Z=0.5 could be an arbitrary 'time' midway
        # except ValueError: # get_final_qubit_coords might fail if no coords set
        #     pass # Fallback to no coords if not set