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