import stim
import numpy as np
import src.surface_code as sc
import src.qrm as qrm

class SurgeryUnit:
    """A class for performing lattice surgery between a QRM code and a surface code."""
    def __init__(self, qrm_code, sc_code: sc.SurfaceCode, error_rate, sg_shift, T_lat_surg):
        self.qrm_code = qrm_code
        self.sc_code = sc_code
        self.error_rate = error_rate
        self.sg_shift = sg_shift
        self.qrm_face_check = [0, 1, 10] # Z checks of the QRM code involved in the surgery
        self.check_list = self.generate_check_list()
        self.T_lat_surg = T_lat_surg
        self.flag_list = self.generate_flag_list()

    def generate_check_list(self):
        surg_check = [
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
        face_check = [{
            'idx': 0 + 16,
            'pos': [self.qrm_code.x_pos_shift + (0) % 6, 5 + (0) // 6],
            'data_qubits': [1,5,3,7]
        }, {
            'idx': 1 + 16,
            'pos': [self.qrm_code.x_pos_shift + (1) % 6, 5 + (1) // 6],
            'data_qubits': [2,3,7,6]
        }, {
            'idx': 10 + 16,
            'pos': [self.qrm_code.x_pos_shift + (10) % 6, 5 + (10) // 6],
            'data_qubits': [7,6,4,5]
        }]
        return face_check + surg_check

    def generate_flag_list(self):
        flag_list = [
            {
                'idx': 0 + 34,
                'pos': [self.qrm_code.x_pos_shift + (0) % 6, 8 + (0) // 6]
            },
            {
                'idx': 1 + 34,
                'pos': [self.qrm_code.x_pos_shift + (1) % 6, 8 + (1) // 6]
            },
            {
                'idx': 10 + 34,
                'pos': [self.qrm_code.x_pos_shift + (10) % 6, 8 + (10) // 6]
            }
        ]
        return flag_list

    def lattice_surgery(self, circuit: stim.Circuit, T_sc_pre, time_shift):
        """
        Args:
            circuit: a stim circuit object that prepares a surface code magic state
            T_lat_surg: number of rounds of linking stabilizer measurements during the lattice surgery stage
            error_rate: physical error rate for each gate
            sc_shift: the offset of surface code qubits in the stim circuit
        Returns:
            A stim circuit object after performing lattice surgery.
        """
        for check in self.check_list[3:]:
            circuit.append('QUBIT_COORDS', check['idx'], check['pos'])

        # set rec_shift for detectors for the first round
        rec_curr_shift = 8
        rec_prev_shift = 8 * (T_sc_pre + 1) + 36 + rec_curr_shift + 16


        # measure the stabilizers
        for t in range(time_shift, time_shift + self.T_lat_surg):
            # initialize flag for check face
            flag_idx_list = [34 + face_check for face_check in self.qrm_face_check]
            circuit.append('H', flag_idx_list)
            circuit.append('DEPOLARIZE1', flag_idx_list, self.error_rate)
            circuit.append('TICK')
            CNOT_list = []
            for face_check in self.qrm_face_check:
                CNOT_list.extend([34 + face_check, 16 + face_check])
            circuit.append('CNOT', CNOT_list)
            circuit.append("DEPOLARIZE2", CNOT_list, self.error_rate)
            circuit.append('TICK')

            # entangle data qubits with ancilla
            for i in range(4):
                CNOT_idx_list = []
                for check in self.check_list:
                    data_qubit = check['data_qubits'][i]
                    if data_qubit is None:
                        continue
                    CNOT_idx_list.extend([data_qubit, check['idx']])
                circuit.append('CNOT', CNOT_idx_list)
                circuit.append("DEPOLARIZE2", CNOT_idx_list, self.error_rate)
                circuit.append('TICK')

            # finalize the flags
            CNOT_list = []
            for face_check in self.qrm_face_check:
                CNOT_list.extend([34 + face_check, 16 + face_check])
            circuit.append('CNOT', CNOT_list)
            circuit.append("DEPOLARIZE2", CNOT_list, self.error_rate)
            circuit.append('TICK')
            circuit.append('H', flag_idx_list)
            circuit.append('DEPOLARIZE1', flag_idx_list, self.error_rate)
            circuit.append('TICK')

            # syndrome measurement
            check_idx_list = [check['idx'] for check in self.check_list]
            circuit.append('X_ERROR', check_idx_list, self.error_rate)
            circuit.append('MR', check_idx_list)
            # flag measurement
            circuit.append('X_ERROR', flag_idx_list, self.error_rate)
            circuit.append('MR', flag_idx_list)
            circuit.append('TICK')

            # detectors
            if t == time_shift:
                for i, check in enumerate(self.check_list[:3]):
                    mc = [i - rec_curr_shift, check['idx'] - rec_prev_shift]
                    circuit.append('DETECTOR', [stim.target_rec(c) for c in mc], check['pos'] + [time_shift + t, 1])
            if t > time_shift:
                for i, check in enumerate(self.check_list):
                    circuit.append('DETECTOR', [stim.target_rec(i - 8), stim.target_rec(i - 20)], check['pos'] + [time_shift + t, 1])
            for i, flag in enumerate(self.flag_list):
                circuit.append('DETECTOR', [stim.target_rec(i-3)], flag['pos'] + [time_shift + t, 1]) # flag detectors, position not tuned

            # surface code checks
            self.sc_code.Z_syndrome_measurement(circuit)

            # add detectors except the (-1, 1) X check
            check_list = [check for check in self.sc_code.check_list if check['type'] == 'Z']
            check_count = len(check_list)
            for i_crr, check in enumerate(check_list):
                if not check['pos'] == [-1, 1]:
                    rec_crr  = stim.target_rec(-(check_count - i_crr))
                    rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - 8)
                    detector_pos = [check['pos'][0], check['pos'][1], t, 2]
                    circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)

        # observable
        circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(-8), stim.target_rec(-9)], 0)

    def decouple_after_surgery(self, circuit: stim.Circuit, round):
        """
        Logical X measurement on QRM and one round of stabilizer measurement on surface code to decouple the two codes.
        Handle the combined X-stabilzier.
        """
        rec_shift = 12 * self.T_lat_surg
        # rec_shift = 0
        # syndrome measurement of the surface code
        self.sc_code.syndrome_measurement(circuit)

        # add detectors except the (-1, 1) X check
        check_count = len(self.sc_code.check_list)
        for i_crr, check in enumerate(self.sc_code.check_list):
            if check['type'] == 'Z':
                rec_shift = 0
            else:
                rec_shift = 12 * self.T_lat_surg
            if not check['pos'] == [-1, 1]:
                rec_crr  = stim.target_rec(-(check_count - i_crr))
                rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
                detector_pos = [check['pos'][0], check['pos'][1], round, 2]
                circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)

        rec_shift = 12 * self.T_lat_surg
        i_crr = 0
        for i, check in enumerate(self.sc_code.check_list):
            if check['pos'] == [-1, 1]:
                i_crr = i
                break
        ext_rec_crr = -(check_count - i_crr) - 15
        ext_rec_prev = -(check_count - i_crr) - check_count - rec_shift - 15
        ext_stabilizer = [ext_rec_crr, ext_rec_prev]

        # measure logical X of the QRM code
        self.qrm_code.X_measurement(circuit, ext_stabilizer)