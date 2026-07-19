import random
import math


def to_min(hh, mm):
    return hh * 60 + mm

FERRY_SCHEDULES = {
    "A": {
        ("Molde", "Sekken"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(14,15), to_min(15,15), to_min(16,15)]},
        ("Sekken", "Molde"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(14,15), to_min(15,15), to_min(16,15)]}
    },
    "B": {
        ("Sandnessjoen", "Bjorn"): {"duration": 25, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]},
        ("Bjorn", "Sandnessjoen"): {"duration": 25, "departures": [to_min(8,30), to_min(9,30), to_min(10,30), to_min(11,30), to_min(12,30), to_min(13,30), to_min(14,30), to_min(15,30), to_min(16,30)]},
        ("Bjorn", "Lokta"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(11,0), to_min(11,30), to_min(12,0), to_min(12,30), to_min(13,0), to_min(13,30), to_min(14,0), to_min(14,30), to_min(15,0), to_min(15,30), to_min(16,0), to_min(16,30)]},
        ("Lokta", "Bjorn"): {"duration": 25, "departures": [to_min(8,0), to_min(8,30), to_min(9,0), to_min(9,30), to_min(10,0), to_min(10,30), to_min(11,0), to_min(11,30), to_min(12,0), to_min(12,30), to_min(13,0), to_min(13,30), to_min(14,0), to_min(14,30), to_min(15,0), to_min(15,30), to_min(16,0), to_min(16,30)]},
        ("Sandnessjoen", "Lokta"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]},
        ("Lokta", "Sandnessjoen"): {"duration": 60, "departures": [to_min(8,0), to_min(9,0), to_min(10,0), to_min(11,0), to_min(12,0), to_min(13,0), to_min(14,0), to_min(15,0), to_min(16,0)]}
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


