import gurobipy as gp
from gurobipy import GRB

# Importiamo il generatore di dati e la funzione del modello
from data_generator import get_dataset  # Sostituisci con il nome reale della tua funzione
from model import create_milp_model           # Sostituisci con il nome del tuo file modello

def run_model_test():
    print("=== 1. Caricamento Dati dall'Istanza ===")
    # Generiamo un'istanza piccola (ad esempio, passa parametri per fare un'istanza ridotta se il tuo generatore lo permette)
    data = get_dataset("A",10) 
    analyze_dataset_essence(data)
    
    # Un piccolo print di controllo per verificare cosa stiamo testando
    print(f"  Caregivers totali: {len(data['caregivers'])}")
    
    print("\n=== 2. Costruzione del Modello MILP ===")
    model, x, y = create_milp_model(data)
    
    # Attiviamo l'output flag a 1 così puoi vedere tutto il log di Gurobi (nodi esplorati, gap, ecc.)
    model.Params.OutputFlag = 1
    # Impostiamo un time limit di sicurezza (es. 5 minuti), anche se su istanze piccole ci metterà pochissimi secondi
    model.Params.TimeLimit = 300 
    
    print("\n=== 3. Ottimizzazione con Gurobi ===")
    model.optimize()
    
    print("\n=== 4. Analisi dei Risultati ===")
    if model.status == GRB.OPTIMAL:
        print("\n" + "="*50)
        print(f" SOLUZIONE OTTIMA TROVATA! Costo Obiettivo: {model.objVal:.2f}")
        print("="*50)
        
        # --- PARSING DELLE ROTTE DEI CAREGIVERS ---
        print("\n👉 ROTTE ATTIVE:")
        for c in data["caregivers"]:
            c_id = c["id"]
            
            # Controlliamo se il caregiver si è mosso dal deposito iniziale
            has_moved = False
            for edge in x.keys():
                if edge[0] == c_id and edge[1] == ("Center", 1) and x[edge].X > 0.5:
                    has_moved = True
                    break
            
            if not has_moved:
                print(f"  [Caregiver {c_id}] ({c['qualification']}): Rimane al centro (Turno non utilizzato).")
                continue
                
            # Se si è mosso, ricostruiamo la rotta sequenzialmente seguendo il flusso delle x == 1
            current_node = ("Center", 1)
            route_sequence = [current_node]
            
            while current_node != ("Center", 2):
                found_next = False
                for edge in x.keys():
                    # edge è una tupla: (caregiver_id, nodo_origine, nodo_destinazione)
                    if edge[0] == c_id and edge[1] == current_node and x[edge].X > 0.5:
                        next_node = edge[2]
                        route_sequence.append(next_node)
                        current_node = next_node
                        found_next = True
                        break
                
                # Sicurezza per evitare loop infiniti se il grafo si rompe durante i test di sviluppo
                if not found_next:
                    print(f"  [ERRORE DUG] Flusso interrotto per {c_id} al nodo {current_node}")
                    break
            
            # Formattiamo la rotta per renderla leggibile a schermo
            readable_route = " -> ".join([f"{n[0]}(v{n[1]})" if "Center" not in str(n[0]) else n[0] for n in route_sequence])
            print(f"  [Caregiver {c_id}] ({c['qualification']}): {readable_route}")

        # --- PARSING DEGLI ORARI DEI PAZIENTI ---
        print("\n👉 ORARI INIZIO SERVIZIO AI PAZIENTI (y):")
        # Ordiniamo i nodi per nome del paziente per leggerli meglio
        sorted_patient_nodes = sorted(list(y.keys()), key=lambda item: (item[0], item[1]))
        
        for p_node in sorted_patient_nodes:
            valore_minuti = y[p_node].X
            ore = int(valore_minuti // 60)
            minuti = int(valore_minuti % 60)
            print(f"  Paziente {p_node[0]} (Visita {p_node[1]}): minuto {valore_minuti:.1f} (Orario stimato ~ {ore:02d}:{minuti:02d})")
            
    elif model.status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD]:
        print("\n❌ IL MODELLO È INFEASIBLE (o UNBOUNDED)!")
        print("I vincoli si stanno scontrando. Avvio il calcolo dell'IIS (Irreducible Infeasible Subsystem) per trovare l'errore...")
        
        # Questo comando dice a Gurobi di isolare i vincoli minimi che causano il fallimento
        model.computeIIS()
        # Salva un file di testo leggibile con i vincoli incriminati
        model.write("il vincolo_bloccato.ilp")
        print("Fatto! Controlla il file 'il_vincolo_bloccato.ilp' appena generato nella cartella per vedere quale equazione fallisce.")
        
    else:
        print(f"\nL'ottimizzazione si è interrotta con codice stato: {model.status}")

def analyze_dataset_essence(data):
    """
    Stampa un riepilogo dettagliato e strutturato del dataset generato
    per controllare la correttezza dei dati rispetto ai requisiti del modello.
    """
    print("=" * 60)
    print(f" ANALISI ESSENZA DATASET: {data['instance_name']}")
    print("=" * 60)
    
    # 1. Informazioni Generali e Mapping delle Regioni
    print(f"\n🌍 TIPO GRUPPO: {data['group_type']}")
    print("📍 MAPPING LOCALITÀ -> REGIONI:")
    # Stampiamo solo i primi elementi per non intasare lo schermo
    for loc, reg in list(data['region_mapping'].items())[:6]:
        print(f"  - {loc}: situato in -> {reg}")
    if len(data['region_mapping']) > 6:
        print(f"  - ... e altre {len(data['region_mapping']) - 6} località.")

    # 2. Analisi Caregivers
    print(f"\n🧑‍⚕️ CAREGIVERS GENERATI ({len(data['caregivers'])}):")
    for cg in data['caregivers']:
        print(f"  - ID {cg['id']:02d} | Qualifica: {cg['qualification']:<10} | Priorità: {cg['priority']} | Turno: {cg['start_time']} a {cg['end_time']} min")

    # 3. Analisi Pazienti e Visite (Il cuore del Grafo)
    print(f"\n🏥 CAMPIONE PAZIENTI E VISITE :")
    for p in data['patients'][:10]:
        print(f"  - Paziente P_{p['id']} (Regione: {p['region']})")
        for v in p['visits']:
            print(f"    ▪ Visita {v['visit_num']} | Durata: {v['duration']} min | TW: [{v['start_tw']}, {v['end_tw']}] | Operatori richiesti: {v['caregivers_count']}")
            print(f"      Skill Richieste -> Min: {v['skill_requirements']['min']} | Max: {v['skill_requirements']['max']}")

    # 4. Controllo Orari Traghetti
    print(f"\n🚢 STRUTTURA ORARI TRAGHETTI (Ferry Schedules):")
    for rotta, info in data['ferry_schedules'].items():
        print(f"  - Tratta {rotta[0]} ➔ {rotta[1]} | Durata: {info['duration']} min")
        print(f"    Partenze (in minuti): {info['departures']}")

    # 5. Verifica Matrice delle Distanze (Driving Matrix)
    print(f"\n🚗 VERIFICA DIZIONARIO DISTANZE (Campione Tuple):")
    sample_keys = list(data['driving_matrix'].keys())[:100]
    for k in sample_keys:
        print(f"  - Chiave Nativa: {k} -> Tempo di guida: {data['driving_matrix'][k]} min")
        
    print("\n" + "=" * 60)
    print(" CONSTRUTTO DATI IN RAM CORRETTO - PRONTO PER IL MODELLO")
    print("=" * 60)

if __name__ == "__main__":
    run_model_test()