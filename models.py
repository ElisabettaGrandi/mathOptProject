import gurobipy as gp
from gurobipy import GRB

def build_graph(data):
    nodes = []
    node_regions = {}
    service_durations = {}
    time_windows = {}
    visit_requirements = {} # caregivers_count, skill_min, skill_max
    
    # Nodo Deposito
    nodes.append(("Center", 1))
    nodes.append(("Center", 2))
    node_regions[("Center", 1)] = data["region_mapping"]["Center"]
    node_regions[("Center", 2)] = data["region_mapping"]["Center"]
    
    # Nodi Paziente
    for p in data["patients"]:
        p_name = f"P_{p['id']}"
        region = p["region"]
        for v in p["visits"]:
            v_node = (p_name, v["visit_num"])
            nodes.append(v_node)
            node_regions[v_node] = region
            service_durations[v_node] = v["duration"]
            time_windows[v_node] = (v["start_tw"], v["end_tw"])
            visit_requirements[v_node] = {
                "count": v["caregivers_count"],
                "min": v["skill_requirements"]["min"],
                "max": v["skill_requirements"]["max"]
            }
            
    # Nodi Traghetto (Espansione in base a orari reali)
    ferry_nodes = []
    ferry_durations = {}
    for (orig, dest), f_data in data["ferry_schedules"].items():
        duration = f_data["duration"]
        for dep in f_data["departures"]:
            f_node = (f"{orig}->{dest}", dep) # -> per tenere duple anche i nodi per i ferry
            ferry_nodes.append(f_node)
            node_regions[f_node] = orig # La regione di partenza del traghetto
            ferry_durations[f_node] = duration
            
    all_nodes = nodes + ferry_nodes
    
    # Calcolo Archi Validi (T_ivjz)
    valid_arcs = []
    travel_times = {}
    
    # Regole di connettività semplificate dell'Appendice A
    for u in all_nodes:
        for v in all_nodes:
            if u == v: continue
            if u == ("Center", 2) or v == ("Center", 1): continue
            
            u_loc, u_idx = u
            v_loc, v_idx = v
            
            #starting regions
            reg_u = node_regions[u]
            reg_v = node_regions[v]
            
            # Caso 1 & 2: Stessa Regione (Guida pura)
            if "->" not in u_loc and "->" not in v_loc and reg_u == reg_v: #se non c'è -> non è un ferry
                #u_loc e v_loc contengono già l1 ed l2 così come impostati nella driving matrix
                dt = data["driving_matrix"][(u_loc, v_loc)]
                
                # Controllo preliminare finestra temporale
                if v in time_windows:
                    u_dur = service_durations.get(u, 0)
                    u_start = time_windows.get(u, (0, 0))[0]
                    if u_start + u_dur + dt > time_windows[v][1]:
                        continue
                        
                valid_arcs.append((u, v))
                travel_times[(u, v)] = dt

            #Caso 3
            elif u_loc == "Center" and "->" in v_loc:
                if data["region_mapping"]["Center"] == v_loc.split("->")[0]: #controlla che la regione della partenza sia la stessa del centro
                    dt = data["driving_matrix"][("Center", v_loc.split("->")[0])] #estrae il dt dal center al porto di v
                    dep_time = v_idx 
                    
                    # Al deposito l'orario di partenza minimo (u_start) e la durata (u_dur) sono 0
                    u_start = time_windows.get(u, (0, 0))[0]
                    
                    if u_start + dt <= dep_time:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = dt
                
            # Caso 4: Da paziente a Traghetto (Regione di partenza comune)
            elif "->" not in u_loc and "->" in v_loc:
                if reg_u == v_loc.split("->")[0]: #paziente nella stessa regione del porto
                    dt = data["driving_matrix"][(u_loc, v_loc.split("->")[0])]
                    dep_time = v_idx
                    
                    u_dur = service_durations.get(u, 0)
                    u_start = time_windows.get(u, (0, 0))[0]
                    
                    if u_start + u_dur + dt <= dep_time:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = dt
                    
            #Caso 5 ferry-centro
            if "->" in u_loc and v_loc == "Center":
                if u_loc.split("->")[1] == data["region_mapping"]["Center"]: #arrivo del caregiver e center nella stessa regione
                    # Il tempo totale è la durata della navigazione + la guida dal porto al Centro
                    total_t = ferry_durations[u] + data["driving_matrix"][(u_loc.split("->")[1], "Center")]
                    
                    dep_time = u_idx  # Orario di partenza del traghetto
                    
                    # Filtro temporale sul rientro (opzionale ma utile): non deve sforare la chiusura del centro
                    if v in time_windows and dep_time + total_t > time_windows[v][1]:
                        continue
                        
                    valid_arcs.append((u, v))
                    travel_times[(u, v)] = total_t

            # Caso 6: Da Traghetto a paziente (Regione di arrivo comune)
            elif "->" in u_loc and "->" not in v_loc: 
                if u_loc.split("->")[1] == reg_v: #paziente nella stessa regione in cui il ferry sbarca
                    total_t = ferry_durations[u] + data["driving_matrix"][(u_loc.split("->")[1], v_loc)]
                    
                    dep_time = u_idx
                    
                    # Filtro temporale sulla finestra del paziente
                    if v in time_windows and dep_time + total_t > time_windows[v][1]:
                        continue
                        
                    valid_arcs.append((u, v))
                    travel_times[(u, v)] = total_t

            # CASO 7: Da Traghetto a Traghetto (Connessione tra tratte)
            elif "->" in u_loc and "->" in v_loc:                
                # Il traghetto 1 arriva dove parte il traghetto 2 (o nella stessa macro-regione)
                if u_loc.split("->")[1] == v_loc.split("->")[0]:
                    dep_time_u = u_idx
                    dep_time_v = v_idx
                    dur_u = ferry_durations[u]
                    
                    # Se il tempo di partenza di v è successivo all'arrivo di u
                    if dep_time_u + dur_u <= dep_time_v:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = 2000 #large costant, as said in appendix A

    return all_nodes, valid_arcs, travel_times, service_durations, time_windows, visit_requirements

