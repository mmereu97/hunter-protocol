import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS & IMPORTS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 45
AXIS_NAME = "Vigilență"
# Pol Stânga (0): Încrezător / Relaxat / Naiv
# Pol Dreapta (100): Suspicios / Vigilent / Paranoic

# 3. FUNCȚIA DE HASHING
def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu a fost găsită la: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", f"Populăm Axa {AXIS_ID}: {AXIS_NAME}...")

    # 4. DATASET-UL
    # Punctaj: 0 = Încrezător, 100 = Suspicios
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Atitudinea față de alții) ---
        (
            "Când cineva este extrem de amabil cu tine fără un motiv evident, ce gândești?",
            "Motives, Kindness, Skepticism", 
            1, 
            [
                ("A) Că este o persoană drăguță.", 0), 
                ("B) Mă bucur de gest.", 30), 
                ("C) Mă întreb ce vrea în schimb.", 70), 
                ("D) Intru la bănuieli. Sigur pregătește o manipulare.", 100)
            ]
        ),
        (
            "Crezi că majoritatea oamenilor ar profita de tine dacă ar avea ocazia?",
            "Worldview, Trust, Cynicism", 
            1, 
            [
                ("A) Nu, oamenii sunt corecți.", 0), 
                ("B) Unii da, dar nu majoritatea.", 30), 
                ("C) Probabil că da, trebuie să fii atent.", 70), 
                ("D) Absolut. 'Omul este lup pentru om'.", 100)
            ]
        ),
        (
            "Cât de des ai impresia că oamenii vorbesc despre tine pe la spate?",
            "Paranoia, Gossip, Self-Referential", 
            1, 
            [
                ("A) Niciodată. Nu sunt subiect de discuție.", 0), 
                ("B) Rar, poate dacă am greșit ceva.", 30), 
                ("C) Uneori am această impresie.", 70), 
                ("D) Frecvent. Simt priviri și șușoteli când intru într-o cameră.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Relații/Monitorizare) ---
        (
            "În relațiile personale sau profesionale, ai tendința să verifici spusele celorlalți pentru a vedea dacă mint?",
            "Verification, Trust Issues, Detective", 
            2, 
            [
                ("A) Nu, am încredere în cuvântul lor.", 0), 
                ("B) Doar dacă ceva nu se leagă.", 30), 
                ("C) Verific discret din când în când.", 70), 
                ("D) Da, verific tot. Încrederea e bună, controlul e mai bun.", 100)
            ]
        ),
        (
            "Dacă un coleg face o greșeală care te afectează, presupui că a fost un accident sau rea-intenție?",
            "Attribution Bias, Malice", 
            2, 
            [
                ("A) Un accident, oricine greșește.", 0), 
                ("B) Probabil neatenție.", 30), 
                ("C) Mă gândesc dacă a făcut-o intenționat.", 70), 
                ("D) A fost sabotaj clar. Voia să mă încurce.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să te relaxezi complet într-un grup de oameni pe care nu îi cunoști foarte bine?",
            "Social Anxiety, Guardedness", 
            2, 
            [
                ("A) Foarte ușor.", 0), 
                ("B) Îmi ia puțin timp să mă acomodez.", 30), 
                ("C) Rămân rezervat și atent.", 70), 
                ("D) Nu mă relaxez. Stau 'cu spatele la perete' și monitorizez tot.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Paranoia / Cinism / Gelozie Patologică) ---
        (
            "Ai simțit vreodată nevoia să verifici telefonul, email-ul sau buzunarele partenerului/colegilor fără știrea lor?",
            "Privacy, Spying, Jealousy", 
            3, 
            [
                ("A) Niciodată. Respect intimitatea.", 0), 
                ("B) M-a bătut gândul, dar nu am făcut-o.", 20), 
                ("C) Am verificat o dată când aveam suspiciuni mari.", 70), 
                ("D) Da, verific regulat. Trebuie să știu adevărul.", 100)
            ]
        ),
        (
            "Crezi că ai dușmani ascunși care complotează activ împotriva succesului tău?",
            "Persecution, Conspiracy, Grandiosity", 
            3, 
            [
                ("A) Nu, nu sunt atât de important.", 0), 
                ("B) Poate am câțiva rivali, e normal.", 30), 
                ("C) Simt că unii vor să mă 'sape'.", 70), 
                ("D) Da, sunt forțe care lucrează concertat să mă blocheze.", 100)
            ]
        ),
        (
            "Dacă cineva te trădează o dată, mai poate recâștiga încrederea ta?",
            "Forgiveness, Grudges, Black and White", 
            3, 
            [
                ("A) Da, oamenii merită a doua șansă.", 0), 
                ("B) Greu, dar posibil.", 30), 
                ("C) Foarte greu. Rămân suspicios mereu.", 70), 
                ("D) Niciodată. Odată trădat, ești șters definitiv.", 100)
            ]
        ),
        (
            "Te simți adesea singurul om lucid într-o lume de oameni falși și manipulatori?",
            "Superiority, Isolation, Misanthropy", 
            3, 
            [
                ("A) Nu, văd oameni buni peste tot.", 0), 
                ("B) Suntem toți complecși.", 30), 
                ("C) Uneori lumea pare falsă.", 60), 
                ("D) Da. Sunt singurul care vede realitatea crudă, restul sunt oi.", 100)
            ]
        )
    ]

    try:
        # 5. CURĂȚARE
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"Curățat întrebări vechi pentru Axa {AXIS_ID}.")

        # 6. INSERARE
        count = 0
        for q_text, tags, wave, opts in questions_data:
            v_hash = generate_hash(q_text, opts)
            
            c.execute("""
                INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (AXIS_ID, v_hash, q_text, tags, wave))
            
            labels = ['A', 'B', 'C', 'D']
            for idx, (opt_text, score) in enumerate(opts):
                c.execute("""
                    INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                    VALUES (?, ?, ?, ?)
                """, (v_hash, labels[idx], opt_text, score))
            count += 1

        conn.commit()
        log("db_conn", f"SUCCES: {count} întrebări inserate pentru {AXIS_NAME}.")

    except Exception as e:
        log_error(f"Eroare Axa {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()