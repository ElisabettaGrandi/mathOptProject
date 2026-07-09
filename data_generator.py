import numpy as np

import numpy as np

def generate_airport_instance(num_aircraft=50, num_fixed_gates=18, high_apron_usage=False, seed=42):
    np.random.seed(seed)
    data = {}
    
    # 1. Definizione dei Gate
    data['m'] = num_fixed_gates # Numero di gate fissi nel terminal
    data['apron'] = num_fixed_gates # L'apron è indicizzato come m (0-indexed in Python)
    data['K_fixed'] = list(range(data['m'])) # Set K' del paper
    data['K'] = data['K_fixed'] + [data['apron']] # Set K (Gate fissi + Apron)[cite: 1]
    
    # Divisione Domestici / Internazionali (es. 60% domestici, 40% internazionali)
    num_dom = int(0.6 * num_fixed_gates)
    data['K_D_fixed'] = data['K_fixed'][:num_dom]   # Set K'_D[cite: 1]
    data['K_I_fixed'] = data['K_fixed'][num_dom:]   # Set K'_I[cite: 1]
    data['K_D'] = data['K_D_fixed'] + [data['apron']] # Set K_D[cite: 1]
    data['K_I'] = data['K_I_fixed'] + [data['apron']] # Set K_I[cite: 1]

    # 2. Definizione degli Aerei
    data['I'] = list(range(num_aircraft)) # Set I[cite: 1]
    
    # Assegnazione tipo aereo (D = Domestico, I = Internazionale)
    # g_dict[i] mappa l'aereo al suo tipo ('D' o 'I')[cite: 1]
    data['g_dict'] = {i: ('D' if np.random.rand() < 0.6 else 'I') for i in data['I']}
    
    # Mappatura K_g[i]: a quali gate può accedere l'aereo i[cite: 1]
    data['K_g'] = {i: (data['K_D'] if data['g_dict'][i] == 'D' else data['K_I']) for i in data['I']}
    data['K_g_fixed'] = {i: (data['K_D_fixed'] if data['g_dict'][i] == 'D' else data['K_I_fixed']) for i in data['I']}

    # 3. Generazione Finestre Temporali (Arrivi e Partenze in minuti, es. arco di 24h = 1440 min)
    # Se high_apron_usage=True (Set 2 del paper), comprimiamo gli arrivi per creare picchi e congestione[cite: 1].
    time_span = 720 if high_apron_usage else 1440 
    schedule = []
    
    for i in data['I']:
        arr = np.random.randint(0, time_span)
        dur = np.random.randint(45, 120) # Ogni aereo sosta tra 45 e 120 minuti
        dep = arr + dur
        schedule.append((arr, dep))
    
    data['schedule'] = schedule # Lista di tuple (arrivo, partenza) per ogni aereo

    # 4. Calcolo dei Clique Massimali (Algoritmo polinomiale basato su intervalli di tempo)[cite: 1]
    data['T_D'] = _find_maximal_cliques(data['I'], schedule, data['g_dict'], target_type='D') # Insieme T_D[cite: 1]
    data['T_I'] = _find_excluding_cliques(data['I'], schedule, data['g_dict'], target_type='I') # Insieme T_I[cite: 1]

    # 5. Distanze tra i Gate (Matrice d e vettore ed)
    # Generiamo coordinate casuali (X, Y) per i gate per calcolare distanze Euclidee coerenti
    gate_coords = {k: (np.random.randint(0, 100), np.random.randint(0, 50)) for k in data['K_fixed']}
    gate_coords[data['apron']] = (50, 150) # L'apron è tipicamente isolato e distante[cite: 1]
    
    d = np.zeros((len(data['K']), len(data['K'])))
    for k in data['K']:
        for l in data['K']:
            d[k, l] = int(np.linalg.norm(np.array(gate_coords[k]) - np.array(gate_coords[l])))
    data['d'] = d # Parametro d_kl[cite: 1]
    
    # ed_k: distanza dall'ingresso/uscita (ipotizziamo sia alle coordinate 0,0)[cite: 1]
    data['ed'] = {k: int(np.linalg.norm(np.array(gate_coords[k]) - np.array((0, 0)))) for k in data['K']} # Parametro ed_k[cite: 1]

    # 6. Passeggeri (Fissi e in Transito)
    data['e'] = {i: np.random.randint(50, 150) for i in data['I']} # Parametro e_i[cite: 1]
    data['f'] = {i: np.random.randint(50, 150) for i in data['I']} # Parametro f_i[cite: 1]
    
    # Passeggeri in transito p_ij[cite: 1]
    # Un passeggero può transitare da i a j solo se l'aereo i arriva PRIMA che l'aereo j parta
    p = np.zeros((num_aircraft, num_aircraft))
    for i in data['I']:
        for j in data['I']:
            if i != j and schedule[i][0] < schedule[j][1]: # Coerenza temporale del transito
                if np.random.rand() < 0.2: # 20% di probabilità che ci sia una tratta di transito attiva
                    p[i, j] = np.random.randint(5, 30)
    data['p'] = p # Parametro p_ij[cite: 1]

    # 7. Calcolo del Numero Minimo di Aerei da mandare in Apron (NA*)[cite: 1]
    # Rappresenta il numero di aerei che eccedono la capacità fisica dei gate fissi nei momenti di picco.
    data['NA'] = _calculate_min_apron(data['T_D'], data['T_I'], len(data['K_D_fixed']), len(data['K_I_fixed'])) # Parametro NA*[cite: 1]

    return data


