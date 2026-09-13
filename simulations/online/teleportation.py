from . import surface_code as sc
from . import qrm_code as qrm
import stim
import numpy as np
from . import lattice_surgery as sg

def build_circuit(T, T_lat_surg, t_round, error_rate):
    """Build the pre-teleportation or full online circuit.

    T specifies additional initial surface-code rounds. For t_round <= T,
    the circuit ends before teleportation with logical X readout. For
    t_round > T, it includes T_lat_surg surgery rounds followed by
    t_round - T surface-code rounds and ideal logical Y readout.
    error_rate is the physical gate-error probability.
    """
    qrm_code = qrm.QRMCode(error_rate, x_pos_shift=-10)
    sc_shift = qrm_code.total_qubit_number + 1 + 2
    sc_code = sc.SurfaceCode(3, 3, error_rate, off_set=sc_shift)
    surface_clock = 1
    if t_round <= T:
        # do T rounds of surface code stabilizer measurements
        circuit = sc_code.initialize_cycle('X', postselection='all')
        for t in range(surface_clock, surface_clock + t_round):
            sc_code.syndrome_cycle(circuit, t, error_rate, postselection='all')
        surface_clock += t_round
        sc_code.logical_measurement(circuit, 'X', surface_clock)
        
        return circuit
    else:
        circuit = qrm_code.prepare_S_state()
        circuit += sc_code.initialize_cycle('X', postselection='all')
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