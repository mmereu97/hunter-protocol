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
AXIS_ID = 36
AXIS_NAME = "Vulnerabilitate la Stres"
# Pol Stânga (0): Rezilient / Tare / Stăpân pe sine
# Pol Dreapta (100): Fragil / Copleșit / Panicat

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
    # Punctaj: 0 = Rezilient, 100 = Fragil
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Reacție la Criză) ---
        (
            "Ți se întâmplă ceva neprevăzut și neplăcut (ex: se strică mașina în drum spre un interviu, pierzi portofelul). Care e prima reacție?",
            "Crisis Management, Panic, Coping", 
            1, 
            [
                ("A) Rămân calm și caut o soluție alternativă.", 0), 
                ("B) Mă enervez puțin, dar acționez rațional.", 30), 
                ("C) Mă sperii și mă agit vizibil.", 70), 
                ("D) Intru în panică totală, îmi vine să plâng sau să renunț.", 100)
            ]
        ),
        (
            "Cum te simți când ai foarte multe sarcini de făcut într-un timp foarte scurt (multitasking sub presiune)?",
            "Workload, Pressure, Focus", 
            1, 
            [
                ("A) Motivat. Adrenalina mă ajută să fiu eficient.", 0), 
                ("B) Puțin stresat, dar le prioritizez.", 30), 
                ("C) Copleșit. Încep să fac greșeli.", 70), 
                ("D) Mă blochez. Nu știu de ce să mă apuc și nu fac nimic.", 100)
            ]
        ),
        (
            "După o zi extrem de stresantă sau o ceartă majoră, cât timp îți ia să îți revii la starea normală?",
            "Recovery, Resilience, Mood", 
            1, 
            [
                ("A) Câteva minute. Nu mă consum.", 0), 
                ("B) O oră sau două de relaxare.", 30), 
                ("C) O zi întreagă sunt dat peste cap.", 70), 
                ("D) Zile întregi. Mă simt epuizat și traumatizat.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Emoții/Ajutor) ---
        (
            "Când ești sub presiune mare, simți nevoia să vină cineva să te ajute sau să preia controlul?",
            "Dependency, Leadership, Stress", 
            2, 
            [
                ("A) Nu, prefer să am eu controlul.", 0), 
                ("B) Mă descurc singur, dar un sfat e bun.", 30), 
                ("C) Da, aș prefera să împart responsabilitatea.", 70), 
                ("D) Da, simt că nu pot face față singur.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să izbucnești în plâns sau să țipi necontrolat din cauza frustrării/stresului?",
            "Emotional Regulation, Breakdown", 
            2, 
            [
                ("A) Niciodată în public sau la muncă.", 0), 
                ("B) Foarte rar, în situații extreme.", 30), 
                ("C) Da, mi se întâmplă când se adună prea multe.", 70), 
                ("D) Da, sunt o persoană foarte emotivă sub stres.", 100)
            ]
        ),
        (
            "Dacă cineva te critică aspru și pe nedrept în fața altora, cum reacționezi?",
            "Criticism, Defense, Shame", 
            2, 
            [
                ("A) Mă apăr calm și cu argumente.", 0), 
                ("B) Mă enervez, dar mă abțin.", 30), 
                ("C) Mă simt umilit și îmi vine să plec.", 70), 
                ("D) Mă pierd cu firea, mă bâlbâi sau plâng.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Burnout / BPD / Victimizare) ---
        (
            "Simți adesea că viața este prea complicată și că nu poți face față cerințelor ei?",
            "Overwhelmed, Life Coping, Helplessness", 
            3, 
            [
                ("A) Nu. Îmi plac provocările vieții.", 0), 
                ("B) Uneori e greu, dar mă descurc.", 30), 
                ("C) Da, simt des că nu mai pot.", 70), 
                ("D) Da, mă simt neputincios și învins.", 100)
            ]
        ),
        (
            "Ai avut vreodată momente de 'îngheț' (freeze response) în care pur și simplu nu ai putut acționa de frică?",
            "Freeze Response, Fear, Trauma", 
            3, 
            [
                ("A) Nu, eu reacționez prin acțiune (Fight).", 0), 
                ("B) Nu îmi amintesc.", 20), 
                ("C) O dată sau de două ori.", 70), 
                ("D) Da, mi se întâmplă des să mă blochez mental.", 100)
            ]
        ),
        (
            "Eviți să îți asumi responsabilități noi sau să iei decizii importante de teamă că nu vei face față stresului?",
            "Avoidance, Anxiety, Career", 
            3, 
            [
                ("A) Nu, caut responsabilități.", 0), 
                ("B) Sunt precaut, dar nu evit.", 30), 
                ("C) Uneori refuz promovări din acest motiv.", 70), 
                ("D) Da, prefer un rol mic și sigur, fără stres.", 100)
            ]
        ),
        (
            "Cât de mult te afectează problemele altora? (ex: dacă un prieten e trist, devii și tu nefuncțional?)",
            "Emotional Contagion, Boundaries", 
            3, 
            [
                ("A) Îl ajut, dar rămân detașat.", 0), 
                ("B) Sunt empatic, dar nu mă dărâmă.", 30), 
                ("C) Mă afectează destul de tare.", 70), 
                ("D) Da, preiau tot stresul din jur ca un burete.", 100)
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