def get_dataset(gt, num_patients, seed=22):

    global region_mapping, group_type, patients, vn, va, vh, vstar, driving_matrix
    patients = []
    vn = []
    va = []
    vh = []
    vstar = []
    driving_matrix = {}

    random.seed(seed)

    group_type = gt
    if group_type == "A":
        regions, weights, center_region = ["Molde", "Sekken"], [0.65, 0.35], "Molde"

    else:
        regions, weights, center_region = ["Sandnessjoen", "Bjorn", "Lokta"], [0.50, 0.30, 0.20], "Sandnessjoen"

    max_dt = 23 if group_type == "A" else 18
    avg_dt = 15 if group_type == "A" else 10 

    total_cg = 0
    node_counter = 1
    a = 0
    b = random.randint(0, 3)
    c = 0
    d = 0
    rand1 = random.sample(range(1, num_patients +1), math.floor(num_patients*30/100))
    rand2 = random.sample(range(1, num_patients +1), math.floor(num_patients*30/100))
    for p_id in range(1, num_patients + 1):
        p_visits = []
        if p_id in rand1:
            num_visits = 2
            total_cg += 2
        else:
            num_visits = 1
            total_cg += 1
        if group_type == "A":
            if (p_id <= math.ceil(num_patients * 65 / 100 )):
                region = "Molde"
            else:
                region = "Sekken"
        else:
            if (p_id <= math.ceil(num_patients * 50 / 100 )):
                region = "Sandnessjoen"
            elif(p_id <= math.ceil(num_patients * 80 / 100 )):
                region = "Bjorn" 
            else:
                region = "Lokta"       
        
        for v_num in range(1, num_visits + 1):
            a = a % 4
            b = b % 4
            c = c % 10
            d = d % 10
            if p_id in rand2:
                cg_count = 2
                total_cg += 1
                if d <= 1:
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 1, "health_aid": 2}}
                elif d <= 4:
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 1, "assistant": 2, "health_aid": 1}}
                elif d <= 7:
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 1, "health_aid": 1}}
                elif d == 8:
                    req_skills = {"min": {"nurse": 0, "assistant": 2, "health_aid": 0}, "max": {"nurse": 0, "assistant": 2, "health_aid": 0}}
                else:
                    req_skills = {"min": {"nurse": 2, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 0, "health_aid": 0}}
                d += 1


            else:
                cg_count = 1
                if c <= 1:
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 1}}
                elif c <= 3:
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 1, "health_aid": 0}}
                elif c <= 5:
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 0, "assistant": 0, "health_aid": 1}}
                elif c <= 7:
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 0, "assistant": 1, "health_aid": 0}}
                else:      
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 1, "assistant": 0, "health_aid": 0}}
                c += 1

            if a == 0:
                duration = 15
            elif a == 1:
                duration = 30
            elif a == 2:
                duration = 45
            else:
                duration = 60
            if b == 0:
                tw_size = 60
            elif b == 3:
                tw_size = 180
            else:
                tw_size = 120
            a += 1
            b += 1
            

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

    for p in patients:
        p_id = p["id"]
        for v in p["visits"]:
            a = None
            b = None
            if p_id in rand1:
                b = p_id
            if p_id in rand2:
                a = p_id

            if v["skill_requirements"]["min"]["nurse"] == 2:
                vn.append((v, p_id))
                vn.append((v, p_id))   
            if v["skill_requirements"]["min"]["assistant"] == 2: 
                va.append((v, p_id))
                va.append((v, p_id))
                vn.append((v, p_id))
                vn.append((v, p_id))    
            if v["skill_requirements"]["min"]["nurse"] == 1:
                vn.append((v, p_id))
                if v["skill_requirements"]["max"]["nurse"] == 2:
                    vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 1:
                    va.append((v, p_id))
                    vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 2:     
                    va.append((v, p_id))
                    va.append((v, p_id))
                    vn.append((v, p_id))
                    vn.append((v, p_id)) 
                if v["skill_requirements"]["max"]["health_aid"] == 1:
                    vh.append((v, p_id))
                    va.append((v, p_id))
                    vn.append((v, p_id))
            if v["skill_requirements"]["min"]["assistant"] == 1:
                va.append((v, p_id))
                vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 2:
                    va.append((v, p_id))
                    vn.append((v, p_id))
                if v["skill_requirements"]["max"]["nurse"] == 1:
                    vn.append((v, p_id))
                if v["skill_requirements"]["max"]["health_aid"] == 1:
                    vh.append((v, p_id))
                    va.append((v, p_id))
                    vn.append((v, p_id))
            if v["skill_requirements"]["min"]["health_aid"] == 1:
                vh.append((v, p_id))
                va.append((v, p_id))
                vn.append((v, p_id))
                if v["skill_requirements"]["max"]["health_aid"] == 2:
                    vh.append((v, p_id))
                    va.append((v, p_id))
                    vn.append((v, p_id))
                if v["skill_requirements"]["max"]["assistant"] == 1:
                    va.append((v, p_id))
                    vn.append((v, p_id))
            if (v["skill_requirements"]["min"]["nurse"] == 0 and 
                v["skill_requirements"]["min"]["assistant"] == 0 and 
                v["skill_requirements"]["min"]["health_aid"] == 0):
                if  v["skill_requirements"]["max"]["health_aid"] == 1:
                    vh.append((v, p_id))
                    va.append((v, p_id))
                    vn.append((v, p_id))
                if  v["skill_requirements"]["max"]["health_aid"] == 0:
                    va.append((v, p_id))
                    vn.append((v, p_id))



        


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
            reg1 = region_mapping[l1]
            reg2 = region_mapping[l2]
            if reg1 == reg2:
                if l1 == l2:
                    driving_matrix[(l1, l2)] = 0
                else:
                    val = max(1, min(23 if group_type == "A" else 18, int(random.gauss(avg_dt, 4))))
                    driving_matrix[(l1, l2)] = val
    if group_type == "A":
        driving_matrix[("Center", "Molde")] = 15
        driving_matrix[("Molde", "Center")] = 15
    else:
        driving_matrix[("Center", "Sandnessjoen")] = 0
        driving_matrix[("Sandnessjoen", "Center")] = 0


    #print(f"DEBUG: Lunghezza liste dopo popolamento:")
    #print(f"  vh: {len(vh)} visite")
    #print(f"  va: {len(va)} visite")
    #print(f"  vn: {len(vn)} visite")

    sorted_caregivers = sorted(caregivers, key=lambda c: c["priority"])
    vn.sort(key=visit_difficulty)
    va.sort(key=visit_difficulty)
    vh.sort(key=visit_difficulty)

    for c in sorted_caregivers:
        location = "Center"
        end = "Center"
        time = c["start_time"]
        stop = c["end_time"]

        complete_Fill_Lists(location, end, time, stop, c)
        #print("EXIT caregiver", c["id"])

    for p in patients:
        p_id = p["id"]
        for v in p["visits"]:
            if v["start_tw"] == 0 and v["end_tw"] == 0:
                v["duration"] = 15
                v["tw_size"] = 180
                v["caregivers_count"] = 1
                v["skill_requirements"] = {
                    "min": {"nurse": 0, "assistant": 0, "health_aid": 0}, 
                    "max": {"nurse": 0, "assistant": 1, "health_aid": 1}
                }
                
                if len(p["visits"]) == 2:
                    other_visit = p["visits"][0] if p["visits"][1] == v else p["visits"][1]
                    
                    if other_visit["start_tw"] >= to_min(13, 0):
                        v["start_tw"] = to_min(9, 0)
                    else:
                        v["start_tw"] = to_min(13, 30)
                else:
                    v["start_tw"] = random.randint(to_min(9, 30), to_min(13, 30))
                
                v["end_tw"] = v["start_tw"] + v["tw_size"]
    
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




