def build_graph(data):
    nodes = []
    node_regions = {}
    service_durations = {}
    time_windows = {}
    visit_requirements = {} # caregivers_count, skill_min, skill_max
    
    # nodo center
    nodes.append(("Center", 1))
    nodes.append(("Center", 2))
    node_regions[("Center", 1)] = data["region_mapping"]["Center"]
    node_regions[("Center", 2)] = data["region_mapping"]["Center"]
    
    # nodi paziente
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
            
    # nodi ferry
    ferry_nodes = []
    ferry_durations = {}
    for (orig, dest), f_data in data["ferry_schedules"].items():
        duration = f_data["duration"]
        for dep in f_data["departures"]:
            f_node = (f"{orig}->{dest}", dep) # -> per tenere duple anche i nodi per i ferry
            ferry_nodes.append(f_node)
            node_regions[f_node] = orig # regione di partenza del traghetto
            ferry_durations[f_node] = duration
            
    all_nodes = nodes + ferry_nodes
    
    # archi validi
    valid_arcs = []
    travel_times = {}
    big_m_arcs = {}
    
    # regole appendice A
    for u in all_nodes:
        for v in all_nodes:
            if u == v: continue
            if u == ("Center", 2) or v == ("Center", 1): continue
            
            u_loc, u_idx = u
            v_loc, v_idx = v
            
            #starting regions
            reg_u = node_regions[u]
            reg_v = node_regions[v]

            u_start_tw, u_end_tw = time_windows.get(u, (480, 1020))
            v_start_tw, v_end_tw = time_windows.get(v, (480, 1020))
            u_dur = service_durations.get(u, 0)
            
            # casi 1 (nodo center - nodo visit --> stessa regione) e 2 (visit - visit --> stessa regione + controllo tw)
            if "->" not in u_loc and "->" not in v_loc and reg_u == reg_v: #se non c'è "->" non è un ferry
                #u_loc e v_loc contengono già l1 ed l2 così come impostati nella driving matrix
                dt = data["driving_matrix"][(u_loc, v_loc)]
                
                # controllo finestra temporale
                if v in time_windows:
                    if u_start_tw + u_dur + dt > time_windows[v][1]:
                        continue
                        
                valid_arcs.append((u, v))
                travel_times[(u, v)] = dt
                big_m_arcs[(u, v)] = max(10, u_end_tw + u_dur + dt - v_start_tw)

            # caso 3 (center - ferry --> partenza del ferry nella stessa regione del center)
            elif u_loc == "Center" and "->" in v_loc:
                if data["region_mapping"]["Center"] == v_loc.split("->")[0]: # controlla che la regione della partenza sia la stessa del centro
                    dt = data["driving_matrix"][("Center", v_loc.split("->")[0])] # estrae il dt dal center al porto di v
                    dep_time = v_idx 
                    
                    # al center l'orario di partenza minimo (u_start) e la durata (u_dur) sono 0                    
                    if u_start_tw + dt <= dep_time:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = dt
                        big_m_arcs[(u, v)] = max(10, u_end_tw + dt - dep_time)
                
            # caso 4 (visit - ferry --> paziente e partenza ferry stessa regione + controllo tempi per partenza ferry)
            elif "->" not in u_loc and "->" in v_loc:
                if reg_u == v_loc.split("->")[0]: # paziente nella stessa regione del porto
                    dt = data["driving_matrix"][(u_loc, v_loc.split("->")[0])]
                    dep_time = v_idx                    
                    if u_start_tw + u_dur + dt <= dep_time:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = dt
                        big_m_arcs[(u, v)] = max(10, u_end_tw + u_dur + dt - dep_time)
                    
            # caso 5 (ferry - center --> destinazione del ferry nella stessa regione del center)
            if "->" in u_loc and v_loc == "Center":
                if u_loc.split("->")[1] == data["region_mapping"]["Center"]: # arrivo del caregiver e center nella stessa regione
                    # il tempo totale è la durata della navigazione + la guida dal porto al center
                    total_t = ferry_durations[u] + data["driving_matrix"][(u_loc.split("->")[1], "Center")]
                    
                    dep_time = u_idx  # orario di partenza del traghetto
                    
                    # rientro: non deve sforare la chiusura del centro
                    if v in time_windows and dep_time + total_t > time_windows[v][1]:
                        continue
                        
                    valid_arcs.append((u, v))
                    travel_times[(u, v)] = total_t
                    big_m_arcs[(u, v)] = max(10, dep_time + total_t - v_start_tw)

            # caso 6 (ferry - visit --> destinazione del ferry nella stessa regione del paziente + controllo tempi di arrivo del ferry e visita)
            elif "->" in u_loc and "->" not in v_loc: 
                if u_loc.split("->")[1] == reg_v: # paziente nella stessa regione in cui il ferry sbarca
                    total_t = ferry_durations[u] + data["driving_matrix"][(u_loc.split("->")[1], v_loc)]
                    dep_time = u_idx
                    
                    # finestra del paziente
                    if v in time_windows and dep_time + total_t > time_windows[v][1]:
                        continue
                        
                    valid_arcs.append((u, v))
                    travel_times[(u, v)] = total_t
                    big_m_arcs[(u, v)] = max(10, dep_time + total_t - v_start_tw)

            # caso 7 (ferry - ferry --> partenza f1 != arrivo f2 + arrivo f1 = partenza f2 + controllo tempi)
            elif "->" in u_loc and "->" in v_loc:                
                # traghetto 1 arriva dove parte traghetto 2 
                if u_loc.split("->")[1] == v_loc.split("->")[0]:
                    dep_time_u = u_idx
                    dep_time_v = v_idx
                    dur_u = ferry_durations[u]
                    
                    # tempo di partenza di v è successivo all'arrivo di u
                    driving_between_ports = data["driving_matrix"].get((u_loc.split("->")[1], v_loc.split("->")[0]), 0)
                    if dep_time_u + dur_u + driving_between_ports <= dep_time_v:
                        valid_arcs.append((u, v))
                        travel_times[(u, v)] = 2000 #large constant (come detto nel paper)
                        big_m_arcs[(u, v)] = max(10, dep_time_u + dur_u + driving_between_ports - dep_time_v)

    return all_nodes, valid_arcs, travel_times, service_durations, time_windows, visit_requirements, big_m_arcs