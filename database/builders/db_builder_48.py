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
AXIS_ID = 48
AXIS_NAME = "Auto-suficiență"
# Pol Stânga (0): Dependent de Grup / Muncă în Echipă
# Pol Dreapta (100): Lup Singuratic / Auto-suficient / Individualist

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
    # Punctaj: 0 = Grup (Team), 100 = Singur (Solo)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe de Lucru) ---
        (
            "Când ai de rezolvat o sarcină complexă la muncă sau la școală, cum preferi să lucrezi?",
            "Work Style, Teamwork vs Solo", 
            1, 
            [
                ("A) În echipă, făcând brainstorming.", 0), 
                ("B) Prefer să am parteneri de discuție.", 30), 
                ("C) Prefer să lucrez singur, dar accept feedback.", 70), 
                ("D) Complet singur. Mă concentrez mai bine și merg mai repede.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să te consulți cu alții înainte de a lua o decizie finală?",
            "Decision Making, Consensus, Autonomy", 
            1, 
            [
                ("A) Esențial. Nu vreau să greșesc singur.", 0), 
                ("B) Important, vreau să aud alte păreri.", 30), 
                ("C) Uneori întreb, dar decid eu.", 70), 
                ("D) Deloc. Am încredere totală în judecata mea.", 100)
            ]
        ),
        (
            "Ce simți când auzi cuvântul 'Teambuilding' sau 'Proiect de Grup'?",
            "Social, Corporate, Attitude", 
            1, 
            [
                ("A) Entuziasm. Îmi place să fiu cu oamenii.", 0), 
                ("B) E o ocazie bună de socializare.", 30), 
                ("C) O obligație necesară.", 60), 
                ("D) Groază sau plictiseală. Prefer să îmi fac treaba și atât.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Rezolvare Probleme/Independență) ---
        (
            "Dacă te blochezi la o problemă tehnică, care e primul instinct?",
            "Problem Solving, Help Seeking", 
            2, 
            [
                ("A) Întreb imediat pe cineva.", 0), 
                ("B) Încerc puțin, apoi întreb.", 30), 
                ("C) Caut pe Google sau în manuale.", 70), 
                ("D) Mă chinui ore în șir singur până o rezolv. Nu cer ajutor.", 100)
            ]
        ),
        (
            "Dacă grupul decide o direcție cu care nu ești de acord, ce faci?",
            "Conformity, Independence, Groupthink", 
            2, 
            [
                ("A) Mă conformez pentru binele grupului.", 0), 
                ("B) Îmi spun părerea, dar accept majoritatea.", 30), 
                ("C) Încerc să îi conving sau mă retrag.", 70), 
                ("D) Fac cum știu eu că e bine, indiferent de ce zic ei.", 100)
            ]
        ),
        (
            "Cât de mult timp poți petrece singur fără să te simți izolat sau plictisit?",
            "Solitude, Needs", 
            2, 
            [
                ("A) Foarte puțin. Am nevoie de oameni în jur.", 0), 
                ("B) O zi sau două.", 30), 
                ("C) Destul de mult.", 70), 
                ("D) Oricât. Sunt cea mai bună companie a mea.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Schizoid / Narcisism / Antisocial) ---
        (
            "Consideri că, de cele mai multe ori, ceilalți oameni doar te încetinesc și te încurcă?",
            "Efficiency, Arrogance, Misanthropy", 
            3, 
            [
                ("A) Nu, munca în echipă e mai eficientă.", 0), 
                ("B) Uneori e greu de coordonat.", 30), 
                ("C) Da, adesea pierd timp explicând.", 70), 
                ("D) Da. Sunt mult mai eficient singur. Ceilalți sunt o frână.", 100)
            ]
        ),
        (
            "Te simți vreodată ca un intrus sau un observator detașat, chiar și în grupurile de prieteni?",
            "Alienation, Detachment, Schizoid", 
            3, 
            [
                ("A) Nu, mă simt conectat.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori simt că nu aparțin.", 60), 
                ("D) Da, mereu. Sunt o insulă.", 100)
            ]
        ),
        (
            "Crezi în zicala: 'Dacă vrei un lucru bine făcut, fă-l singur'?",
            "Philosophy, Trust, Control", 
            3, 
            [
                ("A) Nu, delegarea e cheia.", 0), 
                ("B) E o zicală cinică.", 30), 
                ("C) Are un sâmbure de adevăr.", 60), 
                ("D) Este regula mea de aur în viață.", 100)
            ]
        ),
        (
            "Dacă ești forțat să colaborezi strâns cu cineva zi de zi, cum te simți?",
            "Collaboration, Stress, Independence", 
            3, 
            [
                ("A) Mă bucur de companie.", 0), 
                ("B) E ok, ne obișnuim.", 30), 
                ("C) Mă obosește, am nevoie de spațiu.", 70), 
                ("D) Sufocat și frustrat. Îmi scade randamentul drastic.", 100)
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