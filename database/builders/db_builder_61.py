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
AXIS_ID = 61
AXIS_NAME = "Interes Investigativ (Știință)"
# Pol Stânga (0): Intuitiv / Pratic / Non-academic
# Pol Dreapta (100): Analitic / Curios / Academic

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
    # Punctaj: 0 = Neinteresat, 100 = Investigativ (Cercetător)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Curiozitate Generală) ---
        (
            "Ce fel de articole sau știri îți atrag atenția cel mai des?",
            "Reading, Interests, Science vs Gossip", 
            1, 
            [
                ("A) Bârfe, vedete, sport sau divertisment ușor.", 0), 
                ("B) Știri generale despre ce se întâmplă în lume.", 30), 
                ("C) Articole despre tehnologie sau descoperiri noi.", 70), 
                ("D) Studii științifice, analize aprofundate, documentare.", 100)
            ]
        ),
        (
            "Când te confrunți cu o problemă complexă (ex: de ce nu merge o mașinărie, o eroare de soft), ce faci?",
            "Problem Solving, Analysis", 
            1, 
            [
                ("A) Mă enervez și chem pe cineva să o repare.", 0), 
                ("B) Încerc soluțiile evidente (restart, lovit).", 30), 
                ("C) Caut pe Google să văd dacă alții au pățit la fel.", 70), 
                ("D) Îmi place provocarea. Investighez cauza și încerc să înțeleg mecanismul.", 100)
            ]
        ),
        (
            "Cum ți s-a părut matematica și științele exacte în școală?",
            "School, Math, Logic", 
            1, 
            [
                ("A) Un coșmar. Le uram.", 0), 
                ("B) Grele, dar necesare.", 30), 
                ("C) Interesante, dacă erau predate bine.", 70), 
                ("D) Materiile mele preferate. Îmi plăcea logica lor.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Stil de Muncă/Carieră) ---
        (
            "Dacă ai putea alege un job ideal, ce ai prefera să faci toată ziua?",
            "Career Choice, RIASEC", 
            2, 
            [
                ("A) Să vând ceva sau să conving oameni.", 0), 
                ("B) Să construiesc ceva fizic cu mâinile.", 30), 
                ("C) Să organizez date și dosare.", 60), 
                ("D) Să fac muncă de detectiv/cercetare și să rezolv mistere.", 100)
            ]
        ),
        (
            "Îți place să analizezi grafice, statistici și date numerice pentru a găsi tendințe?",
            "Data Analysis, Statistics", 
            2, 
            [
                ("A) Nu, cifrele mă plictisesc sau mă amețesc.", 0), 
                ("B) Doar dacă e necesar pentru o concluzie simplă.", 30), 
                ("C) Da, sunt utile pentru decizii.", 70), 
                ("D) Da, ador să 'sap' în date și să găsesc adevărul ascuns.", 100)
            ]
        ),
        (
            "Preferi munca practică, unde vezi rezultatul fizic imediat, sau munca intelectuală, abstractă?",
            "Abstract vs Concrete, Work Style", 
            2, 
            [
                ("A) Practică. Vreau să văd ce am făcut.", 0), 
                ("B) O combinație echilibrată.", 30), 
                ("C) Mai mult intelectuală.", 70), 
                ("D) Intelectuală. Ideile și teoriile mă fascinează cel mai mult.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Sindromul Turnului de Fildeș / Lipsă Pragmatism) ---
        (
            "Te pasionează să înțelegi 'de ce' funcționează lucrurile, chiar dacă nu îți folosește practic la nimic?",
            "Curiosity, Theory vs Practice", 
            3, 
            [
                ("A) Nu. Dacă nu e util, e informație degeaba.", 0), 
                ("B) Rar, doar dacă e ceva curios.", 30), 
                ("C) Da, cultura generală e importantă.", 70), 
                ("D) Da. Cunoașterea e un scop în sine pentru mine.", 100)
            ]
        ),
        (
            "Ai răbdare să lucrezi la o problemă dificilă zile sau săptămâni la rând, fără să ai garanția succesului?",
            "Persistence, Research, Grit", 
            3, 
            [
                ("A) Nu. Vreau rezultate rapide.", 0), 
                ("B) Mă frustrez repede dacă nu văd progres.", 30), 
                ("C) Am răbdare dacă miza e mare.", 70), 
                ("D) Da, procesul de descoperire e la fel de important ca rezultatul.", 100)
            ]
        ),
        (
            "Ce te atrage mai mult: un laborator de cercetare sau o sală de ședințe plină de oameni?",
            "Environment, Social vs Intellectual", 
            3, 
            [
                ("A) Sala de ședințe. Îmi place interacțiunea.", 0), 
                ("B) Niciuna, prefer munca de teren.", 20), 
                ("C) Depinde de proiect.", 50), 
                ("D) Laboratorul. Liniște, concentrare și descoperire.", 100)
            ]
        ),
        (
            "Te consideri o persoană care gândește științific și sceptic, cerând mereu dovezi?",
            "Scientific Method, Skepticism", 
            3, 
            [
                ("A) Nu, mă bazez pe intuiție și credință.", 0), 
                ("B) Uneori.", 30), 
                ("C) În general da.", 70), 
                ("D) Absolut. Fără dovezi, o afirmație nu valorează nimic.", 100)
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