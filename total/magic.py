import surface_code as sc
import qrm
import stim
import numpy as np

def magic_preparation(T_sc_pre, T_lat_surg, T_before_grow, T_ps_grow, T_maintain, error_rate):
    """
    Args:
        T_sc_pre: number of rounds of surface code stabilizer measurements during the initial preparation stage
        T_lat_surg: number of rounds of linking stabilizer measurements during the lattice surgery stage
        T_before_grow: number of rounds of surface code stabilizer measurements before lattice growth
        T_ps_grow: number of post-selected rounds of surface code stabilizer measurements during lattice growth
        T_maintain: number of rounds of surface code stabilizer measurements after lattice growth
        error_rate: physical error rate for each gate
    Returns:
        A stim circuit object that prepares a surface code magic state.
    """
    qrm_code = qrm.QRMCode(error_rate, x_pos_shift=-10)
    sc_shift = qrm_code.total_qubit_number + 1 + 2
    sc_code = sc.SurfaceCode(3, 3, error_rate, off_set=sc_shift)
    circuit = qrm_code.prepare_S_state()
    circuit += sc_code.initialize_cycle('X', postselection='all')
    surface_clock = 1
    # do T_sc_pre rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_sc_pre):
        sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
    surface_clock += T_sc_pre
    # do T_lat_surg rounds of lattice surgery
    surgery_shift = qrm_code.total_qubit_number + 1
    lattice_surgery(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, surface_clock)
    surface_clock += T_lat_surg
    # measure logical X of the QRM code
    qrm_code.X_measurement(circuit)
    # do T_before_grow rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_before_grow):
        rec_shift = 0
        if t == T_sc_pre + T_lat_surg + 1:
            rec_shift = 2 * T_lat_surg + 15 # shift due to lattice surgery and QRM measurement
        sc_code.syndrome_cycle(circuit, t, rec_shift=rec_shift, postselection='all')
    surface_clock += T_before_grow
    # grow the surface code
    sc_code.growth_cycle(circuit, 7, 7, surface_clock, postselection='all')
    surface_clock += 1
    # do T_ps_grow rounds of post-selected surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_ps_grow):
        sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
    surface_clock += T_ps_grow
    # do T_maintain rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_maintain):
        sc_code.syndrome_cycle(circuit, t, error_rate)
    surface_clock += T_maintain
    # measure logical Y of the surface code
    sc_code.Y_measurement_noiseless(circuit)
    # one round of error-free syndrome measurement to finalize the detectors
    sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0, rec_shift=1, postselection='all')

    return circuit

def check_list_gen(sc_shift, surgery_shift):
    check_list = [
        {
            'pos': [-1, -1],
            'idx': surgery_shift,
            'data_qubits': [None, None, 1, sc_shift]
        },
        {
            'pos': [-1, 3],
            'idx': surgery_shift + 1,
            'data_qubits': [3, sc_shift + 1, 2, sc_shift + 2]
        }
    ]
    return check_list

def lattice_surgery(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, time_shift):
    """
    Args:
        circuit: a stim circuit object that prepares a surface code magic state
        T_lat_surg: number of rounds of linking stabilizer measurements during the lattice surgery stage
        error_rate: physical error rate for each gate
        sc_shift: the offset of surface code qubits in the stim circuit
    Returns:
        A stim circuit object after performing lattice surgery.
    """
    check_list = check_list_gen(sc_shift, surgery_shift)
    for check in check_list:
        circuit.append('QUBIT_COORDS', check['idx'], check['pos'])
    
    for t in range(time_shift, time_shift + T_lat_surg):
        for i in range(4):
            CNOT_idx_list = []
            for check in check_list:
                data_qubit = check['data_qubits'][i]
                if data_qubit is None:
                    continue
                CNOT_idx_list.extend([data_qubit, check['idx']])
            circuit.append('CNOT', CNOT_idx_list)
            circuit.append("DEPOLARIZE2", CNOT_idx_list, error_rate)
            circuit.append('TICK')

        # syndrome measurement
        check_idx_list = [check['idx'] for check in check_list]
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')
    
        # detectors
        if t > time_shift:
            for i, check in enumerate(check_list):
                circuit.append('DETECTOR', [stim.target_rec(-i - 1), stim.target_rec(-i - 3)], check['pos'] + [time_shift + t, 1])

    # observable
    circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(-1), stim.target_rec(-2)], 0)