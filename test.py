import time
from model import create_milp_model
from data_generator import get_dataset as get_rough_data
from data_from_model import filter_dataset_via_model as get_filtered_data
from matheuristic import solve_wps_matheuristic
<<<<<<< HEAD
from data_try import get_dataset as get_dataset_try
def run_model_test():
    #data = get_dataset("A",13)
    data = data = get_dataset_try("A",30) 
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
=======
def run_test():
    rough_data = get_rough_data("A", 5, 43)
>>>>>>> 5252011b3e39c49a426147f8178ca43589f2a41f

    data = get_filtered_data(rough_data)

    if not data or len(data["patients"]) == 0:
        print("ERROR: Dataset not feasible!")
        return

    print("MILP Model\n")
    milp_model, x, y = create_milp_model(data)
    milp_model.Params.TimeLimit = 1800 # time limit di mezz'ora
    milp_model.Params.OutputFlag = 1
    start_time = time.time()
    milp_model.optimize()
    milp_time = time.time() - start_time

    if milp_model.SolCount > 0:
        print(f"MILP RESULTS Optimum found: {milp_model.ObjVal} Time elapsed: {milp_time:.2f}s")
    else:
        print(f"Cannot resolve MILP. Status: {milp_model.Status}")

    print("WPS Matheuristic\n")
    wps_obj, wps_time = solve_wps_matheuristic(data)
    print(f"\nWPS RESULTS Optimum found: {wps_obj}, Time elapsed: {wps_time:.2f}s")

    print("PS Matheuristic\n")
    ps_obj, ps_time = solve_wps_matheuristic(data, use_wps=False)
    print(f"PS RESULTS Optimum found: {ps_obj}, Time elapsed: {ps_time:.2f}s")

if __name__ == "__main__":
    run_test()
