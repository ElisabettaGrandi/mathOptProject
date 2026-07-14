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
        if "->" in str(n[0]): #nodo ferry
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
        # Eq (28): w* = 1 - |x_inc - x_lp|[cite: 1]
        w_star[key] = 1.0 - abs(val_inc - val_lp)
        
    w_min = min(w_star.values()) if w_star else 0.0
    w_max = max(w_star.values()) if w_star else 1.0
    diff = w_max - w_min
    
    for key, ws in w_star.items():
        # Eq (29): Discretizzazione a Z valori[cite: 1]
        if diff > 1e-6:
            w_disc = (Z + 1) - math.ceil(((ws - w_min) * (Z - 1)) / diff)
        else:
            w_disc = 1
            
        # Eq (30): Sistema di discretizzazione a 3 valori[cite: 1]
        if 1 <= w_disc <= t2:
            weights[key] = 1
        elif t2 < w_disc <= t3:
            weights[key] = int(Z / 2) # 5[cite: 1]
        else:
            weights[key] = Z # 10[cite: 1]
            
    return weights

def solve_wps_matheuristic(data, alpha=0.50, beta=3, time_limit=3600, use_wps=True):
    start_time = time.time()
    all_nodes, valid_arcs, travel_times, _, _, _ = build_graph(data)
    
    ordered_patients = get_ordered_patient_nodes(data, all_nodes)
    num_p_visits = len(ordered_patients)
    
    n_initial = max(1, int(alpha * num_p_visits))
    current_patients = ordered_patients[:n_initial]
    
    print(f"--- FASE I: Costruzione Soluzione Feasibile ({len(current_patients)}/{num_p_visits} visite) ---")
    
    active_regions = list(set(data["region_mapping"][p[0]] for p in current_patients))
    ferry_nodes = filter_ferry_nodes(data, active_regions, all_nodes)
    
    subgraph_nodes = [("Center", 1), ("Center", 2)] + current_patients + ferry_nodes
    
    # primo problema ristretto
    model, x, y = create_milp_model(data, subgraph_nodes)
    model.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
    model.optimize()
    
    if model.Status not in [GRB.OPTIMAL, GRB.SUBOPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        print("Infeffibile all'inizializzazione della Fase I.")
        return None, None
        
    # Salva l'incumbent corrente (x_bar)[cite: 1]
    x_bar = {k: v.X for k, v in x.items() if v.X > 0.5}
    
    # Iterazioni di espansione (Fase I)[cite: 1]
    idx = n_initial
    while idx < num_p_visits:
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
            
        # Aggiungiamo beta pazienti[cite: 1]
        next_idx = min(idx + beta, num_p_visits)
        new_patients = ordered_patients[idx:next_idx]
        current_patients.extend(new_patients)
        idx = next_idx
        
        print(f"Espansione Grafo: {len(current_patients)}/{num_p_visits} visite...")
        
        active_regions = list(set(data["region_mapping"][p[0]] for p in current_patients))
        ferry_nodes = filter_ferry_nodes(data, active_regions, all_nodes)
        subgraph_nodes = [("Center", 1), ("Center", 2)] + current_patients + ferry_nodes
        
        # nuovo modello ristretto
        model, x, y = create_milp_model(data, subgraph_nodes)
        
        # rilassamento lineare per calcolare i pesi
        x_lp = {}
        if use_wps:
            lp_model = model.relax()
            lp_model.optimize()
            if lp_model.Status == GRB.OPTIMAL:
                x_lp = {lp_model.getVarByName(v.VarName).VarName: lp_model.getVarByName(v.VarName).X for v in model.getVars() if "x[" in v.VarName}
        
        # Sostituzione della Funzione Obiettivo con Hamming Distance (Eq 25)[cite: 1]
        # Recuperiamo i nomi delle variabili per mappare l'incumbent precedente
        var_map = {v.VarName: v for v in model.getVars() if "x[" in v.VarName}
        
        # Calcolo dei pesi[cite: 1]
        weights = {}
        if use_wps and x_lp:
            # Adatta le chiavi per l'incumbent x_bar
            x_bar_named = {}
            for (c, u, v) in x_bar.keys():
                name = f"x[{c},{u},{v}]".replace(" ", "")
                x_bar_named[name] = 1.0
            weights = compute_wps_weights(var_map, x_bar_named, x_lp)
        else:
            weights = {k: 1 for k in var_map.keys()} # Classica Proximity Search[cite: 1]
            
        # Definiamo l'obiettivo di Hamming Distance[cite: 1]
        hamming_obj = gp.quicksum(
            weights[v_name] * (1 - var_map[v_name]) if v_name in [f"x[{c},{u},{v}]".replace(" ", "") for (c,u,v) in x_bar.keys()]
            else weights[v_name] * var_map[v_name]
            for v_name in var_map.keys()
        )
        model.setObjective(hamming_obj, GRB.MINIMIZE)
        
        # Risolvi fino a trovare una soluzione fattibile (Solution Limit = 1)[cite: 1]
        model.Params.SolutionLimit = 1
        model.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
        model.optimize()
        
        if model.SolCount == 0:
            print("Espansione Fallita: Nessuna soluzione trovata.")
            return None, None
            
        # Aggiorna l'incumbent x_bar[cite: 1]
        x_bar = {}
        for v in model.getVars():
            if "x[" in v.VarName and v.X > 0.5:
                # Eseguiamo il parsing del nome variabile per estrarre la tupla originale
                parts = v.VarName[2:-1].split(",")
                # Esempio: x[2,('Center',1),('P_1',1)]
                # Ricostruzione sicura delle tuple:
                c_id = int(parts[0])
                u_node = eval(",".join(parts[1:3]))
                v_node = eval(",".join(parts[3:]))
                x_bar[(c_id, u_node, v_node)] = 1.0

    print("--- FASE I Completata con successo! Soluzione iniziale trovata. ---")
    
    # --- FASE II: Solution Refinement ---[cite: 1]
    print("--- FASE II: Raffinamento Soluzione ---")
    
    # Creiamo il modello completo[cite: 1]
    model_full, x_full, y_full = create_milp_model(data, subgraph_nodes=None)
    
    # 1. Valutiamo il costo della soluzione di partenza f(x_bar)[cite: 1]
    for (c, u, v), val in x_bar.items():
        if (c, u, v) in x_full:
            x_full[c, u, v].Start = 1.0
            
    model_full.optimize()
    if model_full.SolCount == 0:
        print("Errore nel ripristinare la soluzione della Fase I nel modello completo.")
        return None, None
        
    best_cost = model_full.ObjVal
    best_sol_x = {k: v.X for k, v in x_full.items() if v.X > 0.5}
    print(f"Costo Soluzione Iniziale: {best_cost}")
    
    # Calcoliamo l'LP Relaxation del modello completo una sola volta (Phase II, Algorithm 2)[cite: 1]
    x_lp_full = {}
    if use_wps:
        lp_full = model_full.relax()
        lp_full.optimize()
        if lp_full.Status == GRB.OPTIMAL:
            x_lp_full = {v.VarName: v.X for v in lp_full.getVars() if "x[" in v.VarName}

    # Iterazioni di ottimizzazione locale con Proximity Search[cite: 1]
    iteration = 1
    theta = 1.0 # Come specificato nel paper, theta = 1 min[cite: 1]
    
    while True:
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break
            
        # Nuovo modello per la ricerca Hamming locale[cite: 1]
        model_it, x_it, y_it = create_milp_model(data, subgraph_nodes=None)
        
        # Aggiungiamo il vincolo di Cut-off (Eq 27): f(x) <= f(x_bar) - theta[cite: 1]
        orig_obj = gp.quicksum(c["priority"] * (model_it.getVarByName(f"t_end[{c['id']}]") - model_it.getVarByName(f"t_start[{c['id']}]")) for c in data["caregivers"])
        model_it.addConstr(orig_obj <= best_cost - theta, name="cutoff")
        
        # Mappatura variabili e calcolo pesi[cite: 1]
        var_map = {v.VarName: v for v in model_it.getVars() if "x[" in v.VarName}
        
        best_sol_named = {}
        for (c, u, v) in best_sol_x.keys():
            name = f"x[{c},{u},{v}]".replace(" ", "")
            best_sol_named[name] = 1.0
            
        if use_wps and x_lp_full:
            weights = compute_wps_weights(var_map, best_sol_named, x_lp_full)
        else:
            weights = {k: 1 for k in var_map.keys()}
            
        # Funzione obiettivo di Hamming Distance (Eq 26)[cite: 1]
        hamming_obj = gp.quicksum(
            weights[v_name] * (1 - var_map[v_name]) if v_name in best_sol_named
            else weights[v_name] * var_map[v_name]
            for v_name in var_map.keys()
        )
        model_it.setObjective(hamming_obj, GRB.MINIMIZE)
        
        # Risolvi fino a trovare un miglioramento[cite: 1]
        model_it.Params.SolutionLimit = 1
        model_it.Params.TimeLimit = max(10, time_limit - (time.time() - start_time))
        model_it.optimize()
        
        if model_it.SolCount > 0:
            # Calcoliamo il costo effettivo della nuova soluzione
            # Valutiamo fissando le variabili intere
            best_sol_x = {k: v.X for k, v in x_it.items() if v.X > 0.5}
            
            # Per ottenere il costo preciso, valutiamo con il modello principale
            model_eval, x_ev, y_ev = create_milp_model(data, subgraph_nodes=None)
            for k, val in best_sol_x.items():
                x_ev[k].Start = 1.0
            model_eval.optimize()
            
            best_cost = model_eval.ObjVal
            print(f"Iterazione {iteration}: Nuovo Ottimo Locale Trovato! Costo = {best_cost}")
            iteration += 1
        else:
            print("Nessun ulteriore miglioramento trovato o limite raggiunto.")
            break
            
    total_duration = time.time() - start_time
    return best_cost, total_duration