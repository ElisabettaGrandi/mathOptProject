import gurobipy as gp
from gurobipy import GRB

from data_generator import get_dataset  
from model import create_milp_model
from matheuristic import solve_wps_matheuristic

def run_model_test():
    data = get_dataset("A",13) 
    analyze_dataset(data)
    
    #print(f"  Total caregivers: {len(data['caregivers'])}")
    
    model, x, y = create_milp_model(data)
    
    model.Params.OutputFlag = 1
    model.Params.TimeLimit = 300 
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        print(f"\nOptimum FOUND, cost: {model.objVal:.2f}")
        
        print("\nROUTES:")
        for c in data["caregivers"]:
            c_id = c["id"]
            
            has_moved = False
            for edge in x.keys():
                if edge[0] == c_id and edge[1] == ("Center", 1) and x[edge].X > 0.5:
                    has_moved = True
                    break
            
            if not has_moved:
                print(f"  [Caregiver {c_id}] ({c['qualification']}): Not utilized.")
                continue
                
            current_node = ("Center", 1)
            route_sequence = [current_node]
            
            while current_node != ("Center", 2):
                found_next = False
                for edge in x.keys():
                    if edge[0] == c_id and edge[1] == current_node and x[edge].X > 0.5:
                        next_node = edge[2]
                        route_sequence.append(next_node)
                        current_node = next_node
                        found_next = True
                        break
                
                if not found_next:
                    print("Graph error")
                    break
            
            readable_route = " -> ".join([f"{n[0]}(v{n[1]})" if "Center" not in str(n[0]) else n[0] for n in route_sequence])
            print(f"  [Caregiver {c_id}] ({c['qualification']}): {readable_route}")

        print("\nSERVICES STARTS (y):")
        sorted_patient_nodes = sorted(list(y.keys()), key=lambda item: (item[0], item[1]))
        
        for p_node in sorted_patient_nodes:
            valore_minuti = y[p_node].X
            ore = int(valore_minuti // 60)
            minuti = int(valore_minuti % 60)
            print(f"  Paziente {p_node[0]} (Visita {p_node[1]}): minuto {valore_minuti:.1f} (Orario stimato ~ {ore:02d}:{minuti:02d})")
            
    elif model.status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD]:
        print("\nINFEASIBLE")
        model.computeIIS()
        model.write("constr.ilp")
        print("Check 'constr.ilp'")
        
    else:
        print(f"\nOptimization interrupted: {model.status}")

    # WPS
    print("WPS")
    wps_cost, wps_time = solve_wps_matheuristic(data, alpha=0.50, beta=3, time_limit=180, use_wps=True)
    
    # PS
    print("\nPS (No Weights)")
    ps_cost, ps_time = solve_wps_matheuristic(data, alpha=0.50, beta=3, time_limit=180, use_wps=False)
    
    print("\nRISULTATI")
    print(f"WPS - Costo Ottimo: {wps_cost} | Tempo di calcolo: {wps_time:.2f}s")
    print(f"PS  - Costo Ottimo: {ps_cost} | Tempo di calcolo: {ps_time:.2f}s")

def analyze_dataset(data):
    print(f"DATASET")
    
    print(f"\nGroup type: {data['group_type']}")
    print("Loc/Patient -> Region:")
    for loc, reg in list(data['region_mapping'].items())[:6]:
        print(f"  - {loc} -> {reg}")
    if len(data['region_mapping']) > 6:
        print(f"  - ... [{len(data['region_mapping']) - 6}]")

    print(f"\nCaregivers ({len(data['caregivers'])}):")
    for cg in data['caregivers']:
        print(f"  - ID {cg['id']:02d} | {cg['qualification']:<10} | pr: {cg['priority']} | Working Mins: {cg['start_time']} - {cg['end_time']}")

    print(f"\nPatients and visits:")
    for p in data['patients'][:10]:
        print(f"  - P_{p['id']} (Region: {p['region']})")
        for v in p['visits']:
            print(f"    ▪ Visit {v['visit_num']} | {v['duration']} min | TW: [{v['start_tw']}, {v['end_tw']}] | Req. cg: {v['caregivers_count']}")
            print(f"      Req. Skills -> Min: {v['skill_requirements']['min']} | Max: {v['skill_requirements']['max']}")

    print(f"\nFerry schedules:")
    for rotta, info in data['ferry_schedules'].items():
        print(f"  - {rotta[0]} -> {rotta[1]} | {info['duration']} min")
        print(f"    Dep: {info['departures']}")

    print(f"\nDriving Matrix:")
    sample_keys = list(data['driving_matrix'].keys())[:100]
    for k in sample_keys:
        print(f"  - {k} -> {data['driving_matrix'][k]} min")

if __name__ == "__main__":
    run_model_test()