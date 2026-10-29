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
AXIS_ID = 40
AXIS_NAME = "Gândire Abstractă / Raționament (IQ)"
# Pol Stânga (0): Gândire Concretă / Pratic / Lent
# Pol Dreapta (100): Gândire Abstractă / Analitic / Rapid

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
    # Punctaj: 0 = Concret, 100 = Abstract
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Învățare/Rezolvare Probleme) ---
        (
            "Când trebuie să înveți un lucru nou și complicat (un soft, o procedură), cât de repede prinzi ideea?",
            "Learning Speed, Intelligence, Adaptability", 
            1, 
            [
                ("A) Am nevoie de timp și de multe repetiții.", 0), 
                ("B) Învăț într-un ritm mediu, dacă mi se explică clar.", 30), 
                ("C) Destul de repede.", 70), 
                ("D) Prind 'din zbor', imediat înțeleg logica din spate.", 100)
            ]
        ),
        (
            "Preferi sarcinile care sunt clare și repetitive sau pe cele care necesită găsirea unor soluții noi?",
            "Work Style, Complexity, Concrete vs Abstract", 
            1, 
            [
                ("A) Clare și repetitive. Nu îmi plac surprizele.", 0), 
                ("B) Prefer să știu ce am de făcut.", 30), 
                ("C) Îmi place să mai schimb, să gândesc puțin.", 70), 
                ("D) Cele complexe. Rutina mă omoară, vreau să-mi folosesc mintea.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să înțelegi concepte teoretice sau filozofice (ex: discuții despre economie, politică globală, metafizică)?",
            "Abstract Thinking, Theory, Interest", 
            1, 
            [
                ("A) Foarte greu. Mă plictisesc sau mă pierd.", 0), 
                ("B) Prefer exemplele practice.", 30), 
                ("C) Le înțeleg dacă sunt explicate bine.", 70), 
                ("D) Foarte ușor. Jonglez cu idei abstracte de plăcere.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Tipare/Analiză) ---
        (
            "Observi adesea legături sau tipare între evenimente aparent neconectate?",
            "Pattern Recognition, Intuition, Logic", 
            2, 
            [
                ("A) Nu, văd lucrurile separat.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori fac conexiuni interesante.", 70), 
                ("D) Da, văd 'sistemul' din spatele lucrurilor constant.", 100)
            ]
        ),
        (
            "Dacă citești un manual de instrucțiuni, ai nevoie de poze și pași exacți sau înțelegi principiul rapid?",
            "Comprehension, Instruction, Logic", 
            2, 
            [
                ("A) Am nevoie de poze și pași detaliați, altfel mă blochez.", 0), 
                ("B) Citesc cu atenție tot textul.", 30), 
                ("C) Frunzăresc și înțeleg esențialul.", 70), 
                ("D) De multe ori nici nu-l deschid, deduc singur cum funcționează.", 100)
            ]
        ),
        (
            "Cum te descurci cu jocurile de strategie, șah sau puzzle-uri logice?",
            "Strategy, Gaming, IQ", 
            2, 
            [
                ("A) Nu îmi plac, sunt prea obositoare.", 0), 
                ("B) Mă descurc onorabil, dar nu strălucesc.", 30), 
                ("C) Sunt bun la ele.", 70), 
                ("D) Sunt expert. Îmi place să anticipez mutările adversarului.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Intelectualizare / Rigiditate Cognitivă / Aroganță) ---
        (
            "Te enervezi când oamenii din jur nu înțeleg lucruri care ție ți se par evidente?",
            "Patience, Intelligence Gap, Arrogance", 
            3, 
            [
                ("A) Nu, poate eu nu explic bine.", 0), 
                ("B) Am răbdare.", 30), 
                ("C) Uneori mă frustrează.", 70), 
                ("D) Da, mă irită prostia sau încetineala altora.", 100)
            ]
        ),
        (
            "Când ai o problemă, te bazezi mai mult pe 'ce s-a mai făcut' (precedent) sau încerci să inventezi o soluție originală?",
            "Innovation, Tradition vs Modernity", 
            3, 
            [
                ("A) Merg pe calea bătătorită. E sigură.", 0), 
                ("B) Întreb pe alții cum au făcut.", 30), 
                ("C) Combin metode vechi cu idei noi.", 60), 
                ("D) Caut o soluție originală și optimizată. Îmi place să inovez.", 100)
            ]
        ),
        (
            "Îți place să analizezi o problemă din mai multe perspective, chiar și cele contradictorii, sau vrei răspunsul corect rapid?",
            "Critical Thinking, Nuance, Depth", 
            3, 
            [
                ("A) Vreau răspunsul clar și scurt.", 0), 
                ("B) Analizez puțin, dar decid repede.", 30), 
                ("C) Îmi place să dezbat opțiunile.", 70), 
                ("D) Ador complexitatea și nuanțele. Adevărul e rar simplu.", 100)
            ]
        ),
        (
            "Te simți epuizat mental după o perioadă de gândire intensă sau te simți energizat?",
            "Cognitive Stamina, Intellectual Need", 
            3, 
            [
                ("A) Epuizat. Gânditul intens mă obosește.", 0), 
                ("B) Obosesc ca după orice muncă.", 30), 
                ("C) Mă simt bine că am rezolvat ceva.", 70), 
                ("D) Energizat. Provocările intelectuale sunt 'hrana' mea.", 100)
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