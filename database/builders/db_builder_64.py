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
AXIS_ID = 64
AXIS_NAME = "Interes Convențional (RIASEC C)"
# Pol Stânga (0): Improvizație / Artistic
# Pol Dreapta (100): Date / Cifre / Birocrație

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
    # Punctaj: 0 = Improvizație, 100 = Convențional (Date/Reguli)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Generale) ---
        (
            "Cum te simți când trebuie să completezi formulare detaliate, să faci dosare sau să organizezi acte?",
            "Admin, Paperwork, Patience", 
            1, 
            [
                ("A) Este o tortură. Le amân cât pot.", 0), 
                ("B) E plictisitor, dar necesar.", 30), 
                ("C) Nu mă deranjează, măcar e clar ce am de făcut.", 70), 
                ("D) Îmi place. Mă relaxează să pun ordine în hârtii.", 100)
            ]
        ),
        (
            "Îți place să lucrezi în Excel, să faci tabele, grafice și să gestionezi baze de date?",
            "Excel, Data, Software", 
            1, 
            [
                ("A) Nu. Mă doare capul de la atâtea cifre.", 0), 
                ("B) Doar funcțiile de bază.", 30), 
                ("C) Mă descurc bine și e util.", 70), 
                ("D) Da! Ador să văd cum datele se așază perfect.", 100)
            ]
        ),
        (
            "Preferi un job unde sarcinile sunt clare, repetitive și bine definite, sau unul unde trebuie să inventezi soluții noi zilnic?",
            "Routine vs Innovation, Career", 
            1, 
            [
                ("A) Să inventez. Rutina mă omoară.", 0), 
                ("B) Prefer varietatea.", 30), 
                ("C) Prefer claritatea și structura.", 70), 
                ("D) Sarcini clare și repetitive. Vreau să știu exact ce am de făcut.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Precizie/Rol) ---
        (
            "Dacă ai organiza un eveniment, ce rol ți-ar plăcea?",
            "Role, Planning vs Execution", 
            2, 
            [
                ("A) Să fiu gazda care întreține atmosfera.", 0), 
                ("B) Să vin cu idei pentru tematică.", 20), 
                ("C) Să coordonez echipa.", 50), 
                ("D) Să țin bugetul, lista de invitați și logistica.", 100)
            ]
        ),
        (
            "Cât de multă satisfacție îți oferă găsirea unei greșeli mici într-un document lung (ex: o virgulă, o cifră greșită)?",
            "Proofreading, Detail Oriented", 
            2, 
            [
                ("A) Niciuna. E enervant.", 0), 
                ("B) Nu observ de obicei.", 30), 
                ("C) Mă bucur că am corectat-o.", 70), 
                ("D) O mare satisfacție. Îmi place să 'vânez' erori.", 100)
            ]
        ),
        (
            "Te atrag domeniile precum Contabilitate, Arhivistică, Programare, Statistică sau Audit?",
            "Career Interest, RIASEC C", 
            2, 
            [
                ("A) Nu, sună teribil de plictisitor.", 0), 
                ("B) Poate programare, că e creativă.", 30), 
                ("C) Statistică sau Audit sună bine.", 70), 
                ("D) Da, sunt domeniile mele ideale.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: OCPD / Rigiditate Birocratică) ---
        (
            "Te simți pierdut sau anxios dacă nu ai instrucțiuni precise despre cum să faci un lucru?",
            "Ambiguity Intolerance, Structure Need", 
            3, 
            [
                ("A) Nu, îmi place să improvizez.", 0), 
                ("B) Mă descurc și fără.", 30), 
                ("C) Prefer instrucțiunile.", 70), 
                ("D) Da. Dacă nu există o procedură, nu mă apuc.", 100)
            ]
        ),
        (
            "Crezi că lumea ar fi un loc mai bun dacă toată lumea ar respecta regulile și procedurile la sânge?",
            "Worldview, Order vs Chaos", 
            3, 
            [
                ("A) Nu, ar fi o lume de roboți.", 0), 
                ("B) Ar fi prea rigid.", 30), 
                ("C) Ar fi mai multă ordine.", 70), 
                ("D) Absolut. Haosul vine din nerespectarea regulilor.", 100)
            ]
        ),
        (
            "Îți place să clasifici, să sortezi și să pui etichete pe lucruri (fisiere, colecții, obiecte)?",
            "Categorization, Organizing", 
            3, 
            [
                ("A) Nu, am totul la grămadă.", 0), 
                ("B) Fac curat când e nevoie.", 30), 
                ("C) Îmi place să am foldere organizate.", 70), 
                ("D) Da, e o activitate relaxantă și necesară. Totul trebuie etichetat.", 100)
            ]
        ),
        (
            "Ești dispus să verifici aceeași listă de date de 3 ori pentru a fi sigur că e 100% corectă?",
            "Accuracy, Perfectionism, Patience", 
            3, 
            [
                ("A) Nu, verific o dată și sper să fie bine.", 0), 
                ("B) Mă plictisesc repede.", 20), 
                ("C) De obicei verific de două ori.", 60), 
                ("D) Da. Precizia este mai importantă decât viteza.", 100)
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