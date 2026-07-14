import random
import math

def to_min(hh, mm):
    return hh * 60 + mm

# Manteniamo le tuple native come chiavi (molto più comode per i dizionari in Python)
FERRY_SCHEDULES = {
    "A": {
        ("Molde", "Sekken"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(16,15), to_min(17,15), to_min(18,15)]},
        ("Sekken", "Molde"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(16,15), to_min(17,15), to_min(18,15)]}
    },
    "B": {
        ("Sandnessjøen", "Bjørn"): {"duration": 25, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(16,0)]},
        ("Bjørn", "Sandnessjøen"): {"duration": 25, "departures": [to_min(8,30), to_min(9,30), to_min(10,30), to_min(11,30), to_min(12,30), to_min(13,30), to_min(16,30)]},
        ("Bjørn", "Løkta"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(16,30)]},
        ("Løkta", "Bjørn"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(16,30)]},
        ("Sandnessjøen", "Løkta"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(16,0)]},
        ("Løkta", "Sandnessjøen"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(16,0)]}
    }
}

def get_dataset(group_type, num_patients, seed=42):
    """Genera e restituisce il dataset direttamente come dizionario Python in RAM"""
    random.seed(seed)
    
    if group_type == "A":
        regions, weights, center_region = ["Molde", "Sekken"], [0.65, 0.35], "Molde"
    else:
        regions, weights, center_region = ["Sandnessjøen", "Bjørn", "Løkta"], [0.50, 0.30, 0.20], "Sandnessjøen"
        
    patients = []
    total_caregiver_visits_needed = 0
    node_counter = 1
    
    for p_id in range(1, num_patients + 1):
        region = random.choices(regions, weights=weights)[0]
        num_visits = 1 if random.random() < 0.70 else 2
        
        p_visits = []
        last_end = None  # Memorizza l'orario della prima visita per la consecutività
        
        # Unico ciclo per gestire sia 1 che 2 visite senza duplicare il codice
        for v_num in range(1, num_visits + 1):
            duration = random.choice([15, 30, 45, 60])
            tw_size = random.choices([60, 120, 180], weights=[0.25, 0.50, 0.25])[0]
            
            # --- GESTIONE FINESTRE TEMPORALI (TW) ---
            if region == center_region:
                if num_visits == 1:
                    start_tw = random.randint(to_min(8, 23 if group_type == "A" else 18), to_min(16, 0))
                else:
                    if v_num == 1:
                        start_tw = random.randint(to_min(8, 23 if group_type == "A" else 18), to_min(13, 0))
                        last_end = start_tw + duration
                    else:
                        start_tw = random.randint(last_end + 120, to_min(16, 0))
            else:
                # Regole per pazienti sulle isole (Sekken / Bjørn / Løkta)
                ferry_to = FERRY_SCHEDULES[group_type][(center_region, region)]["duration"]
                ferry_from = FERRY_SCHEDULES[group_type][(region, center_region)]["duration"]
                
                earliest_start = to_min(8, 46 if group_type == "A" else 36) + ferry_to
                
                if num_visits == 1:
                    start_tw = random.randint(earliest_start, to_min(16, 0) - ferry_from)
                else:
                    if v_num == 1:
                        start_tw = random.randint(earliest_start, to_min(13, 0) - ferry_from)
                        last_end = start_tw + duration
                    else:
                        start_tw = random.randint(last_end + 120, to_min(16, 0) - ferry_from)
            
            cg_count = 1 if random.random() < 0.70 else 2
            total_caregiver_visits_needed += cg_count
            
            # Skill matching (regole del paper)
            # Skill matching corretto e coerente (Evita conflitti min/max in model.py)
            req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, 
                          "max": {"nurse": 0, "assistant": 0, "health_aid": 0}}
            
            if cg_count == 1:
                r = random.random()
                if r < 0.20: 
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 0, "health_aid": 0}}
                elif r < 0.40: 
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 0}}
                elif r < 0.60: 
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 0, "health_aid": 1}}
                elif r < 0.80: 
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 1, "health_aid": 0}}
                else:          
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 1}}
            else: # cg_count == 2
                r = random.random()
                if r < 0.10: 
                    req_skills = {"min": {"nurse": 2, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 0, "health_aid": 0}}
                elif r < 0.20: 
                    req_skills = {"min": {"nurse": 0, "assistant": 2, "health_aid": 0}, "max": {"nurse": 0, "assistant": 2, "health_aid": 0}}
                elif r < 0.50: 
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 1, "health_aid": 0}}
                elif r < 0.80: 
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 1, "assistant": 2, "health_aid": 1}}
                else:          
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 1, "health_aid": 2}}
            p_visits.append({
                "visit_num": v_num,
                "node_id": node_counter,
                "duration": duration,
                "start_tw": start_tw,
                "end_tw": start_tw + tw_size,
                "caregivers_count": cg_count,
                "skill_requirements": req_skills
            })
            node_counter += 1
            
        patients.append({"id": p_id, "region": region, "visits": p_visits})

    num_caregivers = math.ceil(total_caregiver_visits_needed / 7)
    max_simultaneous_needed = max([v["caregivers_count"] for p in patients for v in p["visits"]])
    num_caregivers = max(num_caregivers, max_simultaneous_needed, 6)
    caregivers = []
    qualifications = ["nurse", "assistant", "health_aid"]
    priorities = {"nurse": 3, "assistant": 2, "health_aid": 1}
    
    for c_id in range(1, num_caregivers + 1):
        qual = qualifications[(c_id - 1) % 3]
        working_shift = random.choice([
            {"start": to_min(8, 0), "end": to_min(18, 0)},
            {"start": to_min(9, 0), "end": to_min(19, 0)}
        ])
        caregivers.append({
            "id": c_id, "qualification": qual, "priority": priorities[qual],
            "start_time": working_shift["start"], "end_time": working_shift["end"]
        })

    # Matrice dei tempi con chiavi tuple nativa (l1, l2) invece di stringhe "l1,l2"
    ferry_ports = set()
    current_ferry_schedules = FERRY_SCHEDULES[group_type]
    
    for origin, destination in current_ferry_schedules.keys():
        ferry_ports.add(origin)
        ferry_ports.add(destination)

    region_mapping = {"Center": center_region}
    for p in patients:
        region_mapping[f"P_{p['id']}"] = p["region"]

    for port in ferry_ports:
        region_mapping[port] = port    
    
    locations = ["Center"] + [f"P_{p['id']}" for p in patients] + list(ferry_ports)
    driving_matrix = {}
    avg_dt = 15 if group_type == "A" else 10
    for l1 in locations:
        for l2 in locations:
            reg1 = region_mapping[l1]
            reg2 = region_mapping[l2]
            if reg1 == reg2:  # stessa regione
                if l1 == l2:
                    driving_matrix[(l1, l2)] = 0
                else:
                    val = max(1, min(23 if group_type == "A" else 18, int(random.gauss(avg_dt, 4))))
                    driving_matrix[(l1, l2)] = val

    return {
        "instance_name": f"{group_type}-{num_patients}-{num_caregivers}-{total_caregiver_visits_needed}",
        "group_type": group_type,
        "region_mapping": region_mapping,
        "ferry_schedules": FERRY_SCHEDULES[group_type],
        "caregivers": caregivers,
        "patients": patients,
        "driving_matrix": driving_matrix,
        "min_interval_consecutive_visits": 120
    }