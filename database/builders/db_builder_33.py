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
AXIS_ID = 33
AXIS_NAME = "Valori / Neconvenționalitate"
# Pol Stânga (0): Conformist / Tradiționalist / Dogmatic
# Pol Dreapta (100): Excentric / Liberal / Rebel

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
    # Punctaj: 0 = Conformist, 100 = Excentric
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Tradiție/Norme) ---
        (
            "Cum te raportezi la tradiții și obiceiuri vechi (sărbători, ritualuri sociale)?",
            "Tradition, Culture, Values", 
            1, 
            [
                ("A) Sunt sfinte. Ele ne definesc identitatea.", 0), 
                ("B) Le respect și particip la ele.", 30), 
                ("C) Unele sunt depășite, altele sunt ok.", 70), 
                ("D) Sunt o frână în calea progresului. Ar trebui eliminate.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să 'te integrezi' și să nu ieși în evidență într-un grup?",
            "Conformity, Social Pressure, Image", 
            1, 
            [
                ("A) Foarte important. Nu vreau să fiu oaia neagră.", 0), 
                ("B) Prefer să nu atrag atenția negativă.", 30), 
                ("C) Nu mă deranjează să fiu diferit.", 70), 
                ("D) Deloc. Îmi place să fiu unic și să șochez.", 100)
            ]
        ),
        (
            "Ce părere ai despre oamenii care au tatuaje vizibile, păr colorat strident sau stil vestimentar bizar?",
            "Openness, Judgment, Appearance", 
            1, 
            [
                ("A) Arată neprofesionist și ridicol.", 0), 
                ("B) Nu e stilul meu, dar e treaba lor.", 30), 
                ("C) Îmi place că au curaj.", 70), 
                ("D) Îi admir. Și eu am (sau aș vrea) un stil excentric.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Autoritate/Reguli) ---
        (
            "Dacă un șef sau o autoritate îți impune o regulă care ți se pare ilogică, ce faci?",
            "Authority, Rebellion, Compliance", 
            2, 
            [
                ("A) O respect fără comentarii. Ei știu mai bine.", 0), 
                ("B) O respect, dar mormăi.", 30), 
                ("C) O pun în discuție și cer argumente.", 70), 
                ("D) O ignor sau o încalc demonstrativ.", 100)
            ]
        ),
        (
            "Consideri că societatea are nevoie de reguli stricte și pedepse aspre pentru a funcționa?",
            "Politics, Order vs Chaos, Worldview", 
            2, 
            [
                ("A) Da, absolut. Ordinea e prioritară.", 0), 
                ("B) Da, legile trebuie respectate.", 30), 
                ("C) Regulile ar trebui să fie mai flexibile.", 70), 
                ("D) Nu. Libertatea individuală e mai importantă decât ordinea.", 100)
            ]
        ),
        (
            "Cât de des îți schimbi opiniile politice sau morale?",
            "Flexibility, Dogmatism, Values", 
            2, 
            [
                ("A) Niciodată. Am principii clare și fixe.", 0), 
                ("B) Rar.", 30), 
                ("C) Dacă apar argumente noi, le schimb.", 70), 
                ("D) Des. Totul este relativ, nu există adevăr absolut.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Antisocial / Rigiditate Extremă) ---
        (
            "Ai face ceva considerat 'imoral' de majoritate, dacă tu personal consideri că nu rănești pe nimeni?",
            "Morality, Ethics, Subjectivity", 
            3, 
            [
                ("A) Nu. Morala colectivă ne ghidează.", 0), 
                ("B) Probabil nu, m-aș simți vinovat.", 30), 
                ("C) Depinde despre ce e vorba.", 70), 
                ("D) Da. Morala e o construcție socială, eu am propriile reguli.", 100)
            ]
        ),
        (
            "Te atrag subiectele tabu, teoriile conspirației sau ideile marginale pe care majoritatea le respinge?",
            "Taboo, Curiosity, Fringe", 
            3, 
            [
                ("A) Nu, sunt aberații.", 0), 
                ("B) Sunt amuzante, dar nu le iau în serios.", 30), 
                ("C) Uneori, 'focul nu iese fără fum'.", 60), 
                ("D) Da, adevărul este adesea ascuns de mase.", 100)
            ]
        ),
        (
            "Îți place să provoci oamenii sau să fii 'avocatul diavolului' în discuții, doar pentru a vedea cum reacționează?",
            "Provocation, Trolling, Debate", 
            3, 
            [
                ("A) Nu, evit conflictul și polemica.", 0), 
                ("B) Doar dacă discuția o cere.", 30), 
                ("C) Uneori e distractiv să agiți apele.", 70), 
                ("D) Da, ador să șochez și să dărâm certitudinile altora.", 100)
            ]
        ),
        (
            "Te-ai descrie ca o persoană care prețuiește mai mult 'Siguranța' sau 'Libertatea'?",
            "Core Values, Security vs Freedom", 
            3, 
            [
                ("A) Siguranța. Fără ea nu avem nimic.", 0), 
                ("B) Siguranța, dar cu libertăți rezonabile.", 30), 
                ("C) Libertatea, cu riscurile aferente.", 70), 
                ("D) Libertatea totală. Mai bine mort decât în lanțuri.", 100)
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