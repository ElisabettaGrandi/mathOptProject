import time
from model import create_milp_model
from data_generator import get_dataset as get_rough_data
from data_from_model import filter_dataset_via_model as get_filtered_data
from matheuristic import solve_wps_matheuristic
def run_test():
    rough_data = get_rough_data("A", 5, 43)

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
