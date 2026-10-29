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
AXIS_ID = 29
AXIS_NAME = "Simțul Datoriei"
# Pol Stânga (0): Rebel / Nonconformist / Iresponsabil
# Pol Dreapta (100): Loial / Responsabil / Principial

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
    # Punctaj: 0 = Rebel (Risc), 100 = Responsabil (Safe)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Promisiuni/Reguli) ---
        (
            "Cât de important este pentru tine să îți respecți o promisiune, chiar dacă între timp a devenit foarte incomod să o faci?",
            "Promises, Honor, Reliability", 
            1, 
            [
                ("A) Deloc. Dacă nu mai îmi convine, renunț.", 0), 
                ("B) Inventez o scuză ca să scap.", 30), 
                ("C) Încerc să o renegociez, dar o fac dacă trebuie.", 70), 
                ("D) E crucial. Cuvântul meu este sfânt.", 100)
            ]
        ),
        (
            "Dacă găsești o regulă a companiei care ți se pare stupidă sau ineficientă, ce faci?",
            "Rules, Compliance, Rebelliousness", 
            1, 
            [
                ("A) O ignor complet și fac cum știu eu.", 0), 
                ("B) O ocolesc pe ascuns.", 30), 
                ("C) O respect, dar mă plâng de ea.", 70), 
                ("D) O respect cu strictețe până când se schimbă oficial.", 100)
            ]
        ),
        (
            "Cum te raportezi la autoritate și ierarhie?",
            "Authority, Rebellion, Respect", 
            1, 
            [
                ("A) Autoritatea trebuie sfidată. Nu-mi place să am șefi.", 0), 
                ("B) O tolerez, dar nu pun preț pe ea.", 30), 
                ("C) O respect în general.", 70), 
                ("D) Respect ierarhia și lanțul de comandă necondiționat.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Etică/Muncă) ---
        (
            "Ai luat vreodată concediu medical fără să fii bolnav, doar pentru că aveai nevoie de o zi liberă?",
            "Ethics, Integrity, Work", 
            2, 
            [
                ("A) Da, des. E dreptul meu.", 0), 
                ("B) O dată sau de două ori.", 30), 
                ("C) M-am gândit, dar nu am făcut-o.", 70), 
                ("D) Niciodată. Ar fi incorect față de firmă.", 100)
            ]
        ),
        (
            "Dacă primești restul greșit la magazin (mai mult), îl returnezi?",
            "Honesty, Small Stuff, Morality", 
            2, 
            [
                ("A) Nu, e norocul meu.", 0), 
                ("B) Depinde de sumă.", 30), 
                ("C) De obicei da.", 70), 
                ("D) Întotdeauna. Nu sunt banii mei.", 100)
            ]
        ),
        (
            "Dacă faci o greșeală la muncă pe care nimeni nu a observat-o și nu are impact imediat, o raportezi?",
            "Transparency, Responsibility, Guilt", 
            2, 
            [
                ("A) Nu, tac mâlc.", 0), 
                ("B) O repar pe ascuns și nu zic nimic.", 30), 
                ("C) O raportez dacă există riscul să se afle.", 60), 
                ("D) O raportez imediat. E datoria mea să fiu transparent.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Flight Risk / Neglijență / Integritate) ---
        (
            "Ce contează mai mult pentru tine: să faci 'ceea ce trebuie' (moral) sau să obții rezultatul dorit cu orice preț?",
            "Machiavellianism vs Duty, Philosophy", 
            3, 
            [
                ("A) Rezultatul. Istoria e scrisă de învingători.", 0), 
                ("B) Rezultatul, dar fără să calc pe cadavre.", 30), 
                ("C) Echilibrul între cele două.", 60), 
                ("D) Să fac ce e corect. Onoarea e mai importantă decât succesul.", 100)
            ]
        ),
        (
            "Ești dispus să îndeplinești sarcini care nu sunt în fișa postului tău, dacă asta ajută echipa?",
            "Citizenship, Role, Helpfulness", 
            3, 
            [
                ("A) Nu. 'Not my job'.", 0), 
                ("B) Doar dacă sunt plătit extra.", 30), 
                ("C) Da, ocazional.", 70), 
                ("D) Da, fac tot ce e nevoie pentru misiune.", 100)
            ]
        ),
        (
            "Dacă vezi un coleg încălcând regulamentul (ex: furt mărunt, pontaj fals), îl raportezi?",
            "Whistleblowing, Loyalty vs Duty", 
            3, 
            [
                ("A) Nu, nu sunt turnător.", 0), 
                ("B) Mă prefac că nu văd.", 20), 
                ("C) Îi atrag lui atenția.", 60), 
                ("D) Raportez superiorilor. Regulile sunt pentru toți.", 100)
            ]
        ),
        (
            "Cât de mult te simți 'dator' față de o companie care te-a angajat și te plătește corect?",
            "Loyalty, Flight Risk, Contract", 
            3, 
            [
                ("A) Deloc. E o tranzacție: timp contra bani.", 0), 
                ("B) Puțin, dar plec la prima ofertă mai bună.", 30), 
                ("C) Mă simt loial atâta timp cât sunt tratat bine.", 70), 
                ("D) Foarte loial. Nu aș pleca pentru o mărire mică.", 100)
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