def _find_maximal_cliques(aircraft_list, schedule, g_dict, target_type):
    """Trova i clique massimali di aerei dello stesso tipo sovrapposti nel tempo[cite: 1]"""
    filtered_aircraft = [i for i in aircraft_list if g_dict[i] == target_type]
    if not filtered_aircraft:
        return []
        
    # Estrai tutti gli eventi (tempo, tipo_evento, id_aereo)
    events = []
    for i in filtered_aircraft:
        events.append((schedule[i][0], 'ARR', i))
        events.append((schedule[i][1], 'DEP', i))
    
    # Ordina per tempo. In caso di parità, le partenze prima degli arrivi
    events.sort(key=lambda x: (x[0], 0 if x[1] == 'DEP' else 1))
    
    cliques = []
    current_active = set()
    
    for time, ev_type, i in events:
        if ev_type == 'ARR':
            current_active.add(i)
            # Ogni volta che c'è un arrivo, l'insieme corrente è un candidato clique
            cliques.append(set(current_active))
        else:
            current_active.remove(i)
            
    # Filtra per tenere solo i clique massimali (rimuove i sottoinsiemi)[cite: 1]
    maximal_cliques = []
    for c in sorted(cliques, key=len, reverse=True):
        if not any(c.issubset(m) for m in maximal_cliques if c != m):
            if len(c) > 0:
                maximal_cliques.append(list(c))
                
    return maximal_cliques


def _find_excluding_cliques(aircraft_list, schedule, g_dict, target_type):
    # Funzione specchio per gli aerei internazionali
    return _find_maximal_cliques(aircraft_list, schedule, g_dict, target_type)


def _calculate_min_apron(T_D, T_I, capacity_D, capacity_I):
    """
    Calcola matematicamente il valore NA*[cite: 1].
    Trova il massimo esubero simultaneo rispetto alla capacità dei gate fissi[cite: 1].
    """
    max_apron_D = 0
    for clique in T_D:
        overuse = len(clique) - capacity_D
        if overuse > max_apron_D:
            max_apron_D = overuse
            
    max_apron_I = 0
    for clique in T_I:
        overuse = len(clique) - capacity_I
        if overuse > max_apron_I:
            max_apron_I = overuse
            
    # Il numero minimo totale è la somma degli esuberi massimi dei due settori
    return max_apron_D + max_apron_I