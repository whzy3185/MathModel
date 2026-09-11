import numpy as np
from scipy.optimize import linprog

DT = 1/6
ETA = 0.9
E_MIN, E_MAX = 1200.0, 10800.0
STEP_MAX = 5000.0 * DT

def solve_net(price, net_power, soc0, terminal_soc=None):
    price = np.asarray(price, float)
    net = np.asarray(net_power, float)
    T = len(price)
    # x = [g, charge, discharge, E]
    n = 4 * T
    c = np.r_[price, np.zeros(3*T)]

    Aeq = np.zeros((T + (terminal_soc is not None), n))
    beq = np.zeros(Aeq.shape[0])
    for t in range(T):
        Aeq[t, 3*T+t] = 1
        Aeq[t, T+t] = -ETA
        Aeq[t, 2*T+t] = 1/ETA
        if t == 0:
            beq[t] = soc0
        else:
            Aeq[t, 3*T+t-1] = -1
    if terminal_soc is not None:
        Aeq[T, 4*T-1] = 1
        beq[T] = terminal_soc

    Aub = np.zeros((T, n))
    bub = -net * DT
    for t in range(T):
        Aub[t, t] = -1
        Aub[t, T+t] = 1
        Aub[t, 2*T+t] = -1

    bounds = ([(0, None)]*T +
              [(0, STEP_MAX)]*T +
              [(0, STEP_MAX)]*T +
              [(E_MIN, E_MAX)]*T)
    res = linprog(c, A_ub=Aub, b_ub=bub,
                  A_eq=Aeq, b_eq=beq,
                  bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    return res
