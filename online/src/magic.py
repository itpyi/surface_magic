import src.surface_code as sc
import src.qrm as qrm
import stim
import numpy as np
import src.surgery as sg

def magic_preparation(T, T_lat_surg, t_round, error_rate):
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
    if t_round <= T:
        # do T rounds of surface code stabilizer measurements
        for t in range(surface_clock, surface_clock + t_round):
            sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
        surface_clock += t_round
        sc_code.logical_measurement(circuit, 'X', surface_clock)
    else:
        T_post = t_round - T
        # do T rounds of surface code stabilizer measurements
        for t in range(surface_clock, surface_clock + T):
            sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
        surface_clock += T
        # do T_lat_surg rounds of lattice surgery
        surgery_shift = qrm_code.total_qubit_number + 1
        surgery_unit = sg.SurgeryUnit(qrm_code, sc_code, error_rate, sg_shift=surgery_shift, T_lat_surg=T_lat_surg)
        surgery_unit.lattice_surgery(circuit, T, surface_clock)
        surface_clock += T_lat_surg
        # decouple
        surgery_unit.decouple_after_surgery(circuit, surface_clock)
        surface_clock += 1
        # do T_post rounds of surface code stabilizer measurements
        for t in range(surface_clock, surface_clock + T_post):
            rec_shift = 0
            if t == surface_clock:
                rec_shift = 15 # shift due to lattice surgery and QRM measurement
            sc_code.syndrome_cycle(circuit, t, rec_shift=rec_shift, postselection='all')
        surface_clock += T_post
        # measure logical Y of the surface code
        sc_code.Y_measurement_noiseless(circuit)
        # one round of error-free syndrome measurement to finalize the detectors
        sc_code.syndrome_cycle(circuit, surface_clock, error_rate=0.0, rec_shift=1)

    return circuit