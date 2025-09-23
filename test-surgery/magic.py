import surface_code as sc
import qrm
import stim
import numpy as np

########### Test 1: No S gate applied, observable be final XX ###########

def magic_preparation_test_1(T_sc_pre, T_lat_surg, T_before_grow, T_ps_grow, T_maintain, error_rate):
    """
    Test no S gate applied, observable be final XX.
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
    circuit = qrm_code.prepare_X_state()
    circuit += sc_code.initialize_cycle('X', postselection='all')
    surface_clock = 1
    # do T_sc_pre rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_sc_pre):
        sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
    surface_clock += T_sc_pre
    # do T_lat_surg rounds of lattice surgery
    surgery_shift = qrm_code.total_qubit_number + 1
    lattice_surgery_no_measure(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, surface_clock)
    surface_clock += T_lat_surg
    # decouple
    rec_shift = 2 * T_lat_surg
    decouple_after_surgery(qrm_code, sc_code, circuit, error_rate, surface_clock, rec_shift)
    surface_clock += 1
    # do T_before_grow rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_before_grow):
        rec_shift = 0
        if t == surface_clock:
            rec_shift = 15 # shift due to lattice surgery and QRM measurement
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
    sc_code.logical_measurement(circuit, 'X', surface_clock)
    # sc_code.Y_measurement_noiseless(circuit)
    # one round of error-free syndrome measurement to finalize the detectors
    # sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0.0, rec_shift=1)

    return circuit

def lattice_surgery_no_measure(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, time_shift):
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
    check_idx_list = [check['idx'] for check in check_list]
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
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')
    
        # detectors
        check_count = len(check_list)
        if t > time_shift:
            for i, check in enumerate(check_list):
                rec_crr = stim.target_rec(-(check_count - i))
                rec_prev = stim.target_rec(-(check_count - i) - check_count)
                circuit.append('DETECTOR', [rec_crr, rec_prev], check['pos'] + [time_shift + t, 1])

    # observable
    # circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(-1), stim.target_rec(-2)], 0)


########### Test 2: No correct to standard QRM, others same as Test 1 ###########

def magic_preparation_test_2(T_sc_pre, T_lat_surg, T_before_grow, T_ps_grow, T_maintain, error_rate):
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
    circuit = qrm_code.prepare_S_state(if_standard=False)
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
    # decouple
    rec_shift = 2 * T_lat_surg
    decouple_after_surgery(qrm_code, sc_code, circuit, error_rate, surface_clock, rec_shift)
    surface_clock += 1
    # do T_before_grow rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_before_grow):
        rec_shift = 0
        if t == surface_clock:
            rec_shift = 15 # shift due to lattice surgery and QRM measurement
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
    # sc_code.logical_measurement(circuit, 'X', surface_clock)
    sc_code.Y_measurement_noiseless(circuit)
    # one round of error-free syndrome measurement to finalize the detectors
    sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0.0, rec_shift=1)

    return circuit


########### Test 3: SC initialized in Y. Measure YY ###########

def magic_preparation_test_3(T_sc_pre, T_lat_surg, T_before_grow, T_ps_grow, T_maintain, error_rate):
    """
    SC initialized in Y, observable be final YY.
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
    circuit += sc_code.encoding(gate=['H', 'S'])
    surface_clock = 1
    # do T_sc_pre rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_sc_pre):
        sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
    surface_clock += T_sc_pre
    # do T_lat_surg rounds of lattice surgery
    surgery_shift = qrm_code.total_qubit_number + 1
    lattice_surgery_no_measure(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, surface_clock)
    surface_clock += T_lat_surg
    # decouple
    rec_shift = 2 * T_lat_surg
    decouple_after_surgery_Y(qrm_code, sc_code, circuit, error_rate, surface_clock, rec_shift)
    surface_clock += 1
    # do T_before_grow rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_before_grow):
        rec_shift = 0
        if t == surface_clock:
            rec_shift = 15 # shift due to lattice surgery and QRM measurement
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
    # sc_code.logical_measurement(circuit, 'X', surface_clock)
    sc_code.Y_measurement_noiseless(circuit)
    # one round of error-free syndrome measurement to finalize the detectors
    sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0.0, rec_shift=1)

    return circuit

