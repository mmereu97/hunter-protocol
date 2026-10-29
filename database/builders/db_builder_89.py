import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# DEFINIȚII
AXIS_ID = 89
AXIS_NAME = "Agresivitate"
# Pol 0: Calm / Pașnic
# Pol 100: Periculos / Violent / Agresiv

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm Monstrul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = AGRESIV (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Controlul Furiei) ---
        (
            "Când ești foarte nervos, simți nevoia fizică de a lovi ceva (un perete, o masă, un obiect)?",
            "Physical Urge, Anger, Destruction", 
            1, 
            [
                ("A) Nu, prefer să mă plimb sau să respir.", 0), 
                ("B) Uneori strâng pumnii, dar mă abțin.", 30), 
                ("C) Da, trântesc uși sau obiecte.", 70), 
                ("D) Da, trebuie să lovesc ceva ca să mă calmez.", 100)
            ]
        ),
        (
            "Cât de des intri în conflicte verbale aprinse cu necunoscuți (în trafic, la coadă, pe stradă)?",
            "Conflict Frequency, Road Rage", 
            1, 
            [
                ("A) Niciodată. Evit scandalul.", 0), 
                ("B) Rar, doar dacă sunt provocat grav.", 30), 
                ("C) Destul de des, oamenii sunt idioți.", 70), 
                ("D) Frecvent. Nu las pe nimeni să mă calce pe coadă.", 100)
            ]
        ),
        (
            "Dacă cineva te jignește grav, care e primul impuls?",
            "Retaliation, Impulse, Violence", 
            1, 
            [
                ("A) Să plec sau să îl ignor.", 0), 
                ("B) Să îi răspund sarcastic.", 30), 
                ("C) Să îl înjur și să urlu la el.", 70), 
                ("D) Să îl lovesc.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Istoric Violent) ---
        (
            "Ai fost vreodată implicat într-o bătaie fizică la vârsta adultă?",
            "Violence History, Physical Fight", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) O dată, m-am apărat.", 30), 
                ("C) De câteva ori.", 80), 
                ("D) Da, am avut multe altercații.", 100)
            ]
        ),
        (
            "Când ai consumat alcool, devii mai prietenos sau mai pus pe harță?",
            "Alcohol, Disinhibition, Aggression", 
            2, 
            [
                ("A) Mai vesel sau adorm.", 0), 
                ("B) La fel ca de obicei.", 20), 
                ("C) Devin mai irascibil.", 60), 
                ("D) Devin agresiv și caut scandal.", 100)
            ]
        ),
        (
            "Ai amenințat vreodată pe cineva că îi faci rău fizic?",
            "Threats, Intimidation", 
            2, 
            [
                ("A) Nu, niciodată.", 0), 
                ("B) Poate în glumă.", 20), 
                ("C) Da, la nervi, dar nu am făcut-o.", 70), 
                ("D) Da, și am vorbit serios.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Risc Extrem / Patologie) ---
        (
            "Ai folosit vreodată un obiect (bâtă, cuțit, sticlă) într-o ceartă pentru a intimida sau răni?",
            "Weapons, Lethal Risk", 
            3, 
            [
                ("A) Doamne ferește, nu!", 0), 
                ("B) Nu.", 0), 
                ("C) Am ținut ceva în mână doar defensiv.", 70), 
                ("D) Da.", 100)
            ]
        ),
        (
            "Crezi că violența este uneori singura modalitate de a rezolva o problemă cu anumiți oameni?",
            "Beliefs, Justification of Violence", 
            3, 
            [
                ("A) Nu, violența naște violență.", 0), 
                ("B) Doar în caz de război sau apărare extremă.", 20), 
                ("C) Uneori, unii înțeleg doar de frică.", 70), 
                ("D) Da, bătaia e ruptă din rai. Rezolvă multe.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să 'ți se pună ceață pe ochi' de nervi și să nu mai știi ce faci (Blackout Rage)?",
            "Loss of Control, Rage", 
            3, 
            [
                ("A) Nu, sunt mereu conștient.", 0), 
                ("B) Am fost foarte furios, dar nu am pierdut controlul.", 30), 
                ("C) Am fost aproape.", 70), 
                ("D) Da, mi se întâmplă când explodez.", 100)
            ]
        ),
        (
            "Te simți puternic și respectat atunci când ceilalți se tem de tine?",
            "Intimidation, Ego, Respect vs Fear", 
            3, 
            [
                ("A) Nu, vreau să fiu iubit, nu temut.", 0), 
                ("B) Vreau să fiu respectat pentru competență.", 20), 
                ("C) Puțină teamă impune respect.", 60), 
                ("D) Da. E mai bine să le fie frică decât să te ia peste picior.", 100)
            ]
        )
    ]

    try:
        # CLEANUP & INSERT
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))

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
        
        conn.commit()
        log("db_conn", f"SUCCES: {len(questions_data)} întrebări inserate pentru {AXIS_NAME}.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()