import random
import math


def to_min(hh, mm):
    return hh * 60 + mm

def from_min(m):
    """Funzione di utilità per leggere i minuti in formato HH:MM"""
    return f"{m // 60:02d}:{m % 60:02d}"

# Definizione schedules dei ferry da tabella del paper
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

vn = []
va = []
vh = []
vstar = []
region_mapping = []
driving_matrix = {}
group_type = None
patients = []


def print_dataset_summary(result):
    """Funzione creata appositamente per stampare l'output finale in modo leggibile"""
    print("\n" + "="*50)
    print(f" DATASET GENERATO: {result['instance_name']}")
    print("="*50)
    print(f"Tipo Gruppo: {result['group_type']}")
    print(f"Numero di Caregiver Creati: {len(result['caregivers'])}")
    print(f"Numero di Pazienti Creati: {len(result['patients'])}")
    
    print("\n--- DETTAGLIO CAREGIVER ---")
    for c in result['caregivers']:
        print(f"ID {c['id']}: Qualifica={c['qualification']:<10} | Priorità={c['priority']} | Turno: {from_min(c['start_time'])} - {from_min(c['end_time'])}")
        
    print("\n--- DETTAGLIO PAZIENTI E VISITE ---")
    for p in result['patients']:
        print(f"Paziente ID {p['id']} ({p['region']}):")
        for v in p['visits']:
            print(f"  -> Visita #{v['visit_num']} (Node {v['node_id']}): Durata={v['duration']}m | Tw_Size={v['tw_size']}m | Caregivers Richiesti={v['caregivers_count']}")


