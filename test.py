import gurobipy as gb
from gurobipy import GRB
import numpy as np
import time

def solve_IFS(data):

    num_gates = len(data['K'])
    d_aveto = {k: np.sum(data['d'][:,k]) / num_gates for k in data['K']}
    d_avefrom = {k: np.sum(data['d'][k,:]) / num_gates for k in data['K']}

    model = gb.Model("IFS")
    model.Params.OutputFlag = 1

    x = model.addvars(data['I'], data['K'], vtype=GRB.BINARY, name="x")

    obj = gb.LinExpr()
    for i in data['I']:
        p_to = sum(data['p'][j,i] for j in data['I'])
        p_from = sum(data['p'][i,j] for j in data['I'])
        p_non_transf = data['e'][i] + data['f'][i]

        for k in data['K_g'][i]:
            c = (d_aveto * p_to + d_avefrom * p_from + data['ed'][k] * p_non_transf)
            obj.addTerms(c, x[i,k])

    model.setObjective(obj,GRB.MINIMIZE)
            