def lattice_surgery_no_measure(circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, time_shift):
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
    check_idx_list = [check['idx'] for check in check_list]
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
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')
    
        # detectors
        check_count = len(check_list)
        if t > time_shift:
            for i, check in enumerate(check_list):
                rec_crr = stim.target_rec(-(check_count - i))
                rec_prev = stim.target_rec(-(check_count - i) - check_count)
                circuit.append('DETECTOR', [rec_crr, rec_prev], check['pos'] + [time_shift + t, 1])


def decouple_after_surgery_Y(qrm_code: qrm.QRMCode, sc_code: sc.SurfaceCode, circuit: stim.Circuit, error_rate, round, rec_shift):
    """
    Logical X measurement on QRM and one round of stabilizer measurement on surface code to decouple the two codes.
    Handle the combined X-stabilzier.
    """
    # syndrome measurement of the surface code
    sc_code.syndrome_measurement(circuit)

    # add detectors except the (-1, 1) X check
    check_count = len(sc_code.check_list)
    for i_crr, check in enumerate(sc_code.check_list):
        if not check['pos'] == [-1, 1]:
            rec_crr  = stim.target_rec(-(check_count - i_crr))
            rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
            detector_pos = [check['pos'][0], check['pos'][1], round, 1]
            circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)
    
    i_crr = 0
    for i, check in enumerate(sc_code.check_list):
        if check['pos'] == [-1, 1]:
            i_crr = i
            break
    ext_rec_crr = -(check_count - i_crr) - 15
    ext_rec_prev = -(check_count - i_crr) - check_count - rec_shift - 15
    ext_stabilizer = [ext_rec_crr, ext_rec_prev]

    # measure logical X of the QRM code
    qrm_code.Y_measurement(circuit, ext_stabilizer)

############ Final Code ###########

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
    # decouple
    rec_shift = 2 * T_lat_surg
    decouple_after_surgery(qrm_code, sc_code, circuit, error_rate, surface_clock, rec_shift)
    surface_clock += 1
    # do T_before_grow rounds of surface code stabilizer measurements
    for t in range(surface_clock, surface_clock + T_before_grow):
        rec_shift = 0
        if t == surface_clock:
            rec_shift = 15 # shift due to lattice surgery and QRM measurement
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
    # sc_code.logical_measurement(circuit, 'X', surface_clock)
    sc_code.Y_measurement_noiseless(circuit)
    # one round of error-free syndrome measurement to finalize the detectors
    sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0.0, rec_shift=1)

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
    check_idx_list = [check['idx'] for check in check_list]
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
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')
    
        # detectors
        check_count = len(check_list)
        if t > time_shift:
            for i, check in enumerate(check_list):
                rec_crr = stim.target_rec(-(check_count - i))
                rec_prev = stim.target_rec(-(check_count - i) - check_count)
                circuit.append('DETECTOR', [rec_crr, rec_prev], check['pos'] + [time_shift + t, 1])

    # observable
    circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(-3), stim.target_rec(-4)], 0)

def decouple_after_surgery(qrm_code: qrm.QRMCode, sc_code: sc.SurfaceCode, circuit: stim.Circuit, error_rate, round, rec_shift):
    """
    Logical X measurement on QRM and one round of stabilizer measurement on surface code to decouple the two codes.
    Handle the combined X-stabilzier.
    """
    # syndrome measurement of the surface code
    sc_code.syndrome_measurement(circuit)

    # add detectors except the (-1, 1) X check
    check_count = len(sc_code.check_list)
    for i_crr, check in enumerate(sc_code.check_list):
        if not check['pos'] == [-1, 1]:
            rec_crr  = stim.target_rec(-(check_count - i_crr))
            rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
            detector_pos = [check['pos'][0], check['pos'][1], round, 1]
            circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)
    
    i_crr = 0
    for i, check in enumerate(sc_code.check_list):
        if check['pos'] == [-1, 1]:
            i_crr = i
            break
    ext_rec_crr = -(check_count - i_crr) - 15
    ext_rec_prev = -(check_count - i_crr) - check_count - rec_shift - 15
    ext_stabilizer = [ext_rec_crr, ext_rec_prev]

    # measure logical X of the QRM code
    qrm_code.X_measurement(circuit, ext_stabilizer)