def create_milp_model(data, subgraph_nodes=None):
    """
    Costruisce il modello MILP per l'HHCRSP con Traghetti.
    Se subgraph_nodes è fornito, filtra i nodi per la Phase I della Matheuristica.
    """
    # all_nodes: lista di tuple (ID_nodo, info)
    # Pazienti: ("P_1", 1) -> (ID, Numero_Visita)
    # Traghetti: ("F_1->2", departure_time) -> (Rotta, Orario_Partenza)
    # Depot: ("Center", 1) e ("Center", 2)
    all_nodes, valid_arcs, travel_times, service_durations, time_windows, visit_requirements = build_graph(data)
    
    if subgraph_nodes is not None:
        all_nodes = [n for n in all_nodes if n in subgraph_nodes]
        valid_arcs = [(u, v) for (u, v) in valid_arcs if u in subgraph_nodes and v in subgraph_nodes]
        
    model = gp.Model("Ferry_Model")
    model.Params.OutputFlag = 0 
    
    caregivers = data["caregivers"]
    
    # --- VARIABILI DECISIONALI ---
    # x[c, u, v]: binaria (Eq 21)
    x = model.addVars([(c["id"], u, v) for c in caregivers for (u, v) in valid_arcs], 
                      vtype=GRB.BINARY, name="x")
    
    # y[u]: continua, definita SOLO per i nodi paziente N^P (Eq 22)
    patient_nodes = [n for n in all_nodes if "P_" in str(n[0])]
    y = model.addVars(patient_nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="y")
    
    # t_start[c], t_end[c]: tempi inizio/fine turno (Eq 23, 24)
    t_start = model.addVars([c["id"] for c in caregivers], lb=0.0, vtype=GRB.CONTINUOUS, name="t_start")
    t_end = model.addVars([c["id"] for c in caregivers], lb=0.0, vtype=GRB.CONTINUOUS, name="t_end")
    
    # --- FUNZIONE OBIETTIVO (Eq 1) ---
    obj = gp.quicksum(c["priority"] * (t_end[c["id"]] - t_start[c["id"]]) for c in caregivers)
    model.setObjective(obj, GRB.MINIMIZE)
    
    # --- VINCOLI DI ROUTING (Eq 2 - 7) ---
    for c in caregivers:
        c_id = c["id"]
        # Uscita dal deposito iniziale (Eq 2)
        model.addConstr(gp.quicksum(x[c_id, ("Center", 1), v] for v in all_nodes if (("Center", 1), v) in valid_arcs) <= 1)
        
        # Conservazione del flusso deposito inizio/fine (Eq 3)
        model.addConstr(
            gp.quicksum(x[c_id, ("Center", 1), v] for v in all_nodes if (("Center", 1), v) in valid_arcs) ==
            gp.quicksum(x[c_id, u, ("Center", 2)] for u in all_nodes if (u, ("Center", 2)) in valid_arcs)
        )
        
        # Conservazione del flusso nei nodi intermedi (Eq 4)
        for n in all_nodes:
            if n in [("Center", 1), ("Center", 2)]: continue
            model.addConstr(
                gp.quicksum(x[c_id, u, n] for u in all_nodes if (u, n) in valid_arcs) ==
                gp.quicksum(x[c_id, n, v] for v in all_nodes if (n, v) in valid_arcs)
            )

    # Vincoli di assegnazione e skill matching (Eq 5, 6, 7)
    for n in patient_nodes:
        req = visit_requirements[n]
        
        # Copertura visite (Eq 5)
        model.addConstr(gp.quicksum(x[c["id"], u, n] for c in caregivers for u in all_nodes if (u, n) in valid_arcs) == req["count"])
        
        # Skill matching per qualifica (Eq 6 e 7)
        for q in ["nurse", "assistant", "health_aid"]:
            cg_of_q = [c["id"] for c in caregivers if c["qualification"] == q]
            q_sum = gp.quicksum(x[c_id, u, n] for c_id in cg_of_q for u in all_nodes if (u, n) in valid_arcs)
            
            if q in req["min"]:
                model.addConstr(q_sum >= req["min"][q])
            if q in req["max"]:
                model.addConstr(q_sum <= req["max"][q])

    # --- VINCOLI TEMPORALI E DI SCHEDULING (Eq 8 - 20) ---
    M = 1440 # Impostato a minuti totali in una giornata
    
    for c in caregivers:
        c_id = c["id"]
        
        # Collegamento t_start (Eq 8, 9)
        for v in all_nodes:
            if (("Center", 1), v) in valid_arcs:
                dt = travel_times[(("Center", 1), v)]
                if "P_" in str(v[0]): # Verso Paziente (Eq 8)
                    model.addConstr(t_start[c_id] <= y[v] - dt + M * (1 - x[c_id, ("Center", 1), v]))
                elif "Center" not in str(v[0]): # Verso Traghetto (v[1] è la partenza D_jz) (Eq 9)
                    model.addConstr(t_start[c_id] <= v[1] - dt + M * (1 - x[c_id, ("Center", 1), v]))
                    
        # Collegamento fine turno t_end (Eq 13, 14)
        for u in all_nodes:
            if (u, ("Center", 2)) in valid_arcs:
                dt = travel_times[(u, ("Center", 2))]
                if "P_" in str(u[0]): # Da Paziente (Eq 13)
                    u_dur = service_durations.get(u, 0)
                    model.addConstr(t_end[c_id] >= y[u] + u_dur + dt - M * (1 - x[c_id, u, ("Center", 2)]))
                elif "Center" not in str(u[0]): # Da Traghetto (u[1] è la partenza del traghetto D_iv) (Eq 14)
                    model.addConstr(t_end[c_id] >= u[1] + dt - M * (1 - x[c_id, u, ("Center", 2)]))
        
        # Disponibilità turni (Eq 18, 19, 20)
        model.addConstr(t_start[c_id] >= c["start_time"])
        model.addConstr(t_end[c_id] <= c["end_time"])
        model.addConstr(t_start[c_id] <= t_end[c_id])

    # Relazione temporale consecutiva (Eq 10, 11, 12)
    for (u, v) in valid_arcs:
        if u in [("Center", 1), ("Center", 2)] or v in [("Center", 1), ("Center", 2)]: continue
        dt = travel_times[(u, v)]
        
        is_u_patient = "P_" in str(u[0])
        is_v_patient = "P_" in str(v[0])
        
        for c in caregivers:
            c_id = c["id"]
            if is_u_patient and is_v_patient: # Paziente -> Paziente (Eq 10)
                u_dur = service_durations.get(u, 0)
                model.addConstr(y[v] >= y[u] + u_dur + dt - M * (1 - x[c_id, u, v]))
                
            elif is_u_patient and not is_v_patient: # Paziente -> Traghetto (Eq 11)
                u_dur = service_durations.get(u, 0)
                # v[1] rappresenta l'orario fisso di partenza del traghetto D_jz
                model.addConstr(y[u] <= v[1] - u_dur - dt + M * (1 - x[c_id, u, v]))
                
            elif not is_u_patient and is_v_patient: # Traghetto -> Paziente (Eq 12)
                # u[1] rappresenta la partenza del traghetto D_iv. 
                # dt include già la durata del traghetto (U_iv) + guida (H_lj)
                model.addConstr(y[v] >= u[1] + dt - M * (1 - x[c_id, u, v]))

    # Finestre temporali dei pazienti (Eq 15, 16)
    for n in patient_nodes:
        model.addConstr(y[n] >= time_windows[n][0])
        model.addConstr(y[n] <= time_windows[n][1])

    # Intervallo minimo visite consecutive stesso paziente (Eq 17)
    for n1 in patient_nodes:
        for n2 in patient_nodes:
            # Stesso paziente (n1[0] == n2[0]) e visita successiva (n2[1] == n1[1] + 1)
            if n1[0] == n2[0] and n2[1] == n1[1] + 1:
                u_dur = service_durations.get(n1, 0)
                model.addConstr(y[n2] >= y[n1] + u_dur + data["min_interval_consecutive_visits"])

    model.update()
    return model, x, y