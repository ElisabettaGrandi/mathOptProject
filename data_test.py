import copy
from gurobipy import GRB

# =====================================================================
# IMPORT DEI TUOI MODULI ESISTENTI
# =====================================================================
# Modifica i nomi dei moduli (es. 'modello_originale', 'generatore_dati', 'modello_filtrato')
# a seconda di come hai chiamato i file sul tuo PC.
# Assumiamo qui che:
# - 'modello_originale' contenga build_graph e la versione create_milp_model ORIGINALE (senza x_bar)
# - 'modello_filtrato' contenga build_graph e create_milp_model MODIFICATO (con x_bar e Big-M)
# - 'generatore_dati' contenga get_dataset e FERRY_SCHEDULES
try:
    from model import create_milp_model as create_original_model
    from data_from_model import create_milp_model as create_filtered_model
    from data_generator import get_dataset
    from data_try import get_dataset as get_dataset_try
except ImportError:
    print("[ATTENZIONE] Assicurati che i nomi dei file importati corrispondano ai tuoi file reali.")
    print("In alternativa, incolla qui sopra le definizioni delle funzioni dei tuoi file.")
    raise


def filter_dataset_via_new_model(data):
    """
    Risolve il nuovo modello per estrarre la lista di pazienti 'sicuri'.
    Ritorna un NUOVO dizionario dati contenente solo i pazienti feasible.
    """
    # 1. Costruiamo e risolviamo il modello di copertura modificato (con x_bar e Big-M)
    model, x, y, x_bar = create_filtered_model(data)
    
    print("\n--- [Filtro] Ottimizzazione del modello di copertura con x_bar ---")
    
    model.Params.MIPGap = 0.01      # Ferma il calcolo all'1% di GAP
    model.Params.DualReductions = 0 # Evita lo stato di errore (4)
    model.Params.outputFlag = 1
    model.optimize()
    
    if model.Status != GRB.OPTIMAL and model.Status != GRB.SUBOPTIMAL:
        print("[Errore] Impossibile trovare una soluzione anche con il modello rilassato!")
        return None

    # 2. Troviamo quali visite Gurobi ha deciso di servire (x_bar == 1)
    visite_salvate = set()
    for n, var in x_bar.items():
        if var.X > 0.5:  # Tolleranza numerica standard per variabili binarie
            visite_salvate.add(n)

    print(f"[Filtro] Visite totali nell'istanza iniziale: {len(x_bar)}")
    print(f"[Filtro] Visite giudicate FATTIBILI: {len(visite_salvate)}")

    # 3. REGOLA DI COERENZA: Un paziente viene mantenuto nel dataset finale
    # solo se TUTTE le sue visite pianificate sono state ritenute fattibili dal solutore.
    pazienti_originali = data["patients"]
    pazienti_filtrati = []

    for p in pazienti_originali:
        p_name = f"P_{p['id']}"
        tutte_visite_ok = True
        
        for v in p["visits"]:
            v_node = (p_name, v["visit_num"])
            if v_node not in visite_salvate:
                tutte_visite_ok = False
                break
        
        if tutte_visite_ok:
            pazienti_filtrati.append(p)

    print(f"[Filtro] Pazienti originali: {len(pazienti_originali)} -> Pazienti salvati: {len(pazienti_filtrati)}")

    # 4. Creiamo una copia profonda del dataset originale e sostituiamo la lista pazienti
    clean_data = copy.deepcopy(data)
    clean_data["patients"] = pazienti_filtrati

    return clean_data


def esegui_test_di_fattibilita():
    # 1. Generiamo una nuova istanza (usando il tuo generatore)
    # Impostiamo 15 pazienti su gruppo B per forzare una situazione complessa/infeasible
    num_pazienti = 15
    seed = 43
    best = None
    for i in range(100):
        print(f"Generazione istanza iniziale con {num_pazienti} pazienti (Seed: {seed})...")
        #istanza_iniziale = get_dataset(group_type="B", num_patients=num_pazienti, seed=seed)
        istanza_iniziale = get_dataset_try(gt="B", num_patients=num_pazienti, seed=seed)
        
        print("\n" + "=" * 70)
        print(" FASE 1: TEST MODELLO ORIGINALE SU DATASET INIZIALE")
        print("=" * 70)
        
        # Costruiamo il modello classico di partenza (rigido, senza x_bar)
        # Nota: Usiamo create_original_model che restituisce solo (model, x, y)
        modello_originale, _, _ = create_original_model(istanza_iniziale)
        modello_originale.Params.MIPGap = 0.01      # Ferma il calcolo all'1% di GAP
        modello_originale.Params.DualReductions = 0 # Evita lo stato di errore (4)
        modello_originale.optimize()
        
        if modello_originale.Status == GRB.INFEASIBLE:
            print("\n>>> VERDETTO: Il dataset iniziale è INFEASIBLE (Confermato!)")
        elif modello_originale.Status in [GRB.OPTIMAL, GRB.SUBOPTIMAL]:
            print("\n>>> VERDETTO: Sorprendentemente questa istanza era già feasible.")
        else:
            print(f"\n>>> VERDETTO: Stato del modello non atteso ({modello_originale.Status})")

        seed += 1

       #print("\n" + "=" * 70)
        print(" FASE 2: FILTRAGGIO DEL DATASET TRAMITE NUOVO MODELLO")
        print("=" * 70)
        
        # Generiamo il dataset pulito con il filtro matematico
        dataset_feasible = filter_dataset_via_new_model(istanza_iniziale)
        
        if not dataset_feasible or len(dataset_feasible["patients"]) == 0:
            print("\n[Errore] Il filtro non ha salvato alcun paziente. Prova con un'istanza più grande!")
            return

        print("\n" + "=" * 70)
    print(" FASE 3: VERIFICA DI FATTIBILITÀ SUL NUOVO DATASET")
    print("=" * 70)
    print("Ora lanciamo il TUO modello di partenza (RIGIDO) usando solo i dati filtrati...")
    
    # Costruiamo il modello originale sul dataset depurato
    modello_originale_pulito, _, _ = create_original_model(dataset_feasible)
    modello_originale_pulito.Params.MIPGap = 0.01      # Ferma il calcolo all'1% di GAP
    modello_originale_pulito.Params.DualReductions = 0 # Evita lo stato di errore (4)
    modello_originale_pulito.Params.outputFlag = 1
    modello_originale_pulito.optimize()
    
    # Verdetto finale
    if modello_originale_pulito.Status in [GRB.OPTIMAL, GRB.SUBOPTIMAL]:
        print("\n" + "*" * 60)
        print(" RISULTATO: SUCCESS! Il nuovo dataset è FEASIBLE al 100%!")
        print(f" Tempo di lavoro ottimo totale calcolato: {modello_originale_pulito.ObjVal:.2f} minuti.")
        print("*" * 60)
    elif modello_originale_pulito.Status == GRB.INFEASIBLE:
        print("\n" + "!" * 60)
        print(" RISULTATO: FAIL. Il modello originale è ancora infeasible.")
        print(" Controlla che le modifiche ai vincoli non abbiano lasciato vincoli attivi per sbaglio.")
        print("!" * 60)
    else:
        print(f"\n RISULTATO: Stato inatteso ({modello_originale_pulito.Status})")


if __name__ == "__main__":
    esegui_test_di_fattibilita()