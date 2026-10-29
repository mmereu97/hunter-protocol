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
AXIS_ID = 37
AXIS_NAME = "Ostilitate (Furie)"
# Pol Stânga (0): Calm / Pașnic / Controlat
# Pol Dreapta (100): Furios / Agresiv / Vulcanic

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
    # Punctaj: 0 = Calm, 100 = Furios
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Iritări Zilnice) ---
        (
            "Cât de des ți se întâmplă să te simți furios sau iritat pe parcursul unei săptămâni obișnuite?",
            "Frequency, Temper, Mood", 
            1, 
            [
                ("A) Aproape niciodată. Sunt o persoană foarte calmă.", 0), 
                ("B) O dată sau de două ori, dacă am motive.", 30), 
                ("C) Destul de des, multe lucruri mă enervează.", 70), 
                ("D) Zilnic. Simt o tensiune constantă.", 100)
            ]
        ),
        (
            "Dacă cineva îți taie calea în trafic sau se bagă în fața ta la coadă, cum reacționezi?",
            "Traffic, Social Conflict, Impulse", 
            1, 
            [
                ("A) Îl ignor, poate se grăbește.", 0), 
                ("B) Mă deranjează, dar nu zic nimic.", 30), 
                ("C) Îl claxonez sau îi fac observație pe un ton ridicat.", 70), 
                ("D) Mă înfurii teribil, înjur sau îmi vine să mă dau jos la el.", 100)
            ]
        ),
        (
            "Când un aparat (telefon, PC) nu funcționează cum trebuie, îți vine să îl lovești?",
            "Frustration Tolerance, Physical Aggression", 
            1, 
            [
                ("A) Nu, caut o soluție rațională.", 0), 
                ("B) Mă enervez, dar mă controlez.", 30), 
                ("C) Uneori dau cu pumnul în masă.", 70), 
                ("D) Da, am spart câteva telefoane/tastaturi de nervi.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Conflict/Verbal) ---
        (
            "În timpul unei certe aprinse, ai tendința să ridici vocea sau să țipi pentru a te face auzit?",
            "Conflict Style, Verbal Aggression", 
            2, 
            [
                ("A) Nu, vorbesc calm indiferent de situație.", 0), 
                ("B) Doar dacă și celălalt țipă.", 30), 
                ("C) Da, ridic tonul destul de repede.", 70), 
                ("D) Da, urlu și pot deveni intimidant.", 100)
            ]
        ),
        (
            "Dacă cineva te jignește, cât de greu îți este să nu ripostezi imediat?",
            "Retaliation, Self-Control", 
            2, 
            [
                ("A) Ușor. Nu mă cobor la nivelul lor.", 0), 
                ("B) Mă abțin, dar mă consumă.", 30), 
                ("C) E foarte greu, de obicei răspund acid.", 70), 
                ("D) Imposibil. Cine mă atacă, o pățește pe loc.", 100)
            ]
        ),
        (
            "Prietenii sau familia ți-au spus vreodată că ai un temperament vulcanic sau că le e frică de reacțiile tale?",
            "Feedback, Reputation, Fear", 
            2, 
            [
                ("A) Nu, sunt cunoscut ca pacifist.", 0), 
                ("B) Nu, poate doar că sunt puțin morocănos uneori.", 30), 
                ("C) Mi s-a spus să mă calmez.", 70), 
                ("D) Da, știu că trebuie să aibă grijă să nu mă enerveze.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Agresivitate Fizică / Antisocial / BPD) ---
        (
            "Ai fost vreodată implicat într-o altercație fizică (bătaie, îmbrânceli) la vârsta adultă?",
            "Physical Violence, History, Risk", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) O singură dată, m-am apărat.", 20), 
                ("C) De câteva ori.", 70), 
                ("D) Da, mi se întâmplă să ajung la pumni.", 100)
            ]
        ),
        (
            "Când ești extrem de furios, simți nevoia să distrugi ceva (să trântești ușa, să arunci cu obiecte) pentru a te elibera?",
            "Destructiveness, Venting, Rage", 
            3, 
            [
                ("A) Nu, prefer să mă plimb sau să respir adânc.", 0), 
                ("B) Trântesc ușa uneori, dar atât.", 30), 
                ("C) Da, am nevoie să lovesc ceva (o pernă, un perete).", 70), 
                ("D) Da, fac praf ce am în jur când 'mi se pune pata'.", 100)
            ]
        ),
        (
            "Ai simțit vreodată o furie atât de intensă încât ai avut senzația că pierzi controlul asupra propriilor acțiuni?",
            "Loss of Control, Blackout, Rage", 
            3, 
            [
                ("A) Nu, sunt mereu stăpân pe mine.", 0), 
                ("B) Am fost foarte furios, dar conștient.", 30), 
                ("C) M-am speriat de cât de nervos eram.", 70), 
                ("D) Da, 'mi se pune ceață pe ochi' și nu mai știu ce fac.", 100)
            ]
        ),
        (
            "Consideri că uneori violența (verbală sau fizică) este singura soluție pentru a rezolva o problemă?",
            "Beliefs, Violence Justification", 
            3, 
            [
                ("A) Nu, violența nu e niciodată o soluție.", 0), 
                ("B) Doar în legitimă apărare fizică.", 20), 
                ("C) Uneori e nevoie să fii dur ca să te faci înțeles.", 70), 
                ("D) Da, unii oameni doar de frică știu.", 100)
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