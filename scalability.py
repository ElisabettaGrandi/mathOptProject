from datetime import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
from model import create_milp_model
from data_generator import get_dataset as get_rough_data
from updated_data_generator import get_dataset as get_rough_updated_data
from data_from_model import filter_dataset_via_model as get_filtered_data
from matheuristic import solve_wps_matheuristic
from gurobipy import GRB


def milp_time_callback(model, where):
    if where == GRB.Callback.MIPSOL:
        runtime = model.cbGet(GRB.Callback.RUNTIME)
        sol_count = model.cbGet(GRB.Callback.MIPSOL_SOLCNT)
        if sol_count == 0 or model._milp_t_first is None:
            model._milp_t_first = runtime
        model._milp_t_last = runtime



def run_scalability():
    sizes = [10, 15, 20]
    group_type = "A"
    seed = 50
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    csv_filename = f"scalability_results_{timestamp}_s={seed}.csv"
    png_filename = f"scalability_plots_{timestamp}_s={seed}.png"

    results = []

    for num_pat in sizes:
        print(f"Number of patients: {num_pat}")

        #rough_data = get_rough_data(group_type, num_pat, seed)
        rough_data = get_rough_updated_data(group_type, num_pat, seed)
        data = get_filtered_data(rough_data)

        print(f"\nSolving MILP")
        milp_model, x, y = create_milp_model(data)
        milp_model.Params.TimeLimit = 1800 # time limit di mezz'ora
        milp_model.Params.OutputFlag = 1
        milp_model._milp_t_first = None
        milp_model._milp_t_last = None

        start_time = time.time()
        milp_model.optimize(milp_time_callback)
        milp_time = time.time() - start_time

        if milp_model.SolCount > 0:
            milp_obj = milp_model.ObjVal
        else:
            milp_obj = None

        milp_t_first = round(milp_model._milp_t_first, 2) if milp_model._milp_t_first is not None else None
        milp_t_last = round(milp_model._milp_t_last, 2) if milp_model._milp_t_last is not None else None
        
        best_bound = milp_model.ObjBound if (milp_model.SolCount > 0 or milp_model.Status == 9) else None
        milp_gap = round(milp_model.MIPGap * 100, 2) if milp_model.SolCount > 0 else None

        print(f"\nSolving WPS")
        wps_obj, wps_time, wps_tf, wps_tb = solve_wps_matheuristic(data)

        wps_gap = None
        if wps_obj and best_bound and wps_obj != 0:
            wps_gap = round(abs((wps_obj - best_bound) / wps_obj) * 100, 2)

        print(f"\nSolving PS")
        ps_obj, ps_time, ps_tf, ps_tb = solve_wps_matheuristic(data, use_wps=False)

        ps_gap = None
        if ps_obj and best_bound and ps_obj != 0:
            ps_gap = round(abs((ps_obj - best_bound) / ps_obj) * 100, 2)

        results.append({
            "Patients": num_pat,
            "Caregivers": data["caregivers"],
            "MILP_Obj": milp_obj,
            "MILP_Gap_%": milp_gap,
            "MILP_T_First": milp_t_first,
            "MILP_T_Last": milp_t_last,
            "MILP_Time": round(milp_time, 2),
            "WPS_Obj": wps_obj,
            "WPS_Gap_%": wps_gap,
            "WPS_T_First": round(wps_tf, 2) if wps_tf else None,
            "WPS_T_Last": round(wps_tb, 2) if wps_tb else None,
            "WPS_Time": round(wps_time, 2),
            "PS_Obj": ps_obj,
            "PS_Gap_%": ps_gap,
            "PS_T_First": round(ps_tf, 2) if ps_tf else None,
            "PS_T_Last": round(ps_tb, 2) if ps_tb else None,
            "PS_Time": round(ps_time, 2)
        })
        
    df = pd.DataFrame(results)
    print("Scalability Analysis\n")
    print(df.to_string(index=False))

    df.to_csv(csv_filename, index=False)

    fig, (exePlot, objPlot) = plt.subplots(1, 2, figsize=(14, 6))

    exePlot.plot(df["Patients"], df["MILP_Time"], marker='o', color='crimson', label='MILP', linewidth=2)
    exePlot.plot(df["Patients"], df["WPS_Time"], marker='s', color='navy', label='WPS', linewidth=2)
    exePlot.plot(df["Patients"], df["PS_Time"], marker='^', color='darkorange', label='PS', linewidth=2)
    exePlot.set_title("Execution Time")
    exePlot.set_xlabel("Number of Patients")
    exePlot.set_ylabel("Time (seconds)")
    exePlot.grid(True, linestyle='--', alpha=0.7)
    exePlot.legend()

    df_plot_obj = df.dropna(subset=["WPS_Obj", "PS_Obj"])
    if not df_plot_obj.empty:
        if df["MILP_Obj"].notna().any():
            objPlot.plot(df["Patients"], df["MILP_Obj"], marker='o', color='crimson', label='MILP', linestyle='--')
        objPlot.plot(df["Patients"], df["WPS_Obj"], marker='s', color='navy', label='WPS')
        objPlot.plot(df["Patients"], df["PS_Obj"], marker='^', color='darkorange', label='PS')
    objPlot.set_title("Optimum value")
    objPlot.set_xlabel("Number of Patients")
    objPlot.set_ylabel("Optimum value")
    objPlot.grid(True, linestyle='--', alpha=0.7)
    objPlot.legend()

    plt.tight_layout()
    plt.savefig(png_filename, dpi=300)
    plt.show()

if __name__ == "__main__":
    run_scalability()
