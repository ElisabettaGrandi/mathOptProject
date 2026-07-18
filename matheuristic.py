import time
import math
import gurobipy as gp
from gurobipy import GRB
from model import build_graph, create_milp_model

def get_ordered_patient_nodes(data, all_nodes):
    center_region = data["region_mapping"]["Center"]
    patient_nodes = [n for n in all_nodes if "P_" in str(n[0])]
    
    by_region = {} # pazienti per regione
    for n in patient_nodes:
        p_id = n[0] 
        region = data["region_mapping"][p_id]
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(n)
        
    # center per prima
    ordered_regions = [center_region] + [r for r in by_region if r != center_region]
    
    ordered_nodes = []
    for r in ordered_regions:
        if r in by_region:
            # prima id paziente e poi numero visita
            sorted_nodes = sorted(by_region[r], key=lambda x: (int(x[0].split("_")[1]), x[1]))
            ordered_nodes.extend(sorted_nodes)
            
    return ordered_nodes

def filter_ferry_nodes(data, active_patient_regions, all_nodes):
    active_regions = set(active_patient_regions) | {data["region_mapping"]["Center"]}
    ferry_nodes = []
    for n in all_nodes:
        if "->" in str(n[0]): # nodo ferry
            orig, dest = n[0].split("->")
            if orig in active_regions and dest in active_regions:
                ferry_nodes.append(n)
    return ferry_nodes

def compute_wps_weights(x_vars, x_incumbent, x_lp, Z=10, t2=2, t3=4):
    weights = {}
    w_star = {}
    
    for key in x_vars.keys():
        val_inc = x_incumbent.get(key, 0.0)
        val_lp = x_lp.get(key, 0.0)
        # eq 28
        w_star[key] = 1.0 - abs(val_inc - val_lp)
        
    w_min = min(w_star.values()) if w_star else 0.0
    w_max = max(w_star.values()) if w_star else 1.0
    diff = w_max - w_min
    
    for key, ws in w_star.items():
        # eq 29 
        if diff > 1e-6: # se la diff è 10^-6 significa che i pesi sono quasi identici
            w_disc = (Z + 1) - math.ceil(((ws - w_min) * (Z - 1)) / diff)
        else:
            w_disc = 1
            
        # eq 30
        if 1 <= w_disc <= t2:
            weights[key] = 1
        elif t2 < w_disc <= t3:
            weights[key] = int(Z / 2)
        else:
            weights[key] = Z 
            
    return weights

