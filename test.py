from data_generator import generate_airport_instance
from models import solve_IFS

def run_small_test():
    data = generate_airport_instance(num_aircraft=15, num_fixed_gates=6, seed=123)

    print("IFS Model")
    wd_ifs, sol_ifs = solve_IFS(data)
    print(f"-> IFS Result: {wd_ifs}\n")

if __name__ == "__main__":
    run_small_test()