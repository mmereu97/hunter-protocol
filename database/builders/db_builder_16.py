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
AXIS_ID = 16
AXIS_NAME = "Vivacitate (Energie)"
# Pol Stânga (0): Lent / Pasiv / Relaxat
# Pol Dreapta (100): Energic / Dinamic / Activ

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
    # Punctaj: 0 = Lent, 100 = Energic
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Ritm Zilnic) ---
        (
            "Cum ți-ai descrie ritmul obișnuit de viață?",
            "Lifestyle, Pace, Daily Routine", 
            1, 
            [
                ("A) Foarte lent, 'ardelenesc'. Nu mă grăbesc nicăieri.", 0), 
                ("B) Moderat, îmi iau timp să savurez momentele.", 30), 
                ("C) Alert, am mereu ceva de făcut.", 70), 
                ("D) Frenetic. Sunt mereu pe fugă, 'în priză'.", 100)
            ]
        ),
        (
            "Cum te comporți când mergi pe stradă, chiar și fără o destinație urgentă?",
            "Walking Speed, Energy Level", 
            1, 
            [
                ("A) Mă plimb încet, mă uit la vitrine.", 0), 
                ("B) Mers normal, relaxat.", 30), 
                ("C) Merg destul de repede, depășesc oameni.", 70), 
                ("D) Aproape alerg. Mersul încet mă enervează.", 100)
            ]
        ),
        (
            "Cum arată o zi liberă ideală pentru tine?",
            "Relaxation vs Action, Hobbies", 
            1, 
            [
                ("A) Lenevit în pat, Netflix, somn.", 0), 
                ("B) O plimbare ușoară și o cafea.", 30), 
                ("C) Sport, curățenie sau un proiect personal.", 70), 
                ("D) O zi plină de activități de dimineața până seara.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Vorbire) ---
        (
            "La muncă sau în proiecte, preferi sarcinile care cer...",
            "Work Style, Tasks", 
            2, 
            [
                ("A) Răbdare, migală și ritm constant.", 0), 
                ("B) Analiză liniștită.", 30), 
                ("C) Multitasking și diversitate.", 70), 
                ("D) Viteză de reacție, presiune și acțiune intensă.", 100)
            ]
        ),
        (
            "Ți s-a spus vreodată că vorbești prea repede sau că ești agitat?",
            "Communication, Feedback, Energy", 
            2, 
            [
                ("A) Nu, mi se spune că sunt prea calm/lent.", 0), 
                ("B) Nu, vorbesc normal.", 30), 
                ("C) Uneori, când sunt entuziasmat.", 70), 
                ("D) Da, des. Oamenii abia țin pasul cu mine.", 100)
            ]
        ),
        (
            "Cât de mult poți sta așezat într-un loc (ex: la birou sau cinema) fără să simți nevoia să te miști?",
            "Restlessness, Physical, Patience", 
            2, 
            [
                ("A) Ore întregi, îmi place să stau.", 0), 
                ("B) Destul de mult, dacă e interesant.", 30), 
                ("C) Încep să mă foiesc după o oră.", 70), 
                ("D) Foarte puțin. Trebuie să mă ridic, să mă mișc.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Burnout / ADHD / Loafing) ---
        (
            "Te simți vinovat sau inutil dacă stai degeaba și nu faci nimic productiv?",
            "Productivity, Guilt, Workaholism", 
            3, 
            [
                ("A) Deloc. 'Dolce far niente' e o artă.", 0), 
                ("B) Mă bucur de odihnă fără remușcări.", 30), 
                ("C) Simt că pierd timpul dacă exagerez cu pauzele.", 70), 
                ("D) Da, trebuie să fiu mereu ocupat ca să mă simt bine.", 100)
            ]
        ),
        (
            "Ai tendința de a te implica în mai multe activități decât poți duce, doar pentru că vrei acțiune?",
            "Overcommitment, Enthusiasm, Limits", 
            3, 
            [
                ("A) Nu, îmi conserv energia. Fac strictul necesar.", 0), 
                ("B) Îmi știu limitele.", 30), 
                ("C) Uneori mă aglomerez.", 70), 
                ("D) Da, spun DA la tot și ajung să alerg haotic.", 100)
            ]
        ),
        (
            "Dimineața, te trezești plin de energie sau îți ia mult timp să 'pornești motoarele'?",
            "Morning Energy, Circadian Rhythm", 
            3, 
            [
                ("A) Sunt foarte lent dimineața, am nevoie de timp.", 0), 
                ("B) Mă trezesc treptat.", 30), 
                ("C) Sunt funcțional destul de repede.", 70), 
                ("D) Sar din pat gata de treabă imediat.", 100)
            ]
        ),
        (
            "Cum reacționezi când trebuie să lucrezi cu oameni care se mișcă sau gândesc lent?",
            "Patience, Teamwork, Frustration", 
            3, 
            [
                ("A) Îi înțeleg, nici eu nu mă grăbesc.", 0), 
                ("B) Mă adaptez la ritmul lor.", 30), 
                ("C) Mă impacientez puțin.", 60), 
                ("D) Mă enervează cumplit. Îmi vine să fac eu în locul lor.", 100)
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