import random
import math


def to_min(hh, mm):
    return hh * 60 + mm

# Definizione schedules dei ferry da tabella del paper [cite: 685]
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



def get_dataset(group_type, num_patients, seed=22): # 43 va
    random.seed(seed)
    if group_type == "A":
        regions, weights, center_region = ["Molde", "Sekken"], [0.65, 0.35], "Molde"

    else:
        regions, weights, center_region = ["Sandnessjøen", "Bjørn", "Løkta"], [0.50, 0.30, 0.20], "Sandnessjøen"

    max_dt = 23 if group_type == "A" else 18
    avg_dt = 15 if group_type == "A" else 10 

    patients = []
    doublep = []
    singlep = []
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
            #sistemare
            continue        
        
        for v_num in range(1, num_visits + 1):
            a = a % 4
            b = b % 4
            c = c % 10
            d = d % 10
            if p_id in rand2:
                cg_count = 2
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
            c += 1
            d += 1

            start_tw = None
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

        if p_visits["caregivers_count"] == 2:
            doublep.append({"id": p_id, "region": region, "visits": p_visits})
        else:
            singlep.append({"id": p_id, "region": region, "visits": p_visits})

    vn = []
    va = []
    vh = []
    for p_id in patients:
        for v in p_visits:
            a = None
            b = None
            if p_id in rand1:
                b = p_id
            if p_id in rand2:
                a = p_id

        if v["req_skill"]["min"]["nurse"] == 2:
            vn.append({v, p_id})
            vn.append({v, p_id})   
        if v["req_skill"]["min"]["assistant"] == 2: 
            va.append({v, p_id})
            va.append({v, p_id})
            vn.append({v, p_id})
            vn.append({v, p_id})    
        if v["req_skill"]["min"]["nurse"] == 1:
            vn.append({v, p_id})
            if v["req_skill"]["max"]["nurse"] == 2:
                vn.append({v, p_id})
            if v["req_skill"]["max"]["assistant"] == 1:
                va.append({v, p_id})
                vn.append({v, p_id})
            vn.append({v, p_id}) 
            if v["req_skill"]["max"]["assistant"] == 2:     
                va.append({v, p_id})
                va.append({v, p_id})
                vn.append({v, p_id})
                vn.append({v, p_id}) 
            if v["req_skill"]["max"]["health_aid"] == 1:
                vh.append({v, p_id})
                va.append({v, p_id})
                vn.append({v, p_id})
        if v["req_skill"]["min"]["assistant"] == 1:
            va.append({v, p_id})
            vn.append({v, p_id})
            if v["req_skill"]["max"]["assistant"] == 2:
                va.append({v, p_id})
                vn.append({v, p_id})
            if v["req_skill"]["max"]["nurse"] == 1:
                vn.append({v, p_id})
            if v["req_skill"]["max"]["health_aid"] == 1:
                vh.append({v, p_id})
                va.append({v, p_id})
                vn.append({v, p_id})
        if v["req_skill"]["min"]["health_aid"] == 1:
            vh.append({v, p_id})
            va.append({v, p_id})
            vn.append({v, p_id})
            if v["req_skill"]["max"]["health_aid"] == 2:
                vh.append({v, p_id})
                va.append({v, p_id})
                vn.append({v, p_id})
            if v["req_skill"]["max"]["assistant"] == 1:
                va.append({v, p_id})
                vn.append({v, p_id})

        


    num_caregivers = math.ceil(total_cg / 7)
    caregivers = []
    qualifications = ["nurse", "assistant", "health_aid"]
    priorities = {"health_aid": 1, "assistant": 2, "nurse": 3} # [cite: 694]

       

    for c_id in range(1, num_caregivers + 1):
        qual = qualifications[(c_id - 1) % 3]
        working_shift = {"start": to_min(8, 0), "end": to_min(16, 0)} if (c_id - 1) % 2 == 0 else {"start": to_min(9, 0), "end": to_min(17, 0)}
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
    if group_type == "A":
        driving_matrix[("Center", "Molde")] = 15
        driving_matrix[("Molde", "Center")] = 15
    else:
        driving_matrix[("Center", "Sandnessjøen")] = 0
        driving_matrix[("Sandnessjøen", "Center")] = 0



    # for k,v in priorities:
    #     for c in caregivers:
    #         if c["priority"] != v:
    #             continue
    #         time = c["start_time"]
    #         stop = c["end_time"]
    #         # if len(doublep) != 0:
    #         #     tmp = []
    #         #     for j in doublep:
    #         #         if j["visits"]["req_skill"]["max"][k] > 0:
    #         #             tmp.append(j)
    #         #     if len(tmp) != 0:
    #         #         s = random.sample(tmp, 1)

    sorted_caregivers = sorted(caregivers, key=lambda c: c["priority"])


    vstar = []
    for c in sorted_caregivers:
        location = "Center"
        end = "Center"
        time = c["start_time"]
        stop = c["end_time"]

        complete_Fill_Lists(location, end, time, stop)




    def connectLocations (loc1, loc2):
        reg1 = region_mapping[loc1]
        reg2 = region_mapping[loc2]
        if reg1 == reg2:
            time_to_travel = driving_matrix[(loc1, loc2)]

        else:
            time_to_travel = driving_matrix[(loc1, reg1)] + driving_matrix[(reg2, loc2)] + FERRY_SCHEDULES[group_type][(reg1, reg2)]["duration"]
        return time_to_travel


    def complete_Fill_Lists(location, end, time, stop):
        if len(vstar) !=0:
            v1 = vstar[0]
            if v1[3] == 1:
                location1 = v1[0][1]
                stop1 = v1[-1]
                time1 = v1[1]
                
                for v_rem in vstar:
                    if v_rem == v1:
                        v_rem.remove
                complete_Fill_Lists(location, location1, time , stop1)
                complete_Fill_Lists(location1, end, time1, stop)
            else:
                if time + connectLocations(location, location1) +v1[0][0]["duration"] <=  stop1 - 120:
                    for v_rem in vstar:
                        if v_rem == v1:
                            v_rem.remove
                    complete_Fill_Lists(location1, end, time + connectLocations(location, location1) +v1[0][0]["duration"], stop)
                else:
                    for v_rem in vstar:
                        if v_rem == v1:
                            v_rem.remove
                            break
                    complete_Fill_Lists(location, location1, time, stop- connectLocations( location1, stop)- v1[0][0]["duration"])
                    
                
            
        else:
            fill_Lists(location, end, time, stop)




    def fill_Lists(location, end, time, stop):
        s = 0
        while True:
            if c["qualification"] == "health_aid":
                if s <= len(vh):
                    tryed_visit = vh[s]
                else:
                    break
            if c["qualification"] == "assistant":
                if s <= len(va):
                    tryed_visit = vh[s]
                else:
                    break
            if c["qualification"] == "nurse":
                if s <= len(vh):
                    tryed_visit = vh[s]
                else:
                    break
            if connectLocations(location, tryed_visit[1]) + connectLocations(tryed_visit[1], end) + tryed_visit[0]["duration"] <= stop:
                location = tryed_visit[1]
                patients["p_visits"]["start_tw"] = time + connectLocations(location, tryed_visit[1]) -(patients["p_visits"]["tw_size"] / 2) 
                time = time + connectLocations(location, tryed_visit[1]) + tryed_visit
                patients["p_visits"]["end_tw"] = patients["p_visits"]["start_tw"] + patients["p_visits"]["tw_size"]

                for el in vh:
                    if el[0] == tryed_visit[0]:
                        if el[0] == el.next[0]:
                            vstar.append({el, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[1] == el.next[1]:
                                vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})                                
                                el.next.remove
                        if el[1] == el.next[1]:
                            vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[0] == el.next[0]:
                                el.next.remove
                                vstar.append({el.next, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                        el.remove
                        break
                
                for el in va:
                    if el[0] == tryed_visit[0]:
                        if el[0] == el.next[0]:
                            vstar.append({el, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[1] == el.next[1]:
                                vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})                                
                                el.next.remove
                        if el[1] == el.next[1]:
                            vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[0] == el.next[0]:
                                el.next.remove
                                vstar.append({el.next, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                        el.remove
                        break
                
                for el in vn:
                    if el[0] == tryed_visit[0]:
                        if el[0] == el.next[0]:
                            vstar.append({el, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[1] == el.next[1]:
                                vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})                                
                                el.next.remove
                        if el[1] == el.next[1]:
                            vstar.append({el.next, time, el[0]["duration"], 0, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                            el.next.remove
                            if el[0] == el.next[0]:
                                el.next.remove
                                vstar.append({el.next, time, el[0]["duration"], 1, time - connectLocations(location, tryed_visit[1]) - tryed_visit})
                        el.remove
                        break
            else:
                s += 1
                
                
                        

                    





    







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

    




            

            
              


