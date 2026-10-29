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
AXIS_ID = 95
AXIS_NAME = "Loafing (Chiul Social)"
# Pol 0: Implicat / Proactiv
# Pol 100: Parazit / Leneș / Pasager

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

    # Punctaj: 100 = LOAFING (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Munca în Echipă) ---
        (
            "Când lucrezi într-un grup mare, simți că poți să te relaxezi puțin pentru că muncesc ceilalți?",
            "Teamwork, Effort, Responsibility", 
            1, 
            [
                ("A) Nu, trag la fel de tare sau mai tare.", 0), 
                ("B) Îmi fac partea mea, nimic în plus.", 30), 
                ("C) Da, e mai puțină presiune pe mine.", 70), 
                ("D) Da, mă las 'dus de val'. De ce să mă agit?", 100)
            ]
        ),
        (
            "Cum procedezi când ai o sarcină pe care nu știi să o faci sau nu ai chef de ea?",
            "Problem Solving, Delegation, Laziness", 
            1, 
            [
                ("A) O învăț și o fac.", 0), 
                ("B) Cer ajutor ca să învăț.", 30), 
                ("C) O pasez subtil unui coleg care se pricepe.", 70), 
                ("D) O ignor sau mă fac că am uitat de ea.", 100)
            ]
        ),
        (
            "Cât de des iei pauze lungi de cafea/țigară/socializare în timpul programului?",
            "Time Theft, Distraction, Work Ethic", 
            1, 
            [
                ("A) Foarte rar. Sunt concentrat.", 0), 
                ("B) Pauze normale, scurte.", 30), 
                ("C) Destul de des, am nevoie de relaxare.", 70), 
                ("D) Des. Munca nu fuge.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Efort Minim / Scuze) ---
        (
            "Dacă șeful nu e la birou o zi întreagă, cât de mult muncești?",
            "Supervision, Motivation, Integrity", 
            2, 
            [
                ("A) La fel ca de obicei.", 0), 
                ("B) Poate un ritm puțin mai lejer.", 30), 
                ("C) Mă relaxez vizibil, rezolv chestii personale.", 70), 
                ("D) Plec mai devreme sau nu fac nimic toată ziua.", 100)
            ]
        ),
        (
            "Ești expert în a părea ocupat chiar și când nu faci nimic important?",
            "Appearance vs Reality, Deception", 
            2, 
            [
                ("A) Nu, nu știu să mă prefac.", 0), 
                ("B) Nu, prefer să fiu util.", 20), 
                ("C) Uneori, ca să nu fiu deranjat.", 70), 
                ("D) Da, e o artă. Merg repede cu foi în mână.", 100)
            ]
        ),
        (
            "Când un proiect se apropie de deadline și e nevoie de ore suplimentare, ce faci?",
            "Crunch Time, Commitment", 
            2, 
            [
                ("A) Rămân cot la cot cu echipa.", 0), 
                ("B) Rămân dacă sunt plătit.", 30), 
                ("C) Găsesc un motiv să plec la fix.", 70), 
                ("D) Mă îmbolnăvesc subit sau am o 'urgență' acasă.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Parazitism / Lipsă de Rușine) ---
        (
            "Te deranjează dacă primești același bonus ca un coleg care a muncit dublu față de tine?",
            "Fairness, Entitlement, Conscience", 
            3, 
            [
                ("A) Da, m-aș simți prost. Nu e corect.", 0), 
                ("B) Puțin, dar nu refuz banii.", 30), 
                ("C) Nu. Dacă am fost 'deștept', merit.", 70), 
                ("D) Deloc. Prost e cine muncește, nu cine cere.", 100)
            ]
        ),
        (
            "Ai obiceiul să lași sarcinile grele pentru 'cineva care se pricepe mai bine'?",
            "Avoidance, Competence", 
            3, 
            [
                ("A) Nu, îmi plac provocările.", 0), 
                ("B) Încerc, apoi cer ajutor.", 20), 
                ("C) Da, de ce să mă chinui eu?", 70), 
                ("D) Mereu. Sunt 'manager de idei', nu executant.", 100)
            ]
        ),
        (
            "Dacă echipa eșuează din cauza ta (pentru că nu ți-ai făcut partea), recunoști?",
            "Accountability, Blame", 
            3, 
            [
                ("A) Da, îmi asum vina.", 0), 
                ("B) Recunosc parțial.", 30), 
                ("C) Încerc să mă ascund în grup.", 70), 
                ("D) Nu. Găsesc scuze sau dau vina pe lipsa de comunicare.", 100)
            ]
        ),
        (
            "Care este motto-ul tău la muncă?",
            "Work Philosophy", 
            3, 
            [
                ("A) Fă treaba cât poți de bine.", 0), 
                ("B) Muncește ca să trăiești.", 30), 
                ("C) Fă minimul necesar ca să nu fii dat afară.", 70), 
                ("D) Munca e pentru tractoare. Eu sunt aici pentru salariu.", 100)
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