import random
import math

def to_min(hh, mm):
    return hh * 60 + mm

# definizione schedules dei ferry
FERRY_SCHEDULES = {
    "A": {
        ("Molde", "Sekken"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(14,15), to_min(15,15), to_min(16,15)]},
        ("Sekken", "Molde"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(14,15), to_min(15,15), to_min(16,15)]}
    },
    "B": {
        ("Sandnessjøen", "Bjørn"): {"duration": 25, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]},
        ("Bjørn", "Sandnessjøen"): {"duration": 25, "departures": [to_min(8,30), to_min(9,30), to_min(10,30), to_min(11,30), to_min(12,30), to_min(13,30), to_min(14,30), to_min(15,30), to_min(16,30)]},
        ("Bjørn", "Løkta"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(11,0), to_min(11,30), to_min(12,0), to_min(12,30), to_min(13,0), to_min(13,30), to_min(14,0), to_min(14,30), to_min(15,0), to_min(15,30), to_min(16,0), to_min(16,30)]},
        ("Løkta", "Bjørn"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(11,0), to_min(11,30), to_min(12,0), to_min(12,30), to_min(13,0), to_min(13,30), to_min(14,0), to_min(14,30), to_min(15,0), to_min(15,30), to_min(16,0), to_min(16,30)]},
        ("Sandnessjøen", "Løkta"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]},
        ("Løkta", "Sandnessjøen"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]}
    }
}

def get_dataset(group_type, num_patients, seed=43): #usati: 42, 
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
        
        for v_num in range(1, num_visits + 1):
            duration = random.choice([15, 30, 45, 60])
            tw_size = random.choices([60, 120, 180], weights=[0.25, 0.50, 0.25])[0]
            
            max_dt = 23 if group_type == "A" else 18

            if region == center_region:
            # caso in cui il paziente è nella regione centrale -> turno finisce max alle 16 - tempo di guida massimo per arrivare al center
                limite_pomeridiano_centro = to_min(16, 0) - max_dt
                
                if num_visits == 1:
                    max_start = limite_pomeridiano_centro - duration
                    min_start = to_min(8, 23 if group_type == "A" else 18)
                    start_tw = random.randint(min_start, max(min_start, max_start))
                else:
                    if v_num == 1:
                        # prima visita: nel caso peggiore deve iniziare sufficientemente presto da consentire che la seconda visita venga svolta
                        # quindi può slittare al massimo di tw_size + duration + 120 (stacco tra prima e seconda) + 60 (durata max seconda)
                        max_start = limite_pomeridiano_centro - tw_size - duration - 120 - 60
                        min_start = to_min(8, 23 if group_type == "A" else 18)
                        start_tw = random.randint(min_start, max(min_start, max_start))
                        last_end_worst_case = start_tw + tw_size + duration
                    else:
                        # seconda visita: nel caso peggiore inizia dopo last_end_worst_case + 120
                        min_start = last_end_worst_case + 120
                        max_start = limite_pomeridiano_centro - duration
                        start_tw = random.randint(min_start, max(min_start, max_start))
            else:
                # caso in cui il paziente è sulle isole
                ferry_to = FERRY_SCHEDULES[group_type][(center_region, region)]["duration"]
                #ferry_from = FERRY_SCHEDULES[group_type][(region, center_region)]["duration"]
                earliest_start = to_min(8, 46 if group_type == "A" else 36) + ferry_to
                
                # le due corse aggiunte sopra in FERRY_SCHEDULES le avevamo aggiunte per provare a risolvere
                # originariamente le ultime corse sono negli orari qui sotto
                ultimo_traghetto_ritorno = to_min(16, 15) if group_type == "A" else to_min(16, 30)
                limite_pomeridiano_isola = ultimo_traghetto_ritorno - max_dt
                
                if num_visits == 1:
                    max_start = limite_pomeridiano_isola - duration
                    start_tw = random.randint(earliest_start, max(earliest_start, max_start))
                else:
                    if v_num == 1:
                        # prima visita: come sopra
                        max_start = limite_pomeridiano_isola - tw_size - duration - 120 - 60
                        start_tw = random.randint(earliest_start, max(earliest_start, max_start))
                        last_end_worst_case = start_tw + tw_size + duration
                    else:
                        # seconda visita: come sopra
                        min_start = last_end_worst_case + 120
                        max_start = limite_pomeridiano_isola - duration
                        start_tw = random.randint(min_start, max(min_start, max_start))
            
            cg_count = 1 if random.random() < 0.70 else 2
            total_caregiver_visits_needed += cg_count
            
            req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, 
                          "max": {"nurse": 0, "assistant": 0, "health_aid": 0}}
            
            # le probabilità sono state impostate arbitrariamente cercando di allargare il più possibile le scelte più flessibili
            if cg_count == 1:
                r = random.random()
                if r < 0.10: 
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 0, "health_aid": 0}}
                elif r < 0.20: 
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 0}}
                elif r < 0.30: 
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 0, "health_aid": 1}}
                elif r < 0.65: 
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 1, "health_aid": 0}}
                else:          
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 1}}
            else: 
                r = random.random()
                if r < 0.05: 
                    req_skills = {"min": {"nurse": 2, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 0, "health_aid": 0}}
                elif r < 0.10: 
                    req_skills = {"min": {"nurse": 0, "assistant": 2, "health_aid": 0}, "max": {"nurse": 0, "assistant": 2, "health_aid": 0}}
                elif r < 0.50: 
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 1, "health_aid": 1}}
                elif r < 0.80: 
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 1, "assistant": 2, "health_aid": 1}}
                else:          
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 1, "assistant": 1, "health_aid": 2}}
            
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
    num_caregivers = max(num_caregivers, max_simultaneous_needed, 8)
    caregivers = []
    qualifications = ["nurse", "assistant", "health_aid"]
    priorities = {"nurse": 3, "assistant": 2, "health_aid": 1}
    
    for c_id in range(1, num_caregivers + 1):
        qual = qualifications[(c_id - 1) % 3]
        working_shift = {"start": to_min(8, 0), "end": to_min(16, 0)} if c_id % 2 == 0 else {"start": to_min(9, 0), "end": to_min(17, 0)}
        caregivers.append({
            "id": c_id, "qualification": qual, "priority": priorities[qual],
            "start_time": working_shift["start"], "end_time": working_shift["end"]
        })

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