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

    x = model.addVars(data['I'], data['K'], vtype=GRB.BINARY, name="x")

    obj = gb.LinExpr()

    for i in data['I']:
        p_to = sum(data['p'][j,i] for j in data['I'])
        p_from = sum(data['p'][i,j] for j in data['I'])
        p_non_transf = data['e'][i] + data['f'][i]

        for k in data['K_g'][i]:
            c = (d_aveto[k] * p_to + d_avefrom[k] * p_from + data['ed'][k] * p_non_transf)
            obj.addTerms(c, x[i,k])

    model.setObjective(obj,GRB.MINIMIZE)

    for i in data['I']:
        model.addConstr(gb.quicksum(x[i,k] for k in data['K_g'][i]) == 1, name = f"constr_3")

    for clique_idx, clique in enumerate(data['T_D']):
        for k in data['K_fixed']:
            model.addConstr(gb.quicksum(x[i,k] for i in clique) <= 1, name = f"constr_4")       

    for clique_idx, clique in enumerate(data['T_I']):
        for k in data['K_fixed']:
            model.addConstr(gb.quicksum(x[i,k] for i in clique) <= 1, name = f"constr_5") 

    model.addConstr(gb.quicksum(x[i,data['apron']] for i in data['I']) == data['NA'], name = f"constr_6")

    model.optimize()        

    if model.Status == GRB.OPTIMAL:
        print("IFS' optimum found")
        sol = {i: k for i in data['I'] for k in data['K'] if x[i,k].X > 0.5}

        real_wd = 0
        for i in data['I']:
            for j in data['I']:
                gate_i = sol[i]
                gate_j = sol[j]
                real_wd += data['p'][i,j] * data['d'][gate_i,gate_j]

        for i in data['I']:
            gate_i = sol[i]
            real_wd += (data['e'][i] + data['f'][i]) * data['ed'][gate_i]

        return real_wd, sol
    
    else:
        print("No solution found")
        return None, None

         