def get_dataset(gt, num_patients, seed=22):
    global region_mapping, group_type, vn, va, vh, vstar, patients, driving_matrix
    
    # Reset delle liste globali per evitare accumuli tra chiamate successive
    vn, va, vh, vstar, patients, driving_matrix = [], [], [], [], [], {}
    group_type = gt

    random.seed(seed)
    if group_type == "A":
        regions, weights, center_region = ["Molde", "Sekken"], [0.65, 0.35], "Molde"
    else:
        regions, weights, center_region = ["Sandnessjøen", "Bjørn", "Løkta"], [0.50, 0.30, 0.20], "Sandnessjøen"

    total_cg = 0
    node_counter = 1
    a, c, d = 0, 0, 0
    b = random.randint(0, 3)
    
    rand1 = random.sample(range(1, num_patients + 1), math.floor(num_patients * 30 / 100))
    rand2 = random.sample(range(1, num_patients + 1), math.floor(num_patients * 30 / 100))
    
    print(f"[DEBUG] Pazienti con 2 visite (rand1): {rand1}")
    print(f"[DEBUG] Pazienti con requisiti skill complessi (rand2): {rand2}")

    for p_id in range(1, num_patients + 1):
        p_visits = []
        if p_id in rand1:
            num_visits = 2
            total_cg += 2
        else:
            num_visits = 1
            total_cg += 1
            
        if group_type == "A":
            region = "Molde" if (p_id <= math.ceil(num_patients * 65 / 100)) else "Sekken"
        else:
            if (p_id <= math.ceil(num_patients * 50 / 100)):
                region = "Sandnessjøen"
            elif (p_id <= math.ceil(num_patients * 80 / 100)):
                region = "Bjørn"
            else:
                region = "Løkta"
        
        for v_num in range(1, num_visits + 1):
            a, b, c, d = a % 4, b % 4, c % 10, d % 10
            
            if p_id in rand2:
                cg_count = 2
                if d <= 1: req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 1, "health_aid": 2}}
                elif d <= 4: req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 1, "assistant": 2, "health_aid": 1}}
                elif d <= 7: req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 1, "health_aid": 1}}
                elif d == 8: req_skills = {"min": {"nurse": 0, "assistant": 2, "health_aid": 0}, "max": {"nurse": 0, "assistant": 2, "health_aid": 0}}
                else: req_skills = {"min": {"nurse": 2, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 0, "health_aid": 0}}
            else:
                cg_count = 1
                if c <= 1: req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 1}}
                elif c <= 3: req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 1, "health_aid": 0}}
                elif c <= 5: req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 0, "health_aid": 1}}
                elif c <= 7: req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 0}}
                else: req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 0, "health_aid": 0}}
            
            duration = 15 if a == 0 else (30 if a == 1 else (45 if a == 2 else 60))
            tw_size = 60 if b == 0 else (180 if b == 3 else 120)
            
            a, b, c, d = a+1, b+1, c+1, d+1
            start_tw = 0
            
            p_visits.append({
                "visit_num": v_num,
                "node_id": node_counter,
                "duration": duration,
                "start_tw": start_tw,
                "end_tw": start_tw,
                "tw_size": tw_size,
                "caregivers_count": cg_count,
                "skill_requirements": req_skills
            })
            node_counter += 1

        patients.append({"id": p_id, "region": region, "visits": p_visits})

    # Popolamento liste qualifiche (vn, va, vh)
    for p in patients:
        p_id = p["id"]
        for v in p["visits"]:
            if v["skill_requirements"]["min"]["nurse"] == 2:
                vn.extend([(v, p_id), (v, p_id)])
            if v["skill_requirements"]["min"]["assistant"] == 2:
                va.extend([(v, p_id), (v, p_id)])
                vn.extend([(v, p_id), (v, p_id)])
            if v["skill_requirements"]["min"]["nurse"] == 1:
                vn.append((v, p_id))
                if v["skill_requirements"]["max"]["nurse"] == 2: vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 1: va.extend([(v, p_id)]); vn.extend([(v, p_id), (v, p_id)])
                if v["skill_requirements"]["max"]["assistant"] == 2: va.extend([(v, p_id), (v, p_id)]); vn.extend([(v, p_id), (v, p_id)])
                if v["skill_requirements"]["max"]["health_aid"] == 1: vh.append((v, p_id)); va.append((v, p_id)); vn.append((v, p_id))
            if v["skill_requirements"]["min"]["assistant"] == 1:
                va.append((v, p_id)); vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 2: va.append((v, p_id)); vn.append((v, p_id))
                if v["skill_requirements"]["max"]["nurse"] == 1: vn.append((v, p_id))
                if v["skill_requirements"]["max"]["health_aid"] == 1: vh.append((v, p_id)); va.append((v, p_id)); vn.append((v, p_id))
            if v["skill_requirements"]["min"]["health_aid"] == 1:
                vh.append((v, p_id)); va.append((v, p_id)); vn.append((v, p_id))
                if v["skill_requirements"]["max"]["health_aid"] == 2: vh.append((v, p_id)); va.append((v, p_id)); vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 1: va.append((v, p_id)); vn.append((v, p_id))

    num_caregivers = math.ceil(total_cg / 7)
    caregivers = []
    qualifications = ["nurse", "assistant", "health_aid"]
    priorities = {"health_aid": 1, "assistant": 2, "nurse": 3}

    for c_id in range(1, num_caregivers + 1):
        qual = qualifications[(c_id - 1) % 3]
        working_shift = {"start": to_min(8, 0), "end": to_min(16, 0)} if (c_id - 1) % 2 == 0 else {"start": to_min(9, 0), "end": to_min(17, 0)}
        caregivers.append({
            "id": c_id, 
            "qualification": qual, 
            "priority": priorities[qual],
            "start_time": working_shift["start"], 
            "end_time": working_shift["end"]
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
    avg_dt = 15 if group_type == "A" else 10
    for l1 in locations:
        for l2 in locations:
            reg1, reg2 = region_mapping[l1], region_mapping[l2]
            if reg1 == reg2:
                if l1 == l2: driving_matrix[(l1, l2)] = 0
                else: driving_matrix[(l1, l2)] = max(1, min(23 if group_type == "A" else 18, int(random.gauss(avg_dt, 4))))
                
    if group_type == "A":
        driving_matrix[("Center", "Molde")] = 15
        driving_matrix[("Molde", "Center")] = 15
    else:
        driving_matrix[("Center", "Sandnessjøen")] = 0
        driving_matrix[("Sandnessjøen", "Center")] = 0

    sorted_caregivers = sorted(caregivers, key=lambda c: c["priority"])
    vn.sort(key=visit_difficulty)
    va.sort(key=visit_difficulty)
    vh.sort(key=visit_difficulty)

    print(f"\n[DEBUG] Inizio allocazione visite. Lunghezza liste iniziali: VN={len(vn)}, VA={len(va)}, VH={len(vh)}")

    for c in sorted_caregivers:
        print(f"  -> Allocazione per Caregiver {c['id']} ({c['qualification']})")
        complete_Fill_Lists("Center", "Center", c["start_time"], c["end_time"], c)
        
    print(f"[DEBUG] Fine allocazione. Lunghezza liste residue: VN={len(vn)}, VA={len(va)}, VH={len(vh)}, VSTAR={len(vstar)}\n")
    
    return {
        "instance_name": f"{group_type}-{num_patients}-{num_caregivers}-{total_cg}",
        "group_type": group_type,
        "region_mapping": region_mapping,
        "ferry_schedules": FERRY_SCHEDULES[group_type],
        "caregivers": caregivers,
        "patients": patients,
        "driving_matrix": driving_matrix,
        "min_interval_consecutive_visits": 120
    }

def connectLocations(loc1, loc2, t):
    reg1 = region_mapping[loc1]
    reg2 = region_mapping[loc2]
    if reg1 == reg2:
        return driving_matrix.get((loc1, loc2), 15)
    else:
        tmp = [s for s in FERRY_SCHEDULES[group_type][(reg1, reg2)]["departures"] if s > t]
        if not tmp: return 999  # Salta se non ci sono traghetti disponibili
        return driving_matrix.get((loc1, reg1), 15) + driving_matrix.get((reg2, loc2), 15) + FERRY_SCHEDULES[group_type][(reg1, reg2)]["duration"] + (min(tmp) - t)

def complete_Fill_Lists(location, end, time, stop, c):
    global vstar
    if len(vstar) != 0:
        v1 = vstar[0]
        j = 0
        t = c["qualification"]
        while j < len(vstar):
            if t == "assistant" and vstar[j][0][0]["skill_requirements"]["max"]["assistant"] == 0 and vstar[j][0][0]["skill_requirements"]["max"]["health_aid"] == 0:
                j += 1
            elif t == "health_aid" and vstar[j][0][0]["skill_requirements"]["max"]["health_aid"] == 0:
                j += 1
            else:
                v1 = vstar[j]
                break
        if j == len(vstar):
            fill_Lists(location, end, time, stop, c)
            return 
        if v1[3] == 1:
            location1 = f"P_{v1[0][1]}"
            stop1, time1 = v1[-1], v1[1]
            for v_rem in vstar:
                if v_rem == v1:
                    vstar.remove(v_rem)
                    break
            complete_Fill_Lists(location, location1, time, stop1, c)
            complete_Fill_Lists(location1, end, time1, stop, c)
        else:
            location1 = f"P_{v1[0][1]}"
            stop1, time1 = v1[-1], v1[1]
            if time + connectLocations(location, location1, time) + v1[0][0]["duration"] <= stop1 - 120:
                v1[0][0]["start_tw"] = c["start_time"]
                v1[0][0]["end_tw"] = v1[0][0]["start_tw"] + v1[0][0]["tw_size"]
                for v_rem in vstar:
                    if v_rem == v1:
                        vstar.remove(v_rem)
                        break
                complete_Fill_Lists(location, location1, time + v1[0][0]["duration"], stop1, c)
                complete_Fill_Lists(location1, end, time1, stop, c)
            else:
                v1[0][0]["start_tw"] = to_min(16, 30) - v1[0][0]["tw_size"]
                v1[0][0]["end_tw"] = v1[0][0]["start_tw"] + v1[0][0]["tw_size"]
                for v_rem in vstar:
                    if v_rem == v1:
                        vstar.remove(v_rem)
                        break
                complete_Fill_Lists(location, location1, time, stop1, c)
                complete_Fill_Lists(location1, end, time1, stop, c)
    else:
        fill_Lists(location, end, time, stop, c)

def fill_Lists(location, end, time, stop, c):
    global vh, va, vn, vstar
    s = 0
    while True:
        if c["qualification"] == "health_aid":
            if s < len(vh): visits_list = vh
            else: break
        elif c["qualification"] == "assistant":
            if s < len(va): visits_list = va
            else: break
        elif c["qualification"] == "nurse":
            if s < len(vn): visits_list = vn
            else: break
        else:
            break

        candidates = []
        for visit in visits_list:
            cost = visit_cost(location, end, time, stop, visit)
            if cost is not None:
                candidates.append((cost, visit))

        if not candidates:
            break 
            
        costs = [cc[0] for cc in candidates]
        min_cost, max_cost = min(costs), max(costs)
        threshold = min_cost + 0.3 * (max_cost - min_cost)

        rcl = [visit for cost, visit in candidates if cost <= threshold]
        rcl_with_difficulty = [(visit, visit_difficulty(visit)) for visit in rcl]
        rcl_sorted = sorted(rcl_with_difficulty, key=lambda x: x[1])
        k = min(3, len(rcl_sorted))
        tryed_visit = random.choice([v for v, _ in rcl_sorted[:k]])

        if connectLocations(location, f"P_{tryed_visit[1]}", time) + connectLocations(f"P_{tryed_visit[1]}", end, time + tryed_visit[0]["duration"]) + tryed_visit[0]["duration"] <= stop:
            travel = connectLocations(location, f"P_{tryed_visit[1]}", time) 
            location = f"P_{tryed_visit[1]}"
            tryed_visit[0]["start_tw"] = max(to_min(8,0), time + travel - (tryed_visit[0]["tw_size"] / 2))
            time = time + travel + tryed_visit[0]["duration"]
            tryed_visit[0]["end_tw"] = tryed_visit[0]["start_tw"] + tryed_visit[0]["tw_size"]

            v_target = tryed_visit[0]
            print(f"    [OK] Assegnata visita Node {v_target['node_id']} a Paziente {tryed_visit[1]}")

            # Rimozione e inserimento in vstar
            matched_vh = [item for item in vh if item[0] == v_target]
            if matched_vh:
                if len(matched_vh) > 1:
                    vstar.append((matched_vh[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if matched_vh[0][1] == matched_vh[1][1]:
                        vstar.append((matched_vh[1], time, v_target["duration"], 0, time - v_target["duration"]))
                vh = [item for item in vh if item[0] != v_target]

            matched_va = [item for item in va if item[0] == v_target]
            if matched_va:
                if len(matched_va) > 1:
                    vstar.append((matched_va[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if matched_va[0][1] == matched_va[1][1]:
                        vstar.append((matched_va[1], time, v_target["duration"], 0, time - v_target["duration"]))
                va = [item for item in va if item[0] != v_target]

            matched_vn = [item for item in vn if item[0] == v_target]
            if matched_vn:
                if len(matched_vn) > 1:
                    vstar.append((matched_vn[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if matched_vn[0][1] == matched_vn[1][1]:
                        vstar.append((matched_vn[1], time, v_target["duration"], 0, time - v_target["duration"]))
                vn = [item for item in vn if item[0] != v_target]
        s += 1

def visit_cost(location, end, time, stop, visit):
    patient = f"P_{visit[1]}"
    travel = connectLocations(location, patient, time)
    return_trip = connectLocations(patient, end, time + visit[0]["duration"])
    duration = visit[0]["duration"]
    arrival = time + travel

    if arrival + duration + return_trip > stop:
        return None

    slack = stop - (arrival + duration + return_trip)
    ferry_penalty = 40 if region_mapping[location] != region_mapping[patient] else 0
    return (10 * travel + duration + ferry_penalty - 0.2 * slack)

def visit_difficulty(x):
    visit, pid = x
    return (visit["tw_size"], -visit["duration"], -visit["caregivers_count"], pid)


# --- ESEGUIAMO UN TEST PER VEDERE GLI OUTPUT ---
dataset = get_dataset(gt="A", num_patients=5, seed=42)
print_dataset_summary(dataset)