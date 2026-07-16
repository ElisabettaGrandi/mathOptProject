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






















import random
import math

def to_min(hh, mm):
    return hh * 60 + mm

# Definizione schedules dei ferry da tabella del paper [cite: 685]
FERRY_SCHEDULES = {
    "A": {
        ("Molde", "Sekken"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(16,15)]},
        ("Sekken", "Molde"): {"duration": 30, "departures": [to_min(8,15), to_min(9,15), to_min(10,15), to_min(11,15), to_min(12,15), to_min(13,15), to_min(16,15)]}
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

def get_dataset(group_type, num_patients, seed=43):
    random.seed(seed)
    
    if group_type == "A":
        regions, weights, center_region = ["Molde", "Sekken"], [0.65, 0.35], "Molde"
    else:
        regions, weights, center_region = ["Sandnessjøen", "Bjørn", "Løkta"], [0.50, 0.30, 0.20], "Sandnessjøen"
        
    # -------------------------------------------------------------
    # FASE 1: Generazione preventiva dei Pazienti e calcolo Visite Totali
    # -------------------------------------------------------------
    raw_patients = []
    total_caregiver_visits_needed = 0
    
    for p_id in range(1, num_patients + 1):
        region = random.choices(regions, weights=weights)[0]
        num_visits = 1 if random.random() < 0.70 else 2 # 70% singola visita, 30% doppia [cite: 696]
        is_island = (region != center_region)
        
        p_visits_base = []
        for v_num in range(1, num_visits + 1):
            duration = random.choice([15, 30, 45, 60]) # Distribuzione durate [cite: 700]
            cg_count = 1 if random.random() < 0.70 else 2 # 70% un operatore, 30% due [cite: 697]
            total_caregiver_visits_needed += cg_count
            
            # Requisiti qualifiche fedeli alle specifiche del paper [cite: 698, 699]
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
            else: 
                r = random.random()
                if r < 0.10: 
                    req_skills = {"min": {"nurse": 2, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 0, "health_aid": 0}}
                elif r < 0.20: 
                    req_skills = {"min": {"nurse": 0, "assistant": 2, "health_aid": 0}, "max": {"nurse": 0, "assistant": 2, "health_aid": 0}}
                elif r < 0.50: 
                    req_skills = {"min": {"nurse": 1, "assistant": 0, "health_aid": 0}, "max": {"nurse": 2, "assistant": 1, "health_aid": 1}}
                elif r < 0.80: 
                    req_skills = {"min": {"nurse": 0, "assistant": 1, "health_aid": 0}, "max": {"nurse": 1, "assistant": 2, "health_aid": 1}}
                else:          
                    req_skills = {"min": {"nurse": 0, "assistant": 0, "health_aid": 1}, "max": {"nurse": 1, "assistant": 1, "health_aid": 2}}
            
            p_visits_base.append({
                "patient_id": p_id,
                "region": region,
                "visit_num": v_num,
                "duration": duration,
                "caregivers_count": cg_count,
                "skill_requirements": req_skills,
                "is_island": is_island
            })
            
        raw_patients.append({
            "id": p_id,
            "region": region,
            "visits": p_visits_base,
            "is_island": is_island,
            "num_visits": num_visits
        })

    # -------------------------------------------------------------
    # FASE 2: Generazione dello Staff secondo la formula esatta del paper [cite: 690]
    # -------------------------------------------------------------
    num_caregivers = math.ceil(total_caregiver_visits_needed / 7)
    max_simultaneous_needed = max([v["caregivers_count"] for p in raw_patients for v in p["visits"]])
    num_caregivers = max(num_caregivers, max_simultaneous_needed)
    
    caregivers = []
    qualifications = ["nurse", "assistant", "health_aid"]
    priorities = {"nurse": 3, "assistant": 2, "health_aid": 1} # [cite: 694]
    
    for c_id in range(1, num_caregivers + 1):
        qual = qualifications[(c_id - 1) % 3]
        working_shift = {"start": to_min(8, 0), "end": to_min(16, 0)} if c_id % 2 == 0 else {"start": to_min(9, 0), "end": to_min(17, 0)} # 
        caregivers.append({
            "id": c_id, "qualification": qual, "priority": priorities[qual],
            "start_time": working_shift["start"], "end_time": working_shift["end"]
        })

    # Timeline dello staff per qualifica
    timeline_capacity = {
        qual: [sum(1 for cg in caregivers if cg["qualification"] == qual and cg["start_time"] <= t < cg["end_time"]) 
               for t in range(0, 1440)]
        for qual in qualifications
    }

    max_dt = 23 if group_type == "A" else 18
    avg_dt = 15 if group_type == "A" else 10

    # -------------------------------------------------------------
    # FASE 3: Schedulazione Gerarchica "Ad-Hoc" (Triage dei Vincoli)
    # -------------------------------------------------------------
    # Ordiniamo i pazienti dal più vincolato (Isola + 2 visite) al meno vincolato (Centro + 1 visita)
    # Chiave di ordinamento (is_island: True viene prima, num_visits: 2 viene prima)
    # Calcoliamo un indice di severità per ciascun paziente per fare il Triage preventivo
    for patient in raw_patients:
        score = 0
        if patient["is_island"]:
            score += 1000  # Priorità massima alle isole
        
        # Se ha almeno una visita che richiede 2 caregiver contemporaneamente, è criticissimo
        has_synchronized_visit = any(v["caregivers_count"] == 2 for v in patient["visits"])
        if has_synchronized_visit:
            score += 500
            
        # Se ha due visite (vincolo dei 120 minuti)
        if patient["num_visits"] == 2:
            score += 100
            
        patient["severity_score"] = score

    # Ordiniamo i pazienti dal più severo al meno severo
    raw_patients.sort(key=lambda x: -x["severity_score"])

    scheduled_visits_map = {}

    for patient in raw_patients:
        p_id = patient["id"]
        patient["visits"].sort(key=lambda x: x["visit_num"])
        
        fine_visita_precedente = None

        for visit in patient["visits"]:
            v_num = visit["visit_num"]
            duration = visit["duration"]
            cg_needed = visit["caregivers_count"]
            
            req = visit["skill_requirements"]
            target_qual = "health_aid"
            if req["min"]["nurse"] > 0:
                target_qual = "nurse"
            elif req["min"]["assistant"] > 0:
                target_qual = "assistant"

            # Definizione orizzonte temporale base
            search_start = to_min(8, 0)
            search_end = to_min(17, 0)

            # Finestre per le isole
            if visit["is_island"]:
                ferry_to = FERRY_SCHEDULES[group_type][(center_region, visit["region"])]["duration"]
                ultimo_ritorno = to_min(16, 15) if group_type == "A" else to_min(16, 30)
                
                earliest_ferry = FERRY_SCHEDULES[group_type][(center_region, visit["region"])]["departures"][0]
                earliest_start = earliest_ferry + ferry_to + max_dt
                
                # Sottraiamo ferry_to per garantire al caregiver di avere il tempo di imbarcarsi per il ritorno
                latest_start = ultimo_ritorno - max_dt - duration - ferry_to
                
                search_start = max(search_start, earliest_start)
                search_end = min(search_end, latest_start)
            else:
                search_start = search_start + max_dt
                search_end = search_end - max_dt - duration

            # =========================================================================
            # NUOVA MODIFICA: Controllo preventivo sulla Visita 1 (Se il paziente ne ha 2)
            # =========================================================================
            if patient["num_visits"] == 2 and v_num == 1:
                # Recuperiamo la durata programmata della seconda visita
                durata_seconda_visita = patient["visits"][1]["duration"]
                
                # Calcoliamo l'orario entro cui deve tassativamente finire la visita 1:
                # fine_1 + 120 min stacco + durata_visita_2 + tempo_guida_rientro <= fine_turno (17:00)
                orario_limite_fine_1 = to_min(17, 0) - max_dt - durata_seconda_visita - 120
                
                # Riduciamo search_end per la visita 1
                search_end = min(search_end, orario_limite_fine_1 - duration)
            # =========================================================================

            # SE È LA SECONDA VISITA: Forziamo il vincolo di distanziamento di 120 minuti dal fine della prima
            if v_num == 2 and fine_visita_precedente is not None:
                search_start = max(search_start, fine_visita_precedente + 120)

            best_start = None
            min_load_penalty = float('inf')
            
            possible_starts = list(range(search_start, search_end - duration + 1, 15))
            
            # Se la finestra temporale si stringe troppo, allunghiamo l'orizzonte fino a fine turno
            if not possible_starts:
                search_end_extended = to_min(17, 0) - max_dt - duration
                possible_starts = list(range(search_start, search_end_extended + 1, 15))
                if not possible_starts:
                    possible_starts = [search_start]

            for start_t in possible_starts:
                end_t = start_t + duration
                available = min(timeline_capacity[target_qual][t] for t in range(start_t, end_t))
                
                if available >= cg_needed:
                    load_penalty = sum(1.0 / (timeline_capacity[target_qual][t] + 0.1) for t in range(start_t, end_t))
                    if load_penalty < min_load_penalty:
                        min_load_penalty = load_penalty
                        best_start = start_t

            # Fallback qualifiche
            if best_start is None:
                for alt_qual in qualifications:
                    for start_t in possible_starts:
                        end_t = start_t + duration
                        if min(timeline_capacity[alt_qual][t] for t in range(start_t, end_t)) >= cg_needed:
                            best_start = start_t
                            target_qual = alt_qual
                            break
                    if best_start is not None:
                        break

            # Fallback matematico estremo: mantieni intatto il distanziamento
            if best_start is None:
                best_start = possible_starts[0]

            final_start = best_start
            final_end = final_start + duration
            
            for t in range(final_start, final_end):
                timeline_capacity[target_qual][t] = max(0, timeline_capacity[target_qual][t] - cg_needed)

            fine_visita_precedente = final_end

            # Generazione Time Window reale [cite: 702, 711]
            tw_size = random.choices([60, 120, 180], weights=[0.25, 0.50, 0.25])[0]
            max_shift = max(0, tw_size - duration)
            shift = random.randint(0, max_shift) if max_shift > 0 else 0
            
            start_tw = max(to_min(8, 0), final_start - shift)
            end_tw = start_tw + tw_size

            scheduled_visits_map[(p_id, v_num)] = {
                "visit_num": v_num,
                "duration": duration,
                "start_tw": start_tw,
                "end_tw": end_tw,
                "caregivers_count": cg_needed,
                "skill_requirements": req
            }

    # -------------------------------------------------------------
    # FASE 4: Costruzione Struttura Dati Finale
    # -------------------------------------------------------------
    ferry_ports = set()
    for origin, destination in FERRY_SCHEDULES[group_type].keys():
        ferry_ports.add(origin)
        ferry_ports.add(destination)

    region_mapping = {"Center": center_region}
    for p in raw_patients:
        region_mapping[f"P_{p['id']}"] = p["region"]
    for port in ferry_ports:
        region_mapping[port] = port

    # Driving Matrix
    locations = ["Center"] + [f"P_{p['id']}" for p in raw_patients] + list(ferry_ports)
    driving_matrix = {}
    for l1 in locations:
        for l2 in locations:
            reg1 = region_mapping[l1]
            reg2 = region_mapping[l2]
            if reg1 == reg2:
                if l1 == l2:
                    driving_matrix[(l1, l2)] = 0
                else:
                    val = max(1, min(max_dt, int(random.gauss(avg_dt, 4))))
                    driving_matrix[(l1, l2)] = val

    final_patients = []
    node_counter = 1
    for p in raw_patients:
        p_visits = []
        for v_num in range(1, len(p["visits"]) + 1):
            sched_data = scheduled_visits_map[(p["id"], v_num)]
            sched_data["node_id"] = node_counter
            node_counter += 1
            p_visits.append(sched_data)
            
        final_patients.append({
            "id": p["id"],
            "region": p["region"],
            "visits": p_visits
        })

    return {
        "instance_name": f"{group_type}-{num_patients}-{num_caregivers}-{total_caregiver_visits_needed}",
        "group_type": group_type,
        "region_mapping": region_mapping,
        "ferry_schedules": FERRY_SCHEDULES[group_type],
        "caregivers": caregivers,
        "patients": final_patients,
        "driving_matrix": driving_matrix,
        "min_interval_consecutive_visits": 120
    }



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