def solve_wps_matheuristic(data, alpha=0.50, beta=3, time_limit=3600, use_wps=True):
    start_time = time.time()
    all_nodes, valid_arcs, travel_times, _, _, _, _= build_graph(data)
    
    ordered_patients = get_ordered_patient_nodes(data, all_nodes)
    num_p_visits = len(ordered_patients)
    
    n_initial = max(1, int(alpha * num_p_visits))
    current_patients = ordered_patients[:n_initial]
    
    print("PHASE I")
    
    active_regions = list(set(data["region_mapping"][p[0]] for p in current_patients))
    ferry_nodes = filter_ferry_nodes(data, active_regions, all_nodes)
    
    # [1]
    subgraph_nodes = [("Center", 1), ("Center", 2)] + current_patients + ferry_nodes
    
    # primo problema ristretto
    model, x, y = create_milp_model(data, subgraph_nodes)
    model.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
    model.Params.outputFlag = 1
    model.optimize()
    
    if model.Status not in [GRB.OPTIMAL, GRB.SUBOPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        print("Model infeasible.")
        return None, None
        
    
    print("------------PRIMO PROBLEMA RISTRETTO RISOLTO-------------")
    # soluzione ottima problema ristretto
    x_bar = {k: v.X for k, v in x.items() if v.X > 0.5}
    
    # espansione
    idx = n_initial # indice ultimo paziente inserito
    while idx < num_p_visits:
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
            
        # aggiunta beta pazienti
        next_idx = min(idx + beta, num_p_visits)
        new_patients = ordered_patients[idx:next_idx]
        current_patients.extend(new_patients)
        idx = next_idx
                
        # [7]
        active_regions = list(set(data["region_mapping"][p[0]] for p in current_patients))
        ferry_nodes = filter_ferry_nodes(data, active_regions, all_nodes)
        subgraph_nodes = [("Center", 1), ("Center", 2)] + current_patients + ferry_nodes
        
        # modello ristretto con grafo espanso
        model, x, y = create_milp_model(data, subgraph_nodes)
        
        # rilassamento lineare per calcolare i pesi
        x_lp = {}
        if use_wps:
            lp_model = model.relax()
            lp_model.Params.outputFlag = 1
            lp_model.optimize()
            if lp_model.Status == GRB.OPTIMAL:
                x_lp = {lp_model.getVarByName(v.VarName).VarName: lp_model.getVarByName(v.VarName).X for v in model.getVars() if "x[" in v.VarName}
                print("------------RILASSAMENTO LINEARE RISOLTO-------------")
        
        # map dell'ottimo (nome var, oggetto var)
        var_map = {v.VarName: v for v in model.getVars() if "x[" in v.VarName}
        
        # calcolo dei pesi
        weights = {}
        if use_wps and x_lp:
            # adatta i nomi delle chiavi
            x_bar_named = {}
            for (c, u, v) in x_bar.keys():
                name = f"x[{c},{u},{v}]".replace(" ", "")
                x_bar_named[name] = 1.0
            weights = compute_wps_weights(var_map, x_bar_named, x_lp)
        else:
            weights = {k: 1 for k in var_map.keys()} # per la proximity search (non weighted)
            
        # nuovo obiettivo (Hamming distance) eq. 25
        hamming_obj = gp.quicksum(
            weights[v_name] * (1 - var_map[v_name]) if v_name in [f"x[{c},{u},{v}]".replace(" ", "") for (c,u,v) in x_bar.keys()]
            else weights[v_name] * var_map[v_name]
            for v_name in var_map.keys()
        )
        model.setObjective(hamming_obj, GRB.MINIMIZE)
        
        # risoluzione con il nuovo obiettivo [11]
        model.Params.SolutionLimit = 1
        model.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
        model.Params.outputFlag = 1
        model.optimize()
        
        if model.SolCount == 0:
            print("No solution found")
            return None, None
            
        # aggiorna ottimo
        x_bar = {}
        for v in model.getVars():
            if "x[" in v.VarName and v.X > 0.5:
                # estrazione della tupla
                # x[2,('Center',1),('P_1',1)] --> 2,('Center',1),('P_1',1)
                parts = v.VarName[2:-1].split(",") # [2],[('Center'],[1)],[('P_1'],[1)]
                # ricostruzione dei nodi
                c_id = int(parts[0])
                u_node = eval(",".join(parts[1:3]))
                v_node = eval(",".join(parts[3:]))
                x_bar[(c_id, u_node, v_node)] = 1.0
        print("------------OTTIMO AGGIORNATO-------------")

    print("PHASE I END")
    
    print("PHASE II")
    
    # modello completo
    model_full, x_full, y_full = create_milp_model(data, subgraph_nodes=None)
    
    # costo della soluzione di partenza x_bar [2]
    for key, var in x_full.items():
        if key in x_bar:
            var.lb = 1.0
            var.ub = 1.0
        else:
            var.lb = 0.0
            var.ub = 0.0
    
    model_full.Params.outputFlag = 1
    model_full.optimize()
    if model_full.SolCount == 0:
        model_full.computeIIS()
        model_full.write("modello_fallito.ilp")
        print("ERROR --> given solution not feasible")
        return None, None
    
    print("------------BEST INITIAL COST RISOLTO-------------")

    best_cost = model_full.ObjVal # f(xbar)
    best_sol_x = {k: v.X for k, v in x_full.items() if v.X > 0.5} # xbar per il modello completo
    print(f"Initial Cost: {best_cost}")

    for var in x_full.values():
        var.lb = 0.0
        var.ub = 1.0
    
    # rilassamento lineare [3]
    x_lp_full = {}
    if use_wps: # solo per wps perché per ps i pesi sono tutti uguali impostati a 1
        lp_full = model_full.relax()
        lp_full.Params.outputFlag = 1
        lp_full.optimize()
        if lp_full.Status == GRB.OPTIMAL:
            x_lp_full = {v.VarName: v.X for v in lp_full.getVars() if "x[" in v.VarName}
        print("------------RILASSAMENTO LINEARE P2 RISOLTO-------------")

    iteration = 1
    theta = 1.0 
    
    while True:
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
            
        # nuovo modello -> obj = Hamming + cut off constr
        model_it, x_it, y_it = create_milp_model(data, subgraph_nodes=None) # obj = Hamming e cut off constr
        
        # [7] eq 27
        orig_obj = gp.quicksum(c["priority"] * (model_it.getVarByName(f"t_end[{c['id']}]") - model_it.getVarByName(f"t_start[{c['id']}]")) for c in data["caregivers"]) #f(x)
        model_it.addConstr(orig_obj <= best_cost - theta, name="cutoff")
        
        # map dell'ottimo  
        var_map = {v.VarName: v for v in model_it.getVars() if "x[" in v.VarName}
        
        best_sol_named = {}
        for (c, u, v) in best_sol_x.keys():
            name = f"x[{c},{u},{v}]".replace(" ", "") # nome delle variabili in Gurobi
            best_sol_named[name] = 1.0
            
        # [5]
        if use_wps and x_lp_full:
            weights = compute_wps_weights(var_map, best_sol_named, x_lp_full)
        else:
            weights = {k: 1 for k in var_map.keys()}
            
        # nuova funzione obiettivo [6] eq 26
        hamming_obj = gp.quicksum(
            weights[v_name] * (1 - var_map[v_name]) if v_name in best_sol_named
            else weights[v_name] * var_map[v_name]
            for v_name in var_map.keys()
        )
        model_it.setObjective(hamming_obj, GRB.MINIMIZE)
        
        model_it.Params.SolutionLimit = 1 #appena trova un miglioramento si ferma
        model_it.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
        model_it.Params.outputFlag = 1
        model_it.optimize()
        print("------------MODEL_IT RISOLTO-------------")
        
        if model_it.SolCount > 0:
            # aggiornamento della soluzione
            best_sol_x = {k: v.X for k, v in x_it.items() if v.X > 0.5}
            
            # risoluzione del modello originale con la nuova soluzione per calcolarne il costo [11]
            model_eval, x_ev, y_ev = create_milp_model(data, subgraph_nodes=None)
            model_eval.Params.outputFlag = 1

            for key, var in x_ev.items():
                if key in best_sol_x:
                    var.lb = 1.0
                    var.ub = 1.0
                else:
                    var.lb = 0.0
                    var.ub = 0.0
            model_eval.optimize()
            
            print("------------OTTIMO AGGIORNATO-------------")
            
            best_cost = model_eval.ObjVal
            print(f"New solution's cost = {best_cost}")
            for var in x_ev.values():
                var.lb = 0.0
                var.ub = 1.0
            iteration += 1
        else:
            print("No better solution / time elapsed.")
            break
            
    total_duration = time.time() - start_time
    return best_cost, total_duration