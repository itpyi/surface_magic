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
    qrm_code = qrm.QRMCode(error_rate, x_pos_shift=-8)
    sc_shift = qrm_code.total_qubit_number + 1
    sc_code = sc.SurfaceCode(3, 3, error_rate, off_set=sc_shift)
    circuit = qrm_code.prepare_S_state()
    circuit += sc_code.initialize_cycle('X')

    return circuit

