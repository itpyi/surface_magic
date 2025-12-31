import numpy as np

GATE_I = np.identity(2)
GATE_Z = np.array([[1, 0], [0, -1]])
GATE_H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
GATE_X = np.array([[0, 1], [1, 0]])
GATE_S = np.array([[1, 0], [0, 1j]])
GATE_S_DAG = np.array([[1, 0], [0, -1j]])
GATE_T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])
GATE_T_DAG = np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]])
CTRL0 = np.array([[1, 0], [0, 0]])
CTRL1 = np.array([[0, 0], [0, 1]])
GATE_CZ = np.tensordot(CTRL0, GATE_I, 0) + np.tensordot(CTRL1, GATE_Z, 0)

def add_qubit(ket, ket_add):
    ket_new = np.tensordot(ket, ket_add, 0)
    return ket_new

def gate_on_site(gate, site, ket):
    if isinstance(site, int):
        site = [site]
    n = len(site)
    N = len(ket.shape)
    gate_ind = [2 * i + 1 for i in range(n)]

    gate_ket = np.tensordot(ket, gate, (site, gate_ind))
    new_ind = []
    ind = 0
    for i in range(N):
        if i in site:
            new_ind.append(N - n + site.index(i))
            ind += 1
        else:
            new_ind.append(i - ind)
    gate_ket = np.transpose(gate_ket, new_ind)
    return gate_ket

def tensor_product(operators):
    op = operators[0]
    for i in range(1,len(operators)):
        op = add_qubit(op,operators[i])
    return op

def rearrange_qubits(ket, sites_old, sites_new):
    N = len(ket.shape)
    new_ind = [] 
    for i in range(N):
        if i in sites_old:
            new_ind.append(sites_new[sites_old.index(i)])
        else:
            new_ind.append(i)
    ket = np.transpose(ket, new_ind)
    return ket

def swap_qubits(ket, site1, site2):
    return rearrange_qubits(ket, [site1, site2], [site2, site1])


def rotation_Z(theta):
    gate = np.array([[1,0],[0,np.exp(-1j*theta)]])
    return gate

def rotation_X(theta):
    gate = rotation_Z(theta)
    gate = np.matmul(GATE_H, gate)
    gate = np.matmul(gate, GATE_H)
    return gate

def norm(ket):
    return np.sqrt(np.sum(np.abs(ket)**2))

def qrm_initialization():
    # initialize a logical + state of the QRM code
    Xbasis = np.array([1, 1]) / np.sqrt(2)
    ket = tensor_product([Xbasis]*15)
    Z_stabilizer = tensor_product([GATE_Z]*4)
    Id = tensor_product([GATE_I]*4)
    Z_stabilizer_proj = (Id + Z_stabilizer) / np.sqrt(2) # ensure normalization
    Z_check_list = [
        [ 1, 3, 5, 7],
        [ 3, 2, 7, 6],
        [ 2, 6,14,10],
        [ 6,14,12, 4],
        [13,12, 4, 5],
        [12, 8, 9,13],
        [ 8, 9,10,11],
        [ 9, 1,11, 3],
        [ 5, 7,13,15],
        [10,11,15,14],
    ]
    for check in Z_check_list:
        check = [c - 1 for c in check]
        ket = gate_on_site(Z_stabilizer_proj, check, ket)

    return ket

def transversal_gate(gate, ket):
    for i in range(15):
        ket = gate_on_site(gate, i, ket)
    return ket

def noise_layer(ket, p, type):
    for i in range(15):
        theta = 0
        if not p == 0:
            sigma = np.sqrt(-2*np.log(1-2*p))
            theta = np.random.normal(0, sigma)
        if type == 'X':
            gate = rotation_X(theta)
        elif type == 'Z':
            gate = rotation_Z(theta)
        else:
            raise ValueError("Unknown noise type")
        ket = gate_on_site(gate, i, ket)
    return ket

def X_measurement_postselected(ket):
    X_stabilizer = tensor_product([GATE_X]*8)
    Id = tensor_product([GATE_I]*8)
    X_stabilizer_proj = (Id+X_stabilizer)/2

    X_logical = tensor_product([GATE_X]*7)
    Id = tensor_product([GATE_I]*7)
    X_logical_proj = (Id+X_logical)/2

    X_check_list = [
        [1,3,5,7,9,11,13,15],
        [2,3,6,7,10,11,14,15],
        [4,5,6,7,12,13,14,15],
        [8,9,10,11,12,13,14,15]
    ]

    for check in X_check_list:
        check = [c - 1 for c in check]
        ket = gate_on_site(X_stabilizer_proj, check, ket)
    
    ps_rate = norm(ket)
    dscd_rate = 1 - ps_rate

    ket = gate_on_site(X_logical_proj, [i for i in range(7)], ket)

    err_rate = 1 - norm(ket) / ps_rate if ps_rate > 0 else 0

    return dscd_rate, err_rate


def circuit_simulation(p, gate_type):
    gate = GATE_T
    gate_dag = GATE_T_DAG
    if gate_type == 'S':
        gate = GATE_S
        gate_dag = GATE_S_DAG
    
    ket = qrm_initialization()
    ket = transversal_gate(gate, ket)
    ket = noise_layer(ket, p, 'X')
    ket = transversal_gate(gate_dag, ket)
    # ket = noise_layer(ket, p, 'Z')

    dscd_rate, err_rate = X_measurement_postselected(ket)

    return dscd_rate, err_rate


# def fidelity(ket_0, ket_1):
#     fid = np.abs(np.sum(ket_0*ket_1.conj()))**2
#     return fid

# def weighted_avg_and_std(values, weights):
#     average = np.average(values, weights=weights)
#     # Fast and numerically precise:
#     variance = np.average((values-average)**2, weights=weights)
#     return (average, np.sqrt(variance))

def experiment(N, p, type):
    dscd_rate_list, err_rate_list = [], []
    for i in range(N):
        dscd_rate, err_rate = circuit_simulation(p, type)
        dscd_rate_list.append(dscd_rate)
        err_rate_list.append(err_rate)

    dscd_rate = np.mean(dscd_rate_list)
    err_rate = np.mean(err_rate_list)
    err_var = np.var(err_rate_list)

    return dscd_rate, err_rate, err_var

