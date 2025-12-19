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

    
    #########################################
    ############### Data structures ##########################
    #########################################
    # data_dict: (for finding index of a data qubit from position)
    #     key: position, 
    #     value: index,
    # data_list: list of indices (for loop over data qubits)
    # check_list: list of dicts: {
    #     'type': 'X' or 'Z', 
    #     'pos': position,
    #     'idx': index,
    #     'data_qubits'; indices of data qubits to check
    # }
    #########################################

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

    #########################################
    ############### Code cycles ##########################
    #########################################

    def initialize_cycle(self, type: str, postselection=None):
        circuit = self.initialize_circuit_position()
        self.initialize_circuit(circuit, type)
        self.depolarize_all(circuit)
        self.syndrome_measurement(circuit)
        self.add_detectors_initial(circuit, 0, type, postselection)
        return circuit

    def syndrome_cycle(self, circuit: stim.Circuit, round: int, error_rate=None, rec_shift: int=0, postselection=None):
        self.syndrome_measurement(circuit, error_rate)
        self.add_detectors(circuit, round, rec_shift=rec_shift, postselection= postselection)

    def growth_cycle(self, circuit: stim.Circuit, m_new: int, n_new: int, round: int, postselection=None):
        old_N = self.total_qubit_number
        old_check_list = self.check_list.copy()
        old_m = self.m
        old_n = self.n
        self.reset_indices_for_growth(m_new, n_new)
        new_N = self.total_qubit_number
        new_data_idx_list = []
        new_check_idx_list = []
        for pos in self.data_dict:
            idx = self.data_dict[pos]
            if idx >= old_N:
                circuit.append("QUBIT_COORDS", idx, pos)
                new_data_idx_list.append(idx)
        for check in self.check_list:
            idx = check['idx']
            if idx in range(old_N, new_N):
                circuit.append("QUBIT_COORDS", idx, check['pos'])
                new_check_idx_list.append(idx)
        new_data_X_idx_list = [self.data_dict[pos] for pos in self.data_dict if pos[0] > 2 * (old_m - 1)]
        circuit.append("R", new_data_idx_list + new_check_idx_list)
        circuit.append("H", new_data_X_idx_list)
        circuit.append("DEPOLARIZE1", new_data_X_idx_list, self.error_rate)

        circuit.append('TICK')

        self.depolarize_all(circuit)
        self.syndrome_measurement(circuit)
        self.add_detectors_after_growth(circuit, old_check_list, old_m, old_n, round, postselection=postselection)

    #########################################
    ############### Circuit components ##########################
    #########################################

    def initialize_circuit_position(self):
        circuit = stim.Circuit()
        for pos in self.data_dict:
            circuit.append("QUBIT_COORDS", self.data_dict[pos], pos)
        for check in self.check_list:
            circuit.append("QUBIT_COORDS", check['idx'], check['pos'])
        return circuit

    def initialize_circuit(self, circuit: stim.Circuit, type: str):
        # Initialize data qubits
        circuit.append("R", self.data_list)
        # Initialize ancilla qubits
        check_idx_list = [check['idx'] for check in self.check_list]
        circuit.append("R", check_idx_list)

        if type == 'X':
            circuit.append('H', self.data_list)
            circuit.append("DEPOLARIZE1", self.data_list, self.error_rate)

    def depolarize_all(self, circuit: stim.Circuit):
        circuit.append("DEPOLARIZE1", self.data_list, self.error_rate)
        check_idx_list = [check['idx'] for check in self.check_list]
        circuit.append("DEPOLARIZE1", check_idx_list, self.error_rate)
        circuit.append('TICK')

    def syndrome_measurement(self, circuit: stim.Circuit, error_rate=None):
        # use specified error rate if provided, otherwise use the default one
        if error_rate is None:
            error_rate = self.error_rate

        # initialize X-check ancillae
        X_check_idx_list = [check['idx'] for check in self.check_list if check['type'] == 'X']
        circuit.append('H', X_check_idx_list)
        circuit.append("DEPOLARIZE1", X_check_idx_list, error_rate)
        circuit.append('TICK')

        # CNOT layers
        for i in range(4):
            CNOT_idx_list = []
            for check in self.check_list:
                data_qubit = check['data_qubits'][i]
                if data_qubit is None:
                    continue
                if check['type'] == 'X':
                    CNOT_idx_list.extend([check['idx'], data_qubit])
                if check['type'] == 'Z':
                    CNOT_idx_list.extend([data_qubit, check['idx']])
            circuit.append('CNOT', CNOT_idx_list)
            circuit.append("DEPOLARIZE2", CNOT_idx_list, error_rate)
            circuit.append('TICK')

        # Hadamard layer for X-check ancillae
        circuit.append('H', X_check_idx_list)
        circuit.append("DEPOLARIZE1", X_check_idx_list, error_rate)
        circuit.append('TICK')

        # syndrome measurement
        check_idx_list = [check['idx'] for check in self.check_list]
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')

    def Z_syndrome_measurement(self, circuit: stim.Circuit, error_rate=None):
        # use specified error rate if provided, otherwise use the default one
        if error_rate is None:
            error_rate = self.error_rate

        # CNOT layers
        for i in range(4):
            CNOT_idx_list = []
            for check in self.check_list:
                data_qubit = check['data_qubits'][i]
                if data_qubit is None:
                    continue
                if check['type'] == 'Z':
                    CNOT_idx_list.extend([data_qubit, check['idx']])
            circuit.append('CNOT', CNOT_idx_list)
            circuit.append("DEPOLARIZE2", CNOT_idx_list, error_rate)
            circuit.append('TICK')

        # syndrome measurement
        check_idx_list = [check['idx'] for check in self.check_list if check['type'] == 'Z']
        circuit.append('X_ERROR', check_idx_list, error_rate)
        circuit.append('MR', check_idx_list)
        circuit.append('TICK')

    def logical_measurement(self, circuit: stim.Circuit, type: str, round: int):
        # Hadamard for X measurement
        if type == 'X':
            circuit.append('H', self.data_list)
            circuit.append("DEPOLARIZE1", self.data_list, self.error_rate)
            circuit.append('TICK')

        # Measure all data qubits
        circuit.append('X_ERROR', self.data_list, self.error_rate)
        circuit.append('MR', self.data_list)

        # Extract Z/X-syndrome and make a detector
        for i, check in enumerate(self.check_list):
            if check['type'] == type:
                qubit_rec_shift = - self.m * self.n # shift (0, mn) to (-mn, 0)
                check_rec_shift = - 2 * self.m * self.n + 1 # shift (0, mn-1) to (-2mn + 1, -mn)
                detector_list = [stim.target_rec(i + check_rec_shift)] + [stim.target_rec(self.data_list.index(check['data_qubits'][j]) + qubit_rec_shift) for j in range(4) if check['data_qubits'][j] != None]
                circuit.append('DETECTOR', detector_list, [check['pos'][0], check['pos'][1], round])

        # Extract logical Z/X
        qubit_rec_shift = - self.m * self.n # shift (0, mn) to (-mn, 0)
        logical = []
        if type == 'Z':
            logical = [stim.target_rec(self.data_list.index(self.data_dict[(0, i * 2)]) + qubit_rec_shift) for i in range(self.n)]
        elif type == 'X':
            logical = [stim.target_rec(self.data_list.index(self.data_dict[(i * 2, 0)]) + qubit_rec_shift) for i in range(self.m)]
        circuit.append('OBSERVABLE_INCLUDE', logical, 0)

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

        circuit.append('OBSERVABLE_INCLUDE', stim.target_rec(-1), 0)

    def add_detectors(self, circuit: stim.Circuit, round: int, rec_shift: int = 0, postselection=None):
        check_count = len(self.check_list)
        for i_crr, check in enumerate(self.check_list):
            rec_crr  = stim.target_rec(-(check_count - i_crr))
            rec_prev = stim.target_rec(-(check_count - i_crr) - check_count - rec_shift)
            detector_pos = [check['pos'][0], check['pos'][1], round]
            if postselection == 'all':
                detector_pos.append(1)
            circuit.append('DETECTOR', [rec_crr, rec_prev], detector_pos)

    def add_detectors_initial(self, circuit: stim.Circuit, round: int, type: str, postselection=None):
        check_count = len(self.check_list)
        for i_crr, check in enumerate(self.check_list):
            if check['type'] == type:
                rec_crr  = stim.target_rec(-(check_count - i_crr))
                detector_pos = [check['pos'][0], check['pos'][1], round]
                if postselection == 'all':
                    detector_pos.append(1)
                circuit.append('DETECTOR', [rec_crr], detector_pos)

    def add_detectors_after_growth(self, circuit: stim.Circuit, old_check_list, old_m, old_n, round:int, postselection=None):
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
        CNOT_idx_list = []
        for tgt in first_row_indices[1:]:
            CNOT_idx_list.extend([src_idx, tgt])
        circuit.append("CNOT", CNOT_idx_list)
        circuit.append("TICK")

        self.syndrome_measurement(circuit, error_rate=0)

        return circuit

    
    #########################################
    ############### Example circuits ##########################
    #########################################
    
    def circuit_standard(self, type: str, rounds: int, if_measure=True):
        circuit = self.initialize_circuit_position()
        self.initialize_circuit(circuit, type)
        for t in range(rounds):
            self.depolarize_all(circuit)
            self.syndrome_measurement(circuit)
            if t == 0:
                self.add_detectors_initial(circuit, t, type)
            else:
                self.add_detectors(circuit, t)
        if if_measure:
            self.logical_measurement(circuit, type, rounds)
        return circuit

    def grow_code(self, circuit: stim.Circuit, round_start: int, round_end: int, m_new: int, n_new: int, postselection=None):
        old_N = self.total_qubit_number
        old_check_list = self.check_list.copy()
        old_m = self.m
        old_n = self.n
        self.reset_indices_for_growth(m_new, n_new)
        new_N = self.total_qubit_number
        new_data_idx_list = []
        new_check_idx_list = []
        for pos in self.data_dict:
            idx = self.data_dict[pos]
            if idx >= old_N:
                circuit.append("QUBIT_COORDS", idx, pos)
                new_data_idx_list.append(idx)
        for check in self.check_list:
            idx = check['idx']
            if idx in range(old_N, new_N):
                circuit.append("QUBIT_COORDS", idx, check['pos'])
                new_check_idx_list.append(idx)
        new_data_X_idx_list = [self.data_dict[pos] for pos in self.data_dict if pos[0] > 2 * (old_m - 1)]
        circuit.append("R", new_data_idx_list + new_check_idx_list)
        circuit.append("H", new_data_X_idx_list)
        circuit.append("DEPOLARIZE1", new_data_X_idx_list, self.error_rate)

        circuit.append('TICK')

        self.depolarize_all(circuit)
        self.syndrome_measurement(circuit)
        self.add_detectors_after_growth(circuit, old_check_list, old_m, old_n, round_start, postselection=postselection)

        for t in range(round_start+1, round_end):
            self.depolarize_all(circuit)
            self.syndrome_measurement(circuit)
            self.add_detectors(circuit, t, postselection=postselection)

        return circuit

    def S_state_preserving(self, rounds: int = 10):
        circuit = self.encoding(gate=['H', 'S'])
        for round in range(1, rounds):
            self.syndrome_measurement(circuit)
            self.add_detectors(circuit, round)
        self.Y_measurement_noiseless(circuit)
        self.syndrome_measurement(circuit, error_rate=0)
        self.add_detectors(circuit, rounds, rec_shift=1)
        return circuit

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

    def S_state_preserving_with_growth(self, T, rounds):
        circuit = self.encoding(gate=['H', 'S'])
        if rounds < T:
            for round in range(1, rounds):
                self.syndrome_measurement(circuit)
                self.add_detectors(circuit, round)
        else:
            for round in range(1, T):
                self.syndrome_measurement(circuit)
                self.add_detectors(circuit, round)
            circuit = self.grow_code(circuit, T, rounds, self.m + 2, self.n + 2, if_measure=False)
        self.Y_measurement_noiseless(circuit)
        self.syndrome_measurement(circuit, error_rate=0)
        self.add_detectors(circuit, rounds, rec_shift=1)
        return circuit