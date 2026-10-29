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
AXIS_ID = 35
AXIS_NAME = "Emoții Pozitive (Optimism)"
# Pol Stânga (0): Pesimist / Melancolic / Serios
# Pol Dreapta (100): Optimist / Vesel / Exuberant

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
    # Punctaj: 0 = Pesimist, 100 = Optimist
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Stare Generală) ---
        (
            "În general, cum ai descrie atitudinea ta față de viață?",
            "Outlook, Optimism, Worldview", 
            1, 
            [
                ("A) Viața e grea și plină de dezamăgiri.", 0), 
                ("B) Sunt realist, văd lucrurile așa cum sunt.", 30), 
                ("C) Încerc să văd partea plină a paharului.", 70), 
                ("D) Viața e minunată! Sunt un optimist incurabil.", 100)
            ]
        ),
        (
            "Cât de des râzi cu poftă sau zâmbești pe parcursul unei zile obișnuite?",
            "Laughter, Joy, Expressiveness", 
            1, 
            [
                ("A) Foarte rar. Nu prea am motive.", 0), 
                ("B) Ocazional, la glume bune.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Tot timpul. Râsul e terapia mea.", 100)
            ]
        ),
        (
            "Cum reacționezi când primești o veste bună (ex: o mărire de salariu, un cadou)?",
            "Reaction to Success, Enthusiasm", 
            1, 
            [
                ("A) Sunt sceptic. Mă întreb ce urmează rău.", 0), 
                ("B) Mă bucur interior, dar rămân calm.", 30), 
                ("C) Mă bucur vizibil și împărtășesc cu alții.", 70), 
                ("D) Sunt euforic, sar în sus de bucurie!", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Viitor/Energie) ---
        (
            "Când te gândești la viitorul tău, care este sentimentul dominant?",
            "Future, Hope, Anxiety", 
            2, 
            [
                ("A) Îngrijorare. Cred că lucrurile vor merge prost.", 0), 
                ("B) Incertitudine.", 30), 
                ("C) Speranță. Cred că va fi bine.", 70), 
                ("D) Nerăbdare și entuziasm. Viitorul sună bine!", 100)
            ]
        ),
        (
            "Te entuziasmezi ușor pentru lucruri mici (o zi însorită, o melodie bună, o mâncare gustoasă)?",
            "Small Pleasures, Sensitivity", 
            2, 
            [
                ("A) Nu. Sunt lucruri banale.", 0), 
                ("B) Rareori.", 30), 
                ("C) Da, îmi plac micile plăceri.", 70), 
                ("D) Da! Mă bucur ca un copil de orice lucru frumos.", 100)
            ]
        ),
        (
            "Prietenii te-ar descrie mai degrabă ca fiind 'serios' sau 'vesel'?",
            "Reputation, Social Persona", 
            2, 
            [
                ("A) Serios, chiar posomorât uneori.", 0), 
                ("B) Rezervat.", 30), 
                ("C) Prietenos și deschis.", 70), 
                ("D) Sufletul petrecerii, mereu cu zâmbetul pe buze.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Depresie / Anhedonie vs Manie) ---
        (
            "Ai momente când te simți 'gol' interior și incapabil să simți bucurie, chiar dacă faci lucruri care îți plăceau?",
            "Anhedonia, Depression Check", 
            3, 
            [
                ("A) Da, foarte des. (Risc Anhedonie)", 0), 
                ("B) Uneori, când sunt foarte stresat.", 30), 
                ("C) Foarte rar.", 70), 
                ("D) Niciodată. Am mereu poftă de viață.", 100)
            ]
        ),
        (
            "Crezi că fericirea este o stare naturală sau ceva pentru care trebuie să muncești din greu?",
            "Philosophy, Happiness", 
            3, 
            [
                ("A) Fericirea e o iluzie sau o raritate.", 0), 
                ("B) E un premiu pentru muncă.", 30), 
                ("C) E o alegere de atitudine.", 70), 
                ("D) Este starea mea naturală de a fi.", 100)
            ]
        ),
        (
            "Dacă ți se întâmplă ceva rău dimineața, îți strică dispoziția pentru tot restul zilei?",
            "Resilience, Mood Stability", 
            3, 
            [
                ("A) Da, rămân nervos sau trist toată ziua.", 0), 
                ("B) Îmi ia câteva ore să îmi revin.", 30), 
                ("C) Mă afectează pe moment, dar trec peste.", 70), 
                ("D) Nu. Mă scutur și zâmbesc din nou în 5 minute.", 100)
            ]
        ),
        (
            "Ai tendința să fii sarcastic sau ironic când vezi oameni foarte fericiți?",
            "Cynicism, Jealousy", 
            3, 
            [
                ("A) Da, mi se par falși sau naivi.", 0), 
                ("B) Uneori, dacă exagerează.", 30), 
                ("C) Nu, mă bucur pentru ei.", 70), 
                ("D) Nu, entuziasmul lor e contagios, mă alătur lor!", 100)
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