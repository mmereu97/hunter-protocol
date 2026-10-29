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
AXIS_ID = 79
AXIS_NAME = "Cronotip"
# Pol Stânga (0): Matinal / Ciocârlie / Early Bird
# Pol Dreapta (100): Vespertin / Bufniță / Night Owl

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
    # Punctaj: 0 = Matinal, 100 = Nocturn
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Generale) ---
        (
            "Dacă ai fi complet liber să îți organizezi ziua (fără muncă, fără alarmă), la ce oră te-ai trezi în mod natural?",
            "Wake Up Time, Biology, Circadian", 
            1, 
            [
                ("A) 05:00 - 07:30.", 0), 
                ("B) 07:30 - 09:00.", 30), 
                ("C) 09:00 - 11:00.", 70), 
                ("D) După ora 11:00 sau la prânz.", 100)
            ]
        ),
        (
            "În ce moment al zilei simți că ai cea mai mare claritate mentală și energie?",
            "Peak Energy, Productivity, Focus", 
            1, 
            [
                ("A) Dimineața devreme (8:00 - 11:00).", 0), 
                ("B) La prânz sau după-amiază.", 30), 
                ("C) Seara (18:00 - 22:00).", 70), 
                ("D) Noaptea târziu. Atunci sunt genial.", 100)
            ]
        ),
        (
            "Cum te simți în prima jumătate de oră după ce te-ai trezit dimineața?",
            "Morning Mood, Grogginess", 
            1, 
            [
                ("A) Gata de acțiune, înfometat și energic.", 0), 
                ("B) Puțin somnoros, dar ok.", 30), 
                ("C) 'Nu-mi vorbiți'. Am nevoie de cafea ca să funcționez.", 70), 
                ("D) Ca un zombi. Fizic sunt treaz, mental dorm încă o oră.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Program de lucru/Social) ---
        (
            "Dacă ar trebui să faci o muncă fizică grea sau un antrenament intens, când ai prefera să fie?",
            "Exercise, Physical Peak", 
            2, 
            [
                ("A) Dimineața la 8:00.", 0), 
                ("B) Pe la 11:00 - 12:00.", 30), 
                ("C) După-amiaza târziu.", 70), 
                ("D) Seara. Dimineața nu am forță.", 100)
            ]
        ),
        (
            "Trebuie să lucrezi la un proiect care necesită concentrare maximă timp de 3 ore. Ce interval alegi?",
            "Deep Work, Schedule", 
            2, 
            [
                ("A) 08:00 - 11:00.", 0), 
                ("B) 14:00 - 17:00.", 30), 
                ("C) 20:00 - 23:00.", 70), 
                ("D) 23:00 - 02:00.", 100)
            ]
        ),
        (
            "Cât de greu îți este să te culci la ora 22:00 și să adormi rapid?",
            "Sleep Onset, Insomnia", 
            2, 
            [
                ("A) Foarte ușor, la ora aia mi-e somn.", 0), 
                ("B) Rezonabil.", 30), 
                ("C) Greu, mă foiesc în pat.", 70), 
                ("D) Imposibil. Atunci sunt cel mai treaz.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Burnout / Tulburări de Somn / Incompatibilitate Job) ---
        (
            "Dacă ești forțat să te trezești la ora 6:00 dimineața mai multe zile la rând, cum reacționezi?",
            "Sleep Deprivation, Adaptation", 
            3, 
            [
                ("A) Mă obișnuiesc repede, e ok.", 0), 
                ("B) Sunt obosit, dar rezist.", 30), 
                ("C) Devin irascibil și neproductiv.", 70), 
                ("D) Mă îmbolnăvesc fizic sau clachez nervos. E tortură.", 100)
            ]
        ),
        (
            "Ai apetit dimineața la scurt timp după trezire?",
            "Breakfast, Metabolism", 
            3, 
            [
                ("A) Da, micul dejun e masa principală.", 0), 
                ("B) Pot mânca ceva ușor.", 30), 
                ("C) Nu prea.", 70), 
                ("D) Nu pot înghiți nimic până la prânz, doar cafea.", 100)
            ]
        ),
        (
            "Ai tendința să amâni ora de culcare (Revenge Bedtime Procrastination) doar pentru a avea timp pentru tine, chiar dacă știi că vei fi obosit?",
            "Habits, Psychology, Late Night", 
            3, 
            [
                ("A) Nu, somnul e prioritar.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori.", 60), 
                ("D) Da, noaptea e singurul moment când mă simt liber.", 100)
            ]
        ),
        (
            "Dacă ai putea alege un job cu ture, pe care l-ai alege?",
            "Shift Work, Preference", 
            3, 
            [
                ("A) Tura 1 (07:00 - 15:00).", 0), 
                ("B) Program normal (09:00 - 17:00).", 20), 
                ("C) Tura 2 (14:00 - 22:00).", 80), 
                ("D) Tura de noapte sau program flexibil care începe la prânz.", 100)
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