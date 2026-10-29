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
AXIS_ID = 25
AXIS_NAME = "Hărnicie"
# Pol Stânga (0): Procrastinator / Relaxat / Leneș
# Pol Dreapta (100): Disciplinat / Muncitor / Voință

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
    # Punctaj: 0 = Leneș, 100 = Harnic
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Obiceiuri Zilnice) ---
        (
            "Când ai o sarcină dificilă de făcut, dar care nu este urgentă (ex: curățenie generală, un raport lung), cum procedezi?",
            "Procrastination, Tasks, Habits", 
            1, 
            [
                ("A) O amân până în ultima secundă posibilă.", 0), 
                ("B) Îmi găsesc alte lucruri mai mici de făcut înainte.", 30), 
                ("C) O planific și mă apuc de ea rezonabil de repede.", 70), 
                ("D) O fac prima, ca să scap de ea ('Eat the frog').", 100)
            ]
        ),
        (
            "Cum te comporți când ești obosit, dar mai ai de lucru pentru a atinge un obiectiv?",
            "Stamina, Resilience, Effort", 
            1, 
            [
                ("A) Mă opresc imediat. Nu are rost să mă forțez.", 0), 
                ("B) Mai fac puțin, apoi cedez.", 30), 
                ("C) Iau o pauză scurtă și continui.", 70), 
                ("D) Trag de mine până termin. Nu mă culc până nu e gata.", 100)
            ]
        ),
        (
            "Ce părere ai despre 'munca grea' (hard work)?",
            "Work Ethic, Philosophy", 
            1, 
            [
                ("A) Este pentru cei care nu știu să lucreze inteligent.", 0), 
                ("B) E necesară, dar nu trebuie exagerat.", 30), 
                ("C) Este cheia succesului în majoritatea cazurilor.", 70), 
                ("D) Este o virtute. Mă simt împlinit când muncesc din greu.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Obiective/Auto-disciplină) ---
        (
            "Cât de des reușești să îți ții rezoluțiile de Anul Nou sau obiectivele personale pe termen lung?",
            "Goals, Consistency, Willpower", 
            2, 
            [
                ("A) Niciodată. Renunț după prima săptămână.", 0), 
                ("B) Rareori, îmi pierd entuziasmul.", 30), 
                ("C) Destul de des, dacă sunt importante.", 70), 
                ("D) Aproape întotdeauna. Sunt foarte disciplinat.", 100)
            ]
        ),
        (
            "Dacă lucrezi de acasă (fără supraveghere), cât de productiv ești comparativ cu biroul?",
            "Self-Discipline, Remote Work, Focus", 
            2, 
            [
                ("A) Mult mai puțin. Mă iau cu alte treburi casnice/TV.", 0), 
                ("B) Încep mai greu, dar fac strictul necesar.", 30), 
                ("C) La fel de productiv.", 70), 
                ("D) Mai productiv. Nu mă întrerupe nimeni și muncesc intens.", 100)
            ]
        ),
        (
            "Cum abordezi sarcinile plictisitoare sau repetitive?",
            "Boredom Tolerance, Duty", 
            2, 
            [
                ("A) Le evit sau le pasez altcuiva.", 0), 
                ("B) Le fac cu greață și multe pauze.", 30), 
                ("C) Le fac pentru că trebuie făcute.", 70), 
                ("D) Le fac rapid și eficient, fac parte din job.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Loafing / Neglijență) ---
        (
            "Te bazezi adesea pe 'inspirație' sau 'chef' pentru a lucra?",
            "Motivation, Discipline vs Mood", 
            3, 
            [
                ("A) Da, dacă nu am chef, nu fac nimic.", 0), 
                ("B) În mare parte, da. E greu fără inspirație.", 30), 
                ("C) Nu, disciplina bate motivația.", 70), 
                ("D) Nu. Sunt ca un soldat, execut ce trebuie indiferent de stare.", 100)
            ]
        ),
        (
            "Ai tendința să lași lucrurile neterminate și să începi altele noi?",
            "Completion, Follow-through", 
            3, 
            [
                ("A) Da, am zeci de proiecte abandonate.", 0), 
                ("B) Se întâmplă când îmi pierd interesul.", 30), 
                ("C) Rar, încerc să finalizez.", 70), 
                ("D) Niciodată. Mă obsedează lucrurile lăsate la jumătate.", 100)
            ]
        ),
        (
            "Dacă ai putea să ai un venit pasiv care să îți acopere toate nevoile, ai mai munci?",
            "Motivation, Lifestyle, Idleness", 
            3, 
            [
                ("A) Nu. Aș sta toată ziua la plajă/jocuri.", 0), 
                ("B) M-aș ocupa doar de hobby-uri relaxante.", 30), 
                ("C) Da, aș face voluntariat sau ceva util.", 70), 
                ("D) Da, aș munci la fel de mult, dar la proiectele mele. Nu pot sta degeaba.", 100)
            ]
        ),
        (
            "Cât de des întârzii cu predarea lucrărilor (deadline-uri)?",
            "Reliability, Deadlines", 
            3, 
            [
                ("A) Foarte des. Am mereu nevoie de extensii.", 0), 
                ("B) Uneori, pe ultima sută de metri.", 30), 
                ("C) Foarte rar.", 80), 
                ("D) Niciodată. Predau chiar înainte de termen.", 100)
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