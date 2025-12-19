import numpy as np
import stim
import galois


class QRMCode:
    def __init__(self, error_rate, x_pos_shift = 0):
        self.n = 15
        self.k = 1
        self.d = 3
        self.X_checks = [
            [1,3,5,7,9,11,13,15],
            [2,3,6,7,10,11,14,15],
            [4,5,6,7,12,13,14,15],
            [8,9,10,11,12,13,14,15]
        ]
        self.Z_checks = [
            [ 1, 3, 5, 7, 0, 0],
            [ 3, 2, 7, 6, 0, 0],
            [ 2, 6,14,10, 0, 0],
            [ 6,14,12, 4, 0, 0],
            [13,12, 4, 5, 0, 0],
            [12, 8, 0,13, 9, 0],
            [ 8, 9,10,11, 0, 0],
            [ 9, 1,11, 3, 0, 0],
            [ 5, 7,13,15, 0, 0],
            [10,11,15,14, 0, 0],
            # redundancies
            [ 4, 5, 0, 0, 7, 6],
            [14, 0, 8, 0,10,12],
            [ 0, 0, 9, 1, 5,13],
            [ 0,10, 2, 0,11, 3],
            [ 0,15, 6, 0,14, 7],
            [15,13, 0, 0,12,14],
            [ 7, 0, 3, 0,15,11],
            [11, 0, 0, 9,13,15]
        ]
        self.meta_checks = [
            [ 1,18, 8, 9],
            [ 1,18,13,17],
            [ 2,10,14,15],
            [ 2,10, 3,17],
            [ 5,15, 4, 9],
            [ 5,15,11,16],
            [ 7,16, 6,10],
            [ 7,16,12,18],
        ]
        self.z_syndrome_feedback = self.z_syndrome_feedback_gen()
        self.error_rate = error_rate
        self.total_qubit_number = 51  # 15 data qubits + 18 ancilla qubits + 18 flag qubits
        self.x_pos_shift = x_pos_shift  # shift the x coordinates of the QRM code qubits by this amount


    def z_syndrome_feedback_gen(self):
        F = galois.GF(2)

        H = self.to_matrix_np(self.Z_checks[:10])
        sub_col = [i - 1 for i in [1,2,4,8,3,5,6,9,10,12]]  # select 10 columns from 15 columns
        H_sub = H[:, sub_col]
        C_sub = np.linalg.inv(H_sub)
        # print(M)
        log_X = np.array([1] * 7 + [0] * 8, dtype=np.uint8).view(F)
        C_full = np.array([C_sub[sub_col.index(i), :] if i in sub_col else [0]*10 for i in range(15)], dtype=np.uint8).view(F)
        for i in range(10):
            if np.sum(C_full[:3, i]) == 1:  # odd overlap with qubits 1, 2, 3
                C_full[:, i] = (C_full[:, i] + log_X)
        return C_full


    def to_matrix_np(self, L):
        F = galois.GF(2)
        M = np.zeros((10, 15), dtype=np.uint8)
        for i, cols in enumerate(L):
            if len(cols) == 0:
                continue
            cols = list(filter(lambda x: x != 0, cols))
            idx = np.asarray(cols) - 1  # convert 1-based to 0-based
            M[i, idx] = 1
        M = M.view(F)
        return M
    

    def get_bit(self, n, i):
        return (n >> i) & 1


    def prepare_S_state(self):
        """
        Returns a QRM circuit with depolarizing noise applied.
        The error rate can be adjusted.
        """
        circuit = stim.Circuit()
        for i in range(1, 16):
            circuit.append_operation("QUBIT_COORDS", [i], [self.x_pos_shift + self.get_bit(i,0) + 2 * self.get_bit(i,2), self.get_bit(i,1) + 2 * self.get_bit(i,3)])
        for j in range(16,34):
            circuit.append_operation("QUBIT_COORDS", [j], [self.x_pos_shift + (j - 16) % 6, 5 + (j - 16) // 6])
        for j in range(34,52):
            circuit.append_operation("QUBIT_COORDS", [j], [self.x_pos_shift + (j - 34) % 6, 8 + (j - 34) // 6])

        # initialize data qubits, ancilla qubits and flags
        circuit.append('H', list(range(1, 16)) + list(range(34, 52)))
        circuit.append("DEPOLARIZE1", range(1,52), [self.error_rate])
        circuit.append('TICK')

        # one round of stabilizer measurements
        for i in range(6):
            # initial flags
            CNOT_list = []
            if i == 0:
                for j in range(18):
                    CNOT_list.extend([34 + j, 16 + j])
                circuit.append('CNOT', CNOT_list)
                circuit.append("DEPOLARIZE2", CNOT_list, [self.error_rate])
                circuit.append('TICK')
            # Z-check measurements
            CNOT_list = []
            for j in range(18):
                qubit = self.Z_checks[j][i]
                if qubit != 0:
                    CNOT_list.extend([qubit, 16 + j])
            circuit.append('CNOT', CNOT_list)
            circuit.append("DEPOLARIZE2", CNOT_list, [self.error_rate])
            circuit.append('TICK')
            # final flags
            if i == 5:
                CNOT_list = []
                for j in range(18):
                    CNOT_list.extend([34 + j, 16 + j])
                circuit.append('CNOT', CNOT_list)
                circuit.append("DEPOLARIZE2", CNOT_list, [self.error_rate])
                circuit.append('TICK')
                circuit.append('H', list(range(34,52)))
                circuit.append("DEPOLARIZE1", range(34,52), [self.error_rate])
                circuit.append('TICK')
        circuit.append('X_ERROR', list(range(16, 52)), [self.error_rate])
        circuit.append('MR', list(range(16, 52)))


        # metachecks
        for i, mc in enumerate(self.meta_checks):
            mc = [c - 37 for c in mc]
            circuit.append('DETECTOR', [stim.target_rec(mc[0]),stim.target_rec(mc[1]),stim.target_rec(mc[2]),stim.target_rec(mc[3])], [self.x_pos_shift + i, 0, 0, 1])

        # check flags
        for j in range(18):
            circuit.append('DETECTOR', [stim.target_rec(-j-1)], [self.x_pos_shift + j // 4, j % 4, 1, 1]) 
        circuit.append('TICK')


        # apply transversal gates
        circuit.append('S_DAG', list(range(1, 16)))
        feedback_list = []
        for i in range(15):
            for j in range(10):
                if self.z_syndrome_feedback[i, j] == 1:
                    feedback_list.extend([stim.target_rec(j - 36), i + 1])
        circuit.append('CZ', feedback_list)
        circuit.append("DEPOLARIZE1", range(1,16), [self.error_rate])
        circuit.append('TICK')

        # return a standard qrm code in S state
        return circuit


    def Y_measurement(self, circuit):
        """
        Returns a QRM circuit with Y measurements applied.
        """
        circuit.append('S_DAG', list(range(1, 16)))
        circuit.append('H', list(range(1, 16)))
        circuit.append("DEPOLARIZE1", range(1,16), [self.error_rate])
        circuit.append('TICK')

        circuit.append('X_ERROR', list(range(1, 16)), [self.error_rate])
        circuit.append('MR', list(range(1, 16)))
        circuit.append('TICK')
    
        # readout checks
        for i, stabilizer in enumerate(self.X_checks):
            circuit.append('DETECTOR', [stim.target_rec(i - 16) for i in stabilizer], [self.x_pos_shift + i, 0, 2, 1])

    
        # readout logical Y
        circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(i - 15) for i in range(15)], 0)
    

    def X_measurement(self, circuit, ext_stabilizer):
        """
        Returns a QRM circuit with X measurements applied.
        """
        circuit.append('H', list(range(1, 16)))
        circuit.append("DEPOLARIZE1", range(1,16), [self.error_rate])
        circuit.append('TICK')

        circuit.append('X_ERROR', list(range(1, 16)), [self.error_rate])
        circuit.append('MR', list(range(1, 16)))
        circuit.append('TICK')
    
        # readout checks
        for i, stabilizer in enumerate(self.X_checks):
            if i > 0:
                circuit.append('DETECTOR', [stim.target_rec(j - 16) for j in stabilizer], [self.x_pos_shift + i, 0, 2, 1])
            else:
                circuit.append('DETECTOR', [stim.target_rec(j - 16) for j in stabilizer] + [stim.target_rec(j) for j in ext_stabilizer], [self.x_pos_shift + i, 0, 2, 1])

    
        # readout logical X
        circuit.append('OBSERVABLE_INCLUDE', [stim.target_rec(i - 15) for i in range(15)], 0)