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
AXIS_ID = 77
AXIS_NAME = "Burnout (Epuizare)"
# Pol 0: Energic / Motivat
# Pol 100: Epuizat / Cinic / Prăbușit

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
    log("sys", f"Populăm Clinicul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = BURNOUT (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Nivel Energie / Dimineața) ---
        (
            "Cum te simți dimineața, când sună alarma să mergi la muncă?",
            "Morning Dread, Energy, Motivation", 
            1, 
            [
                ("A) Odihnit și gata de treabă.", 0), 
                ("B) Puțin somnoros, dar ok.", 30), 
                ("C) Obosit, trag de mine să mă ridic.", 70), 
                ("D) Simt o greutate imensă, anxietate și nu vreau să mă dau jos din pat.", 100)
            ]
        ),
        (
            "Cât de des te simți 'stors' emoțional la finalul programului?",
            "Emotional Exhaustion, Workload", 
            1, 
            [
                ("A) Rar. Mai am energie și pentru hobby-uri.", 0), 
                ("B) Uneori, după zile grele.", 30), 
                ("C) Destul de des, vreau doar liniște.", 70), 
                ("D) Zilnic. Sunt o 'legumă' când ajung acasă.", 100)
            ]
        ),
        (
            "Mai găsești sens sau satisfacție în munca pe care o faci?",
            "Meaning, Cynicism, Engagement", 
            1, 
            [
                ("A) Da, îmi place ce fac.", 0), 
                ("B) E un job ok, plătește facturile.", 30), 
                ("C) Mă întreb des ce caut acolo.", 70), 
                ("D) Nu. Totul mi se pare inutil și frustrant.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Cinism / Detașare) ---
        (
            "Ai devenit mai critic sau mai cinic față de colegi, clienți sau șefi în ultima vreme?",
            "Cynicism, Irritability, Depersonalization", 
            2, 
            [
                ("A) Nu, am răbdare cu ei.", 0), 
                ("B) Poate puțin mai ironic.", 30), 
                ("C) Da, mă irită mult mai repede.", 70), 
                ("D) Da, nu îi mai suport. Îmi vine să urlu la ei.", 100)
            ]
        ),
        (
            "Simți că muncești mult, dar realizezi puțin (eficiență scăzută)?",
            "Professional Efficacy, Brain Fog", 
            2, 
            [
                ("A) Nu, sunt productiv.", 0), 
                ("B) Am zile și zile.", 20), 
                ("C) Da, mă concentrez greu.", 70), 
                ("D) Da, stau ore întregi în fața ecranului fără să fac nimic.", 100)
            ]
        ),
        (
            "Ai simptome fizice pe care le asociezi cu munca (dureri de cap, spate, insomnii)?",
            "Somatic, Stress, Health", 
            2, 
            [
                ("A) Nu, sunt sănătos.", 0), 
                ("B) O ușoară tensiune uneori.", 30), 
                ("C) Da, dorm prost duminica seara.", 70), 
                ("D) Da, am probleme de sănătate cauzate direct de stresul de la job.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Colaps Total) ---
        (
            "Te-ai gândit să îți dai demisia fără să ai un alt plan, doar ca să scapi?",
            "Desperation, Flight Risk", 
            3, 
            [
                ("A) Nu, ar fi iresponsabil.", 0), 
                ("B) Mă uit după alte joburi, dar nu plec oricum.", 30), 
                ("C) M-a bătut gândul.", 70), 
                ("D) Da. Sunt la un pas să plec și să nu mă mai uit înapoi.", 100)
            ]
        ),
        (
            "Simți că jobul te-a transformat într-o persoană pe care nu o mai placi (mai rea, mai tristă)?",
            "Identity, Personality Change", 
            3, 
            [
                ("A) Nu, separ jobul de viață.", 0), 
                ("B) Sunt doar mai obosit.", 30), 
                ("C) Da, sunt mai morocănos acasă.", 70), 
                ("D) Da, m-a distrus. Nu mai sunt eu.", 100)
            ]
        ),
        (
            "Îți pasă dacă firma dă faliment sau proiectul eșuează?",
            "Apathy, Detachment", 
            3, 
            [
                ("A) Da, îmi pasă de munca mea.", 0), 
                ("B) M-ar afecta financiar.", 20), 
                ("C) Nu prea mai îmi pasă.", 70), 
                ("D) Sincer, m-aș bucura să văd totul arzând.", 100)
            ]
        ),
        (
            "Cât de aproape simți că ești de o cădere nervoasă (breakdown)?",
            "Mental Health, Crisis", 
            3, 
            [
                ("A) Foarte departe.", 0), 
                ("B) Gestionez stresul, e ok.", 20), 
                ("C) Sunt la limită.", 70), 
                ("D) Simt că clachez în orice moment.", 100)
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