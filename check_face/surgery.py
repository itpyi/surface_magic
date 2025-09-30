import stim
import numpy as np
import surface_code as sc
import qrm

class SurgeryUnit:
    """A class for performing lattice surgery between a QRM code and a surface code."""
    def __init__(self, qrm_code, sc_code: sc.SurfaceCode, error_rate, sg_shift):
        self.qrm_code = qrm_code
        self.sc_code = sc_code
        self.error_rate = error_rate
        self.sg_shift = sg_shift
        self.check_list = [
            {
                'pos': [-1, -1],
                'idx': self.sg_shift,
                'data_qubits': [None, None, 1, self.sc_code.data_dict[(0, 0)]]
            },
            {
                'pos': [-1, 3],
                'idx': self.sg_shift + 1,
                'data_qubits': [3, self.sc_code.data_dict[(0, 2)], 2, self.sc_code.data_dict[(0, 4)]]
            }
        ]
        self.qrm_face_check = [0, 1, 10] # Z checks of the QRM code involved in the surgery

    def lattice_surgery(self, circuit: stim.Circuit, T_lat_surg, error_rate, sc_shift, surgery_shift, time_shift):
        """
        Args:
            circuit: a stim circuit object that prepares a surface code magic state
            T_lat_surg: number of rounds of linking stabilizer measurements during the lattice surgery stage
            error_rate: physical error rate for each gate
            sc_shift: the offset of surface code qubits in the stim circuit
        Returns:
            A stim circuit object after performing lattice surgery.
        """
        for check in self.check_list:
            circuit.append('QUBIT_COORDS', check['idx'], check['pos'])

        # initialize flag for check face

        # measure the stabilizers
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

        # finalize the flags

        # observable
        circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(-1), stim.target_rec(-2)], 0)