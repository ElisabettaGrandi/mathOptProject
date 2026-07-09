from data_generator import generate_airport_instance
from models import solve_IFS

def run_small_test():
    data = generate_airport_instance(num_aircraft=15, num_fixed_gates=6, seed=123)