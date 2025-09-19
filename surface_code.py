import numpy as np
import stim

class SurfaceCode:
    def __init__(self, m: int, n: int, error_rate: float = 0.001, off_set: int = 0):
        self.m = m # Number of columns
        self.n = n # Number of rows
        self.error_rate = error_rate
        self.off_set = off_set
        self.data_dict, self.data_list = self.generate_data_dict_and_list()
        self.check_list = self.generate_check_list(self.data_dict)
        self.total_qubit_number = len(self.data_list) + len(self.check_list) + self.off_set

    def generate_data_dict_and_list(self):
        """
        data_dict: (for finding index of a data qubit from position)
            key: position, 
            value: index,
        data_list: list of indices (for loop over data qubits)
        """
        data_dict = {}
        data_list = []
        idx = self.off_set
        for i in range(self.m):
            for j in range(self.n):
                data_dict[(2 * i, 2 * j)] = idx
                data_list.append(idx)
                idx += 1
        return data_dict, data_list

    def generate_check_list(self, data_dict):
        """
        list of dicts: {
            'type': 'X' or 'Z',
            'pos': position,
            'idx': index,
            'data_qubits'; indices of data qubits to check
        }
        """
        check_list = []
        idx = self.m * self.n + self.off_set
        # X checks
        for i in range(0, self.m + 1, 2):
            for j in range(self.n - 1):
                pos = [2 * i - 1 + 2 * (j % 2), 2 * j + 1]
                if pos[0] <= 2 * self.m - 1:
                    check_list.append({
                        'type': 'X',
                        'pos': pos,
                        'idx': idx,
                        'data_qubits': [
                            data_dict.get((pos[0] - 1, pos[1] - 1)),
                            data_dict.get((pos[0] - 1, pos[1] + 1)),
                            data_dict.get((pos[0] + 1, pos[1] - 1)),
                            data_dict.get((pos[0] + 1, pos[1] + 1)),
                        ]
                    })
                    idx += 1
        # Z checks
        for i in range(self.m - 1):
            for j in range(0, self.n + 1, 2):
                pos = [2 * i + 1, 2 * j + 1 - 2 * (i % 2)]
                if pos[1] <= 2 * self.n - 1:
                    check_list.append({
                        'type': 'Z',
                        'pos': pos,
                        "idx": idx,
                        'data_qubits': [
                            data_dict.get((pos[0] - 1, pos[1] - 1)),
                            data_dict.get((pos[0] + 1, pos[1] - 1)),
                            data_dict.get((pos[0] - 1, pos[1] + 1)),
                            data_dict.get((pos[0] + 1, pos[1] + 1)),
                        ]
                    })
                    idx += 1
        return check_list

    def circuit_standard_Z(self, rounds: int = 10, if_measure=True):
        circuit = self.initialize_circuit_position()
        self.initialize_circuit(circuit)
        for t in range(rounds):
            self.depolarize_data(circuit)
            self.syndrome_measurement(circuit, t)
        if if_measure:
            self.Z_measurement(circuit, rounds)
        return circuit

    def initialize_circuit_position(self):
        circuit = stim.Circuit()
        for pos in self.data_dict:
            circuit.append("QUBIT_COORDS", self.data_dict[pos], pos)
        for check in self.check_list:
            circuit.append("QUBIT_COORDS", check['idx'], check['pos'])
        return circuit

    def initialize_circuit(self, circuit: stim.Circuit):
        # Initialize data qubits
        for i in self.data_list:
            circuit.append("R", i)
        # Initialize ancilla qubits
        for check in self.check_list:
            circuit.append("R", check['idx'])

    def depolarize_data(self, circuit: stim.Circuit):
        circuit.append("DEPOLARIZE1", self.data_list, self.error_rate)
        circuit.append('TICK')

    def syndrome_measurement(self, circuit: stim.Circuit, round: int, rec_shift: int = 0, postselection=None):
        # initialize X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("DEPOLARIZE1", check['idx'], self.error_rate)
        circuit.append('TICK')

        # CNOT layers
        for i in range(4):
            for check in self.check_list:
                if check['type'] == 'X' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['idx'], check['data_qubits'][i]])
                if check['type'] == 'Z' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['data_qubits'][i], check['idx']])
            for check in self.check_list:
                if check['type'] == 'X' and check['data_qubits'][i] != None:
                    circuit.append("DEPOLARIZE2", [check['idx'], check['data_qubits'][i]], self.error_rate)
                if check['type'] == 'Z' and check['data_qubits'][i] != None:
                    circuit.append("DEPOLARIZE2", [check['data_qubits'][i], check['idx']], self.error_rate)
            circuit.append('TICK')

        # Hadamard layer for X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("DEPOLARIZE1", [check['idx']], self.error_rate)
        circuit.append('TICK')

        # syndrome measurement
        for check in self.check_list:
            circuit.append('X_ERROR', [check['idx']], self.error_rate)
        for check in self.check_list:
            circuit.append('MR', [check['idx']])
        circuit.append('TICK')

        # if detector is required, add detector operations
        check_count = len(self.check_list)
        if round > 0:
            for i_crr, check in enumerate(self.check_list):
                rec_crr  = stim.target_rec(-(check_count - i_crr))
                rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
                detector_pos = [check['pos'][0], check['pos'][1], round]
                if postselection == 'all':
                    detector_pos.append(1)
                circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)
        else:
            for i_crr, check in enumerate(self.check_list):
                if check['type'] == 'Z':
                    rec_crr  = stim.target_rec(-(check_count - i_crr))
                    detector_pos = [check['pos'][0], check['pos'][1], round]
                    if postselection == 'all':
                        detector_pos.append(1)
                    circuit.append('DETECTOR', [rec_crr], detector_pos)

    def syndrome_measurement_noiseless(self, circuit: stim.Circuit, round: int, rec_shift: int = 0):
        # initialize X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        circuit.append('TICK')

        # CNOT layers
        for i in range(4):
            for check in self.check_list:
                if check['type'] == 'X' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['idx'], check['data_qubits'][i]])
                if check['type'] == 'Z' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['data_qubits'][i], check['idx']])
            circuit.append('TICK')

        # Hadamard layer for X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        circuit.append('TICK')

        # syndrome measurement
        for check in self.check_list:
            circuit.append('MR', [check['idx']])
        circuit.append('TICK')

        # if detector is required, add detector operations
        check_count = len(self.check_list)
        if round > 0:
            for i_crr, check in enumerate(self.check_list):
                rec_crr  = stim.target_rec(-(check_count - i_crr))
                rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
                circuit.append('DETECTOR', [rec_crr, rec_prev], [check['pos'][0], check['pos'][1], round])
        else:
            for i_crr, check in enumerate(self.check_list):
                if check['type'] == 'Z':
                    rec_crr  = stim.target_rec(-(check_count - i_crr))
                    circuit.append('DETECTOR', [rec_crr], [check['pos'][0], check['pos'][1], round])

    def Z_measurement(self, circuit: stim.Circuit, round: int):
        # Measure all data qubits
        circuit.append('X_ERROR', self.data_list, self.error_rate)
        circuit.append('MR', self.data_list)

        # Extract Z-syndrome and make a detector
        for i, check in enumerate(self.check_list):
            if check['type'] == 'Z':
                qubit_rec_shift = - self.m * self.n # shift (0, mn) to (-mn, 0)
                check_rec_shift = - 2 * self.m * self.n + 1 # shift (0, mn-1) to (-2mn + 1, -mn)
                detector_list = [stim.target_rec(i + check_rec_shift)] + [stim.target_rec(self.data_list.index(check['data_qubits'][j]) + qubit_rec_shift) for j in range(4) if check['data_qubits'][j] != None]
                circuit.append('DETECTOR', detector_list, [check['pos'][0], check['pos'][1], round])

        # Extract logical Z
        qubit_rec_shift = - self.m * self.n # shift (0, mn) to (-mn, 0)
        logical_Z = [stim.target_rec(i + qubit_rec_shift) for i in range(self.n)]
        circuit.append('OBSERVABLE_INCLUDE', logical_Z, 0)

    def grow_code(self, circuit: stim.Circuit, round_start: int, round_end: int, m_new: int, n_new: int, postselection=None, if_measure=True):
        old_N = self.total_qubit_number
        old_check_list = self.check_list.copy()
        old_m = self.m
        old_n = self.n
        self.reset_indices_for_growth(m_new, n_new)
        new_N = self.total_qubit_number
        for pos in self.data_dict:
            idx = self.data_dict[pos]
            if idx >= old_N:
                circuit.append("QUBIT_COORDS", idx, pos)
                circuit.append('R', idx)
        for pos in self.data_dict:
            if pos[0] > 2 * (old_m - 1):
                idx = self.data_dict[pos]
                circuit.append('H', idx)
        for check in self.check_list:
            idx = check['idx']
            if idx in range(old_N, new_N):
                circuit.append("QUBIT_COORDS", idx, check['pos'])
                circuit.append('R', idx)

        self.depolarize_data(circuit)
        self.syndrome_measurement_after_growth(circuit, old_check_list, old_m, old_n, round_start, postselection=postselection)

        for t in range(round_start+1, round_end):
            self.depolarize_data(circuit)
            self.syndrome_measurement(circuit, t, postselection=postselection)
        if if_measure:
            self.Z_measurement(circuit, round_end)
        
        return circuit


    def reset_indices_for_growth(self, m_new, n_new):
        self.m = m_new
        self.n = n_new
        new_data_dict, new_data_list = self.generate_data_dict_and_list()
        new_check_list = self.generate_check_list(new_data_dict)
        
        # update data qubits and build data index map
        data_map = {}
        for i, data_qubit_position in enumerate(new_data_dict):
            idx_new_construct = new_data_dict[data_qubit_position]
            idx_targ = 0
            if data_qubit_position in self.data_dict:
                idx_targ = self.data_dict[data_qubit_position]
                # print('existing data qubit found')
            else:
                idx_targ = self.total_qubit_number
                self.total_qubit_number += 1
                # print('new data qubit')
            new_data_dict[data_qubit_position] = idx_targ
            new_data_list[i] = idx_targ
            data_map[idx_new_construct] = idx_targ
            # print('reset index as', idx_new_construct, 'to', idx_targ)
        self.data_dict = new_data_dict
        self.data_list = new_data_list

        # update checks
        for i in range(len(new_check_list)):
            check = new_check_list[i]
            idx_targ = 0
            if_old = False
            for old_check in self.check_list:
                if check['pos'] == old_check['pos']:
                    if_old = True
                    idx_targ = old_check['idx']
                    # print('existing check qubit found')
                    break
            if not if_old:
                idx_targ = self.total_qubit_number
                self.total_qubit_number += 1
                # print('new check qubit')
            new_check_list[i]['idx'] = idx_targ
            # print('reset index as', check['idx'], 'to', idx_targ)
            for j in range(4):
                idx_new_construct = check['data_qubits'][j]
                new_check_list[i]['data_qubits'][j] = data_map.get(idx_new_construct)
                # print('reset checked data qubit as', idx_new_construct, 'to', new_check_list[i]['data_qubits'][j])
        self.check_list = new_check_list
    
    def syndrome_measurement_after_growth(self, circuit: stim.Circuit, old_check_list, old_m, old_n, round:int, postselection=None):
        # initialize X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("DEPOLARIZE1", check['idx'], self.error_rate)
        circuit.append('TICK')

        # CNOT layers
        for i in range(4):
            for check in self.check_list:
                if check['type'] == 'X' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['idx'], check['data_qubits'][i]])
                if check['type'] == 'Z' and check['data_qubits'][i] != None:
                    circuit.append('CNOT', [check['data_qubits'][i], check['idx']])
            for check in self.check_list:
                if check['type'] == 'X' and check['data_qubits'][i] != None:
                    circuit.append("DEPOLARIZE2", [check['idx'], check['data_qubits'][i]], self.error_rate)
                    # circuit.append("CORRELATED_ERROR", [check['idx'], check['data_qubits'][i]], error_rate)
                if check['type'] == 'Z' and check['data_qubits'][i] != None:
                    circuit.append("DEPOLARIZE2", [check['data_qubits'][i], check['idx']], self.error_rate)
                    # circuit.append("CORRELATED_ERROR", [check['data_qubits'][i], check['idx']], error_rate)
            circuit.append('TICK')

        # Hadamard layer for X-check ancillae
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append('H', check['idx'])
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("DEPOLARIZE1", [check['idx']], self.error_rate)
        circuit.append('TICK')

        # syndrome measurement
        for check in self.check_list:
            circuit.append('X_ERROR', [check['idx']], self.error_rate)
        for check in self.check_list:
            circuit.append('MR', [check['idx']])
        circuit.append('TICK')

        # add detector
        # 3 cases:
        #   1. The check qubit is in the old list: the detector compares measurement in this round with the previous round
        #   2. The check is of type-Z and pos[0] < 2 * (old_m - 1) and pos[1] > 2 * old_n: the detector is directly this round of measurement
        #   3. The check is of type-X and pos[0] > 2 * old_m: the detector is directly this round of measurement
        old_positions = {tuple(ch['pos']) for ch in old_check_list}
        prev_check_count = len(old_check_list)
        curr_check_count = len(self.check_list)
        pos_to_prev_idx = {tuple(ch['pos']): i for i, ch in enumerate(old_check_list)}

        for i_curr, check in enumerate(self.check_list):
            pos = tuple(check['pos'])
            pos_t = [pos[0], pos[1], round]
            if postselection == 'all':
                pos_t.append(1)

            # REC of this round for this check (based on MR order, not qubit index)
            rec_curr = stim.target_rec(-(curr_check_count - i_curr))

            # Case 1: existing check within old region -> compare with previous round
            if pos in old_positions:
                i_prev = pos_to_prev_idx[pos]
                rec_prev = stim.target_rec(-(curr_check_count + (prev_check_count - i_prev)))
                circuit.append('DETECTOR', [rec_curr, rec_prev], pos_t)
            # Case 2: new Z-check -> single-round detector
            elif check['type'] == 'Z' and (pos[0] < 2 * (old_m - 1) and pos[1] > 2 * old_n):
                circuit.append('DETECTOR', [rec_curr], pos_t)
            # Case 3: new X-check -> single-round detector
            elif check['type'] == 'X' and pos[0] > 2 * old_m:
                circuit.append('DETECTOR', [rec_curr], pos_t)

    def encoding(self, gate: list[str] = ['I']):
        """
        A noiseless encoding circuit that encodes the physical state of the qubit at (0,0) to the logical qubit.
        The gate can be a single-qubit Clifford gate.
        """
        circuit = self.initialize_circuit_position()
        # Coordinates / indices
        src_idx = self.data_dict[(0, 0)]

        circuit.append("R", self.data_list)
        circuit.append("R", [c['idx'] for c in self.check_list])

        # Apply single-qubit Clifford gate to the source data qubit
        for g in gate:
            g = g.upper()
            if g in ("X", "Y", "Z", "H", "S"):
                circuit.append(g, src_idx)
            elif g in ("I", "ID", ""):
                pass
            else:
                raise ValueError(f"Unsupported gate '{gate}'. Use one of I,X,Y,Z,H,S.")

        # Fan out along first row to encode into a repetition (logical X string) subsystem
        first_row_indices = [self.data_dict[(2 * j, 0)] for j in range(self.m)]
        for tgt in first_row_indices[1:]:
            circuit.append("CNOT", [src_idx, tgt])
        circuit.append("TICK")

        # (Optional) One noiseless stabilizer round to start in codespace
        # Initialize ancillas
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("H", check['idx'])
        circuit.append("TICK")

        # Data-ancilla CNOT pattern (noiseless)
        for layer in range(4):
            for check in self.check_list:
                dq = check['data_qubits'][layer]
                if dq is None:
                    continue
                if check['type'] == 'X':
                    circuit.append("CNOT", [check['idx'], dq])
                else:  # Z check
                    circuit.append("CNOT", [dq, check['idx']])
            circuit.append("TICK")

        # Finish X ancillas
        for check in self.check_list:
            if check['type'] == 'X':
                circuit.append("H", check['idx'])
        circuit.append("TICK")

        # Measure ancillas (no detectors; projection only)
        for check in self.check_list:
            circuit.append("MR", [check['idx']])
        circuit.append("TICK")

        return circuit

    def Y_measurement_noiseless(self, circuit: stim.Circuit):
        """
        A noiseless logical Y measurement circuit.
        The logical Y operator is a product of a vertical logical Z operator and a horizontal logical X operator.
        """
        logical_Y = [stim.target_y(self.data_dict[(0, 0)])]
        for i in range(1, self.m):
            logical_Y.append(stim.target_x(self.data_dict[(2 * i, 0)]))
        for j in range(1, self.n):
            logical_Y.append(stim.target_z(self.data_dict[(0, 2 * j)]))

        logical_Y = stim.target_combined_paulis(logical_Y)
        circuit.append('MPP', logical_Y)

        circuit.append('OBSERVABLE_INCLUDE', stim.target_rec(-1), 1)

    ## This method is not fault-tolerant, trying to figure out the reason

    # def S_state_preserving(self, rounds: int = 10):
    #     circuit = self.encoding(gate=['H', 'S'])
    #     for round in range(1, rounds):
    #         self.syndrome_measurement(circuit, round)
    #     self.Y_measurement_noiseless(circuit)
    #     for round in range(rounds, rounds + 5):
    #         shift = 1 if round == rounds else 0
    #         self.syndrome_measurement(circuit, round, rec_shift=shift)
    #     return circuit
    
    def S_state_preserving(self, rounds: int = 10):
        circuit = self.encoding(gate=['H', 'S'])
        for round in range(1, rounds):
            self.syndrome_measurement(circuit, round)
        self.Y_measurement_noiseless(circuit)
        self.syndrome_measurement_noiseless(circuit, rounds, rec_shift=1)
        return circuit

    def S_state_preserving_with_growth(self, T, rounds):
        circuit = self.encoding(gate=['H', 'S'])
        if rounds < T:
            for round in range(1, rounds):
                self.syndrome_measurement(circuit, round)
        else:
            for round in range(1, T):
                self.syndrome_measurement(circuit, round)
            circuit = self.grow_code(circuit, T, rounds, self.m + 2, self.n + 2, if_measure=False)
        self.Y_measurement_noiseless(circuit)
        self.syndrome_measurement_noiseless(circuit, rounds, rec_shift=1)
        return circuit