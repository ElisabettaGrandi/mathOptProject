import gurobipy as gp
from gurobipy import GRB

from graph import build_graph

def create_milp_model(data, subgraph_nodes=None):
    # all_nodes: lista di tuple (ID_nodo, info)
    # Pazienti: ("P_1", 1) -> (ID, Numero_Visita)
    # Traghetti: ("F_1->2", departure_time) -> (Rotta, Orario_Partenza)
    # Center: ("Center", 1) e ("Center", 2)

    all_nodes, valid_arcs, travel_times, service_durations, time_windows, visit_requirements, big_m_arcs = build_graph(data)

    valid_arcs = list(set(valid_arcs))
    all_nodes = list(set(all_nodes))
    
    if subgraph_nodes is not None:
        all_nodes = [n for n in all_nodes if n in subgraph_nodes]
        valid_arcs = [(u, v) for (u, v) in valid_arcs if u in subgraph_nodes and v in subgraph_nodes]
        
    model = gp.Model("Ferry_Model")
    model.Params.OutputFlag = 0 
    
    caregivers = data["caregivers"]
    
    # VARIABILI
    # x[c, u, v]: binaria 
    x = model.addVars([(c["id"], u, v) for c in caregivers for (u, v) in valid_arcs], 
                      vtype=GRB.BINARY, name="x")
    
    # y[u]: continua, definita per i nodi paziente N^P 
    patient_nodes = [n for n in all_nodes if "P_" in str(n[0])]
    y = model.addVars(patient_nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="y")
    
    # t_start[c], t_end[c]: tempi inizio/fine turno 
    t_start = model.addVars([c["id"] for c in caregivers], lb=0.0, vtype=GRB.CONTINUOUS, name="t_start")
    t_end = model.addVars([c["id"] for c in caregivers], lb=0.0, vtype=GRB.CONTINUOUS, name="t_end")
    
    x_bar = model.addVars(patient_nodes, vtype=GRB.BINARY, name="x_bar")

    # OBIETTIVO
    obj = (100000 * gp.quicksum(x_bar[n] for n in patient_nodes) 
        - gp.quicksum(c["priority"] * (t_end[c["id"]] - t_start[c["id"]]) for c in caregivers))
    model.setObjective(obj, GRB.MAXIMIZE)
    
    M_big = 1440 # minuti totali in una giornata
    # VINCOLI
    # eq 2-7
    for c in caregivers:
        c_id = c["id"]
        # (2) ensure that each caregiver departs from the starting node (0, 1) at most once
        model.addConstr(gp.quicksum(x[c_id, ("Center", 1), v] for v in all_nodes if (("Center", 1), v) in valid_arcs) <= 1)
        
        # (3) guarantee that each caregiver who departs from the starting node must return to the ending node (0, 2)
        model.addConstr(
            gp.quicksum(x[c_id, ("Center", 1), v] for v in all_nodes if (("Center", 1), v) in valid_arcs) ==
            gp.quicksum(x[c_id, u, ("Center", 2)] for u in all_nodes if (u, ("Center", 2)) in valid_arcs)
        )
        
        # (4) establish flow conservation: a caregiver entering either a patient node or a ferry node must also exit it
        for n in all_nodes:
            if n in [("Center", 1), ("Center", 2)]: continue
            model.addConstr(
                gp.quicksum(x[c_id, u, n] for u in all_nodes if (u, n) in valid_arcs) ==
                gp.quicksum(x[c_id, n, v] for v in all_nodes if (n, v) in valid_arcs)
            )

    for n in patient_nodes:
        req = visit_requirements[n]

        total_caregivers_at_node = gp.quicksum(x[c["id"], u, n] for c in caregivers for u in all_nodes if (u,n) in valid_arcs)

        # OLD      
        # (5) specify the exact number of caregivers assigned to each patient node
        # model.addConstr(gp.quicksum(x[c["id"], u, n] for c in caregivers for u in all_nodes if (u, n) in valid_arcs) == req["count"])
        
        # NEW
        # (5) relaxed with bigM
        model.addConstr(total_caregivers_at_node - req["count"] <= M_big * (1 - x_bar[n]))
        model.addConstr(req["count"] - total_caregivers_at_node <= M_big * (1 - x_bar[n]))

        # OLD
        # (6) ensure that the number of caregivers of each qualification assigned to a patient node meets the minimum requirement. In contrast, constraints (7) ensure that the
        # number of caregivers of each qualification assigned to a patient node does not exceed the allowable limit.
        # for q in ["nurse", "assistant", "health_aid"]:
        #    cg_of_q = [c["id"] for c in caregivers if c["qualification"] == q]
        #    q_sum = gp.quicksum(x[c_id, u, n] for c_id in cg_of_q for u in all_nodes if (u, n) in valid_arcs)
            
        #    if q in req["min"]:
        #       model.addConstr(q_sum >= req["min"][q])
        #   if q in req["max"]:
        #       model.addConstr(q_sum <= req["max"][q])

        # NEW
        # (6) and (7) relaxed
        for q in ["nurse", "assistant", "health_aid"]:
            cg_of_q = [c["id"] for c in caregivers if c["qualification"] == q]
            q_sum = gp.quicksum(x[c_id, u, n] for c_id in cg_of_q for u in all_nodes if (u, n) in valid_arcs)

            if q in req["min"]:
                model.addConstr(q_sum >= req["min"][q] - M_big * (1 - x_bar[n]))
            if q in req["max"]:
                model.addConstr(q_sum <= req["max"][q] + M_big * (1 - x_bar[n]))
            
    for c in caregivers:
        c_id = c["id"]
        
        # (8) ensure that when the first destination for a caregiver is a patient node, the caregiver’s departure time from the healthcare center is no later than the service
        # start time at that patient minus the arc traversal time
        for v in all_nodes:
            if (("Center", 1), v) in valid_arcs:
                dt = travel_times[(("Center", 1), v)]
                m_specific = big_m_arcs[(("Center", 1), v)]
                if "P_" in str(v[0]): # Verso Paziente (Eq 8)
                    model.addConstr(t_start[c_id] <= y[v] - dt + m_specific * (1 - x[c_id, ("Center", 1), v]))
                elif "Center" not in str(v[0]): # Verso Traghetto (v[1] è la partenza D_jz) (Eq 9)
                    model.addConstr(t_start[c_id] <= v[1] - dt + m_specific * (1 - x[c_id, ("Center", 1), v]))
                    
        # (13) ensure that when the origin node of the last traversed arc corresponds to a patient visit, the caregiver’s arrival at the healthcare center is no earlier than
        # the sum of the service start time, service duration, and arc traversal time
        # (14) guarantee that when the origin node of the last traversed arc corresponds to a ferry trip, the caregiver’s arrival at the healthcare center is no earlier than the sum of the ferry departure
        # time and arc traversal time
        for u in all_nodes:
            if (u, ("Center", 2)) in valid_arcs:
                dt = travel_times[(u, ("Center", 2))]
                m_specific = big_m_arcs[(u, ("Center", 2))]
                if "P_" in str(u[0]): # Da Paziente (Eq 13)
                    u_dur = service_durations.get(u, 0)
                    model.addConstr(t_end[c_id] >= y[u] + u_dur + dt - m_specific * (1 - x[c_id, u, ("Center", 2)]))
                elif "Center" not in str(u[0]): # Da Traghetto (u[1] è la partenza del traghetto D_iv) (Eq 14)
                    model.addConstr(t_end[c_id] >= u[1] + dt - m_specific * (1 - x[c_id, u, ("Center", 2)]))
        
        # (18)–(19) guarantee that the departure time from the healthcare center and the return time to 
        # the healthcare center for each caregiver are within the given caregiver’s time window
        model.addConstr(t_start[c_id] >= c["start_time"])
        model.addConstr(t_end[c_id] <= c["end_time"])
        # (20) ensure that the route starting time does not exceed the route ending time for each caregiver
        model.addConstr(t_start[c_id] <= t_end[c_id])

    for (u, v) in valid_arcs:
        if u in [("Center", 1), ("Center", 2)] or v in [("Center", 1), ("Center", 2)]: continue
        dt = travel_times[(u, v)]
        m_specific = big_m_arcs[(u, v)]
        
        is_u_patient = "P_" in str(u[0])
        is_v_patient = "P_" in str(v[0])
        
        for c in caregivers:
            c_id = c["id"]
            if is_u_patient and is_v_patient: 
                # (10) ensure that the service start time at node (𝑗, 𝑧) cannot be earlier than the
                # sum of the service start time at node (𝑖, 𝑣), the service duration at node (𝑖, 𝑣), and the arc traversal time 
                u_dur = service_durations.get(u, 0)
                model.addConstr(y[v] >= y[u] + u_dur + dt - m_specific * (1 - x[c_id, u, v]))
                
            elif is_u_patient and not is_v_patient: 
                # (11) guarantee that the service start time at the patient does not exceed the ferry departure time minus the
                # sum of the service duration and the arc traversal time
                u_dur = service_durations.get(u, 0)
                # v[1] orario fisso di partenza del traghetto D_jz
                model.addConstr(y[u] <= v[1] - u_dur - dt + m_specific * (1 - x[c_id, u, v]))
                
            elif not is_u_patient and is_v_patient: 
                # (12) ensure that the start service time at that patient is greater than or
                # equal to the sum of the ferry departure time and the arc traversal time
                # u[1] rappresenta la partenza del traghetto D_iv. 
                # dt include già la durata del traghetto (U_iv) + guida (H_lj)
                model.addConstr(y[v] >= u[1] + dt - m_specific * (1 - x[c_id, u, v]))

    # (15)–(16) ensure that each patient node is visited within its designated time window
    for n in patient_nodes:
        model.addConstr(y[n] >= time_windows[n][0])
        model.addConstr(y[n] <= time_windows[n][1])

    # (17) enforce the required interval between consecutive visits to each patient
    for n1 in patient_nodes:
        for n2 in patient_nodes:
            # Stesso paziente (n1[0] == n2[0]) e visita successiva (n2[1] == n1[1] + 1)
            if n1[0] == n2[0] and n2[1] == n1[1] + 1:
                u_dur = service_durations.get(n1, 0)
                # OLD
                # model.addConstr(y[n2] >= y[n1] + u_dur + data["min_interval_consecutive_visits"])
                # NEW
                model.addConstr(y[n2] >= y[n1] + u_dur + data["min_interval_consecutive_visits"] - M_big * (2 - x_bar[n1] - x_bar[n2]))
                
    model.update()
    return model, x, y, x_bar