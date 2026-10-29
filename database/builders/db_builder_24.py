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
AXIS_ID = 24
AXIS_NAME = "Organizare"
# Pol Stânga (0): Haotic / Dezordonat / Spontan
# Pol Dreapta (100): Structurat / Ordonat / Meticulos

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
    # Punctaj: 0 = Haotic, 100 = Ordonat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Mediu Fizic/Obiceiuri) ---
        (
            "Cum arată de obicei biroul sau spațiul tău de lucru?",
            "Workspace, Tidiness, Habits", 
            1, 
            [
                ("A) 'Haos creativ'. Doar eu știu unde sunt lucrurile.", 0), 
                ("B) Destul de aglomerat, fac curat doar când e nevoie.", 30), 
                ("C) În mare parte ordonat.", 70), 
                ("D) Impecabil. Fiecare lucru are locul lui stabilit.", 100)
            ]
        ),
        (
            "Folosești liste de sarcini (To-Do lists) sau calendare pentru a te organiza?",
            "Planning, Tools, Structure", 
            1, 
            [
                ("A) Nu, țin minte sau improvizez.", 0), 
                ("B) Scriu pe bilețele, dar le pierd des.", 30), 
                ("C) Da, folosesc un calendar sau o agendă.", 70), 
                ("D) Da, viața mea e planificată la minut în aplicații dedicate.", 100)
            ]
        ),
        (
            "Cât de des ți se întâmplă să pierzi sau să rătăcești obiecte (chei, telefon, acte)?",
            "Attention, Neglect, Order", 
            1, 
            [
                ("A) Foarte des. Îmi petrec mult timp căutând chestii.", 0), 
                ("B) Uneori, când sunt grăbit.", 30), 
                ("C) Rar.", 70), 
                ("D) Niciodată. Știu exact unde e orice obiect.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Eficiență/Metodă) ---
        (
            "Dacă trebuie să pleci într-o călătorie, cum îți faci bagajul?",
            "Preparation, Planning, Spontaneity", 
            2, 
            [
                ("A) Arunc câteva haine în geantă cu 30 min înainte să plec.", 0), 
                ("B) Îl fac în seara dinainte, fără o listă.", 30), 
                ("C) Mă gândesc din timp ce îmi trebuie.", 70), 
                ("D) Fac o listă cu zile înainte și bifez fiecare obiect.", 100)
            ]
        ),
        (
            "Când primești un email important la care trebuie să răspunzi mai târziu, ce faci cu el?",
            "Digital Hygiene, Workflow", 
            2, 
            [
                ("A) Rămâne în Inbox printre alte mii de mailuri necitite.", 0), 
                ("B) Îl las 'Unread' ca să-l văd.", 30), 
                ("C) Îl pun într-un folder sau îi pun o etichetă (flag).", 70), 
                ("D) Îl trec în sistemul de task-uri și arhivez mailul (Inbox Zero).", 100)
            ]
        ),
        (
            "Cum te simți când intri într-o cameră dezordonată și murdară?",
            "Reaction to Disorder, Cleanliness", 
            2, 
            [
                ("A) Nu mă deranjează, nu observ detaliile.", 0), 
                ("B) E neplăcut, dar pot să ignor.", 30), 
                ("C) Mă deranjează, aș vrea să fie curat.", 70), 
                ("D) Simt o nevoie fizică urgentă de a face ordine.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Neglijență vs OCPD/Micromanagement) ---
        (
            "Ai tendința de a curăța sau rearanja lucrurile după alții pentru că nu le-au pus 'cum trebuie'?",
            "Control, Rigidity, OCPD", 
            3, 
            [
                ("A) Nu, nu-mi pasă cum le pun alții.", 0), 
                ("B) Doar dacă e mizerie mare.", 30), 
                ("C) Uneori, dacă e spațiul meu.", 70), 
                ("D) Da, mă irită dacă un obiect e mutat cu 2 cm.", 100)
            ]
        ),
        (
            "Cât de mult te bazezi pe proceduri standardizate versus improvizație în munca ta?",
            "Process, improvisation, Compliance", 
            3, 
            [
                ("A) Improvizez total. Procedurile mă sufocă.", 0), 
                ("B) Urmez liniile mari, dar fac cum simt.", 30), 
                ("C) Respect procedurile în majoritatea cazurilor.", 70), 
                ("D) Urmez procedura la virgulă. Regulile există cu un motiv.", 100)
            ]
        ),
        (
            "Te consideri o persoană care se concentrează pe 'Imaginea de ansamblu' sau pe 'Detalii'?",
            "Big Picture vs Detail, Perfectionism", 
            3, 
            [
                ("A) Imaginea de ansamblu. Detaliile mă plictisesc.", 0), 
                ("B) Mai mult ansamblu, dar verific și detaliile mari.", 30), 
                ("C) Echilibrat.", 60), 
                ("D) Detaliile sunt totul. O eroare mică strică tot.", 100)
            ]
        ),
        (
            "Ți se întâmplă să ratezi termene limită (deadline-uri) sau să întârzii la întâlniri din cauza lipsei de organizare?",
            "Punctuality, Reliability, Neglect", 
            3, 
            [
                ("A) Da, am o problemă cu timpul. Sunt mereu pe fugă.", 0), 
                ("B) Uneori, dacă sunt foarte aglomerat.", 30), 
                ("C) Foarte rar, sunt punctual.", 80), 
                ("D) Niciodată. Ajung mereu cu 10 minute mai devreme.", 100)
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