def connectLocations (loc1, loc2, t):
    reg1 = region_mapping[loc1]
    reg2 = region_mapping[loc2]
    if reg1 == reg2:
        time_to_travel = driving_matrix[(loc1, loc2)]

    else:
        tmp = [s for s in FERRY_SCHEDULES[group_type][(reg1, reg2)]["departures"] if s > t]

        if not tmp:
            return float('inf')

        time_to_travel = driving_matrix[(loc1, reg1)] + driving_matrix[(reg2, loc2)] + FERRY_SCHEDULES[group_type][(reg1, reg2)]["duration"] + (min(tmp) - t)
    return time_to_travel


def complete_Fill_Lists(location, end, time, stop, c):

    #print("----------------")
    #print(c["id"], c["qualification"])
    #print("vstar", len(vstar))

    
    if len(vstar) !=0:
        j = 0
        t = c["qualification"]
        while j < len(vstar):
            if t== "assistant" and vstar[j][0][0]["skill_requirements"]["max"]["assistant"] == 0 and  vstar[j][0][0]["skill_requirements"]["max"]["health_aid"] == 0:
                j += 1
            elif t == "health_aid" and vstar[j][0][0]["skill_requirements"]["max"]["health_aid"] == 0:
                j += 1
            else:
                v1 = vstar[j]
                break
        if j == len(vstar):
            #print("CALL fill_lists")
            fill_Lists(location, end, time, stop, c)
            return 
        vstar.pop(j)

        #print("POP", v1[0][1])

        location1 = f"P_{v1[0][1]}"
        stop1 = v1[-1]
        time1 = v1[1]
        if v1[3] == 1:
            
            
            complete_Fill_Lists(location, location1, time , stop1, c)
            complete_Fill_Lists(location1, end, time1, stop, c)
        else:


            if time + connectLocations(location, location1, time) +v1[0][0]["duration"] <=  stop1 - 120:
                v1[0][0]["start_tw"] = c["start_time"]
                v1[0][0]["end_tw"] = v1[0][0]["start_tw"] + v1[0][0]["tw_size"]
                
                complete_Fill_Lists(location, location1, time + v1[0][0]["duration"], stop1, c)
                complete_Fill_Lists(location1, end, time1, stop, c)
            else:
                v1[0][0]["start_tw"] = to_min(16, 30) -  v1[0][0]["tw_size"]
                v1[0][0]["end_tw"] = v1[0][0]["start_tw"] + v1[0][0]["tw_size"]
                
                complete_Fill_Lists(location, location1, time, stop1, c)
                complete_Fill_Lists(location1, end, time1, stop, c)
                
            
        
    else:
        #print("CALL fill_lists")
        fill_Lists(location, end, time, stop, c)



def fill_Lists(location, end, time, stop, c):
    global vh, va, vn

    #print(f"DEBUG fill_Lists: caregiver {c['id']} ({c['qualification']})")
    #print(f"  vh: {len(vh)}, va: {len(va)}, vn: {len(vn)}")

    failed_visits = []
    
    while True:
        if c["qualification"] == "health_aid":
            visits_list = vh
        if c["qualification"] == "assistant":
            visits_list = va
        if c["qualification"] == "nurse":
            visits_list = vn

        candidates = []

        for visit in visits_list:

            if visit[0] in failed_visits:
                continue

            cost = visit_cost(
                location,
                end,
                time,
                stop,
                visit
            )

            if cost is not None:
                candidates.append((cost, visit))

        if not candidates:
            break 
        costs = [cc[0] for cc in candidates]
        min_cost = min(costs)
        max_cost = max(costs)
        threshold = min_cost + 0.3 * (max_cost - min_cost)

        rcl = [visit for cost, visit in candidates if cost <= threshold]

        if not rcl:
            for cost, visit in candidates:
                if visit[0] not in failed_visits:
                    failed_visits.append(visit[0])
            continue


        rcl_with_difficulty = [(visit, visit_difficulty(visit)) for visit in rcl]
        rcl_sorted = sorted(rcl_with_difficulty, key=lambda x: x[1])
        k = min(3, len(rcl_sorted))
        tryed_visit = random.choice([v for v, _ in rcl_sorted[:k]])

        
        v_target = tryed_visit[0]
        if connectLocations(location, f"P_{tryed_visit[1]}", time) + connectLocations(f"P_{tryed_visit[1]}", end, time + tryed_visit[0]["duration"]) + tryed_visit[0]["duration"] <= stop:
            travel = connectLocations(location, f"P_{tryed_visit[1]}", time) 
            location = f"P_{tryed_visit[1]}"
            tryed_visit[0]["start_tw"] = max( to_min(8,0), time + travel -  (tryed_visit[0]["tw_size"] / 2))
            time = time + travel + tryed_visit[0]["duration"]
            tryed_visit[0]["end_tw"] = tryed_visit[0]["start_tw"] + tryed_visit[0]["tw_size"]

            to_be_added = True

            matched_vh = [item for item in vh if item[0] == v_target]
            matched_couple_vh = [item for item in vh if item[1] == tryed_visit[1] and item[0]["skill_requirements"] == v_target["skill_requirements"] and item[0] != v_target]
            
            if len(matched_vh) > 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_vh[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if len(matched_couple_vh) >= 1:
                        vstar.append((matched_couple_vh[0], time, v_target["duration"], 0, time - v_target["duration"]))
            elif len(matched_couple_vh) >= 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_couple_vh[0], time, v_target["duration"], 0, time - v_target["duration"]))
                    if len(matched_couple_vh) == 2:
                        vstar.append((matched_couple_vh[1], time, v_target["duration"], 0, time - v_target["duration"]))
            
            vh[:] = [item for item in vh if item not in matched_vh and item not in matched_couple_vh]

            matched_va = [item for item in va if item[0] == v_target]
            matched_couple_va = [item for item in va if item[1] == tryed_visit[1] and item[0]["skill_requirements"] == v_target["skill_requirements"] and item[0] != v_target]
            
            if len(matched_va) > 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_va[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if len(matched_couple_va) >= 1:
                        vstar.append((matched_couple_va[0], time, v_target["duration"], 0, time - v_target["duration"]))
            elif len(matched_couple_va) >= 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_couple_va[0], time, v_target["duration"], 0, time - v_target["duration"]))
                    if len(matched_couple_va) == 2:
                        vstar.append((matched_couple_va[1], time, v_target["duration"], 0, time - v_target["duration"]))
            
            va[:] = [item for item in va if item not in matched_va and item not in matched_couple_va]

            matched_vn = [item for item in vn if item[0] == v_target]
            matched_couple_vn = [item for item in vn if item[1] == tryed_visit[1] and item[0]["skill_requirements"] == v_target["skill_requirements"] and item[0] != v_target]
            
            if len(matched_vn) > 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_vn[0], time, v_target["duration"], 1, time - v_target["duration"]))
                    if len(matched_couple_vn) >= 1:
                        vstar.append((matched_couple_vn[0], time, v_target["duration"], 0, time - v_target["duration"]))
            elif len(matched_couple_vn) >= 1:
                if to_be_added:
                    to_be_added = False
                    vstar.append((matched_couple_vn[0], time, v_target["duration"], 0, time - v_target["duration"]))
                    if len(matched_couple_vn) == 2:
                        vstar.append((matched_couple_vn[1], time, v_target["duration"], 0, time - v_target["duration"]))
            
            vn[:] = [item for item in vn if item not in matched_vn and item not in matched_couple_vn]
        else:
            
            failed_visits.append(v_target)



def visit_cost(location, end, time, stop, visit):

    patient = f"P_{visit[1]}"

    travel = connectLocations(location, patient, time)
    return_trip = connectLocations(patient, end, time + visit[0]["duration"])

    if travel == float('inf') or return_trip == float('inf'):
        return None

    duration = visit[0]["duration"]

    arrival = time + travel



    if arrival + duration > stop:
        return None

    slack = stop - (arrival + duration + return_trip)

    ferry_penalty = 0
    if region_mapping[location] != region_mapping[patient]:
        ferry_penalty = 40

    score = (
        10 * travel +
        duration +
        ferry_penalty -
        0.2 * slack
    )

    return score  

def visit_difficulty(x):
    visit, pid = x

    return (
        visit["tw_size"],
        -visit["duration"],
        -visit["caregivers_count"],
        pid
    )