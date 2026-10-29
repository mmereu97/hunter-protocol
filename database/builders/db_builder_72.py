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
AXIS_ID = 72
AXIS_NAME = "Grit (Perseverență)"
# Pol Stânga (0): Renunță ușor / Inconstant
# Pol Dreapta (100): Tenace / Rezilient / Dedicat

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
    # Punctaj: 0 = Renunță, 100 = Tenace
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Consistență) ---
        (
            "Cât de des ți se întâmplă să începi un proiect nou cu mult entuziasm, dar să îți pierzi interesul după câteva luni?",
            "Consistency, Projects, Interest", 
            1, 
            [
                ("A) Foarte des. Am multe proiecte neterminate.", 0), 
                ("B) Uneori, dacă găsesc ceva mai interesant.", 30), 
                ("C) Rar. Încerc să termin ce încep.", 70), 
                ("D) Niciodată. Dacă m-am apucat, îl duc la capăt indiferent de timp.", 100)
            ]
        ),
        (
            "Cum reacționezi când te lovești de un obstacol major sau un eșec în atingerea unui scop?",
            "Resilience, Failure, Coping", 
            1, 
            [
                ("A) Mă descurajez și caut altceva de făcut.", 0), 
                ("B) Iau o pauză lungă să mă gândesc.", 30), 
                ("C) Mă enervez, dar caut soluții.", 60), 
                ("D) Mă motivează și mai tare. Nu accept înfrângerea.", 100)
            ]
        ),
        (
            "Ai aceleași interese și obiective profesionale acum ca și acum 3-4 ani, sau se schimbă frecvent?",
            "Long Term Goals, Focus", 
            1, 
            [
                ("A) Se schimbă des. Îmi place diversitatea.", 0), 
                ("B) S-au schimbat parțial.", 30), 
                ("C) În mare parte sunt aceleași.", 70), 
                ("D) Da, am o direcție clară pe care o urmez de ani de zile.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Efort/Muncă) ---
        (
            "Consideri că succesul este determinat mai mult de talentul înnăscut sau de efortul susținut?",
            "Growth Mindset, Effort, Philosophy", 
            2, 
            [
                ("A) De talent și noroc.", 0), 
                ("B) Talentul e baza, munca ajută.", 30), 
                ("C) Efortul contează mai mult.", 70), 
                ("D) Efortul este totul. Talentul fără muncă e inutil.", 100)
            ]
        ),
        (
            "Ești capabil să lucrezi la o sarcină plictisitoare sau dificilă luni de zile, fără să vezi rezultate imediate, doar pentru că face parte dintr-un plan mai mare?",
            "Delayed Gratification, Discipline", 
            2, 
            [
                ("A) Nu. Am nevoie de rezultate rapide.", 0), 
                ("B) E foarte greu, îmi pierd răbdarea.", 30), 
                ("C) Pot, dacă știu că merită.", 70), 
                ("D) Da. Sunt maratonist, nu sprinter.", 100)
            ]
        ),
        (
            "Comparativ cu majoritatea oamenilor, te consideri o persoană care muncește mai mult ('hard worker')?",
            "Self-Image, Work Ethic", 
            2, 
            [
                ("A) Nu, prefer să muncesc 'smart', nu mult.", 0), 
                ("B) Sunt în medie.", 30), 
                ("C) Da, sunt destul de harnic.", 60), 
                ("D) Da, sunt dispus să muncesc oricât e nevoie.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: ADHD / Lipsă Voință / Flight Risk) ---
        (
            "Ai un scop suprem (o 'busolă') care îți ghidează majoritatea acțiunilor zilnice de ani de zile?",
            "Life Purpose, Focus", 
            3, 
            [
                ("A) Nu, trăiesc momentul.", 0), 
                ("B) Am obiective pe termen scurt.", 30), 
                ("C) Am o idee generală despre ce vreau.", 60), 
                ("D) Da, tot ce fac este aliniat cu misiunea mea.", 100)
            ]
        ),
        (
            "Dacă eșuezi lamentabil într-un proiect important, cât timp îți ia să te ridici și să încerci din nou?",
            "Recovery, Persistence", 
            3, 
            [
                ("A) Renunț la proiect. Nu a fost să fie.", 0), 
                ("B) Îmi ia mult timp să îmi revin.", 30), 
                ("C) Câteva zile de supărare, apoi reîncep.", 70), 
                ("D) Imediat. Eșecul este doar o lecție.", 100)
            ]
        ),
        (
            "Te bazezi pe motivație (chef) sau pe disciplină (obligație auto-impusă) pentru a progresa?",
            "Discipline vs Motivation", 
            3, 
            [
                ("A) Pe chef. Dacă nu am chef, iese prost.", 0), 
                ("B) Am nevoie de inspirație.", 30), 
                ("C) Încerc să fiu disciplinat.", 60), 
                ("D) Disciplină pură. Fac ce trebuie, indiferent cum mă simt.", 100)
            ]
        ),
        (
            "Preferi să știi câte puțin din toate (să schimbi des domeniile) sau să devii maestru într-un singur domeniu, chiar dacă durează 10 ani?",
            "Depth vs Breadth, Mastery", 
            3, 
            [
                ("A) Puțin din toate. Mă plictisesc repede.", 0), 
                ("B) Schimb domeniul la câțiva ani.", 30), 
                ("C) Prefer specializarea.", 70), 
                ("D) Maestru. Vreau să fiu cel mai bun într-un singur lucru.", 100)
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