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
AXIS_ID = 80
AXIS_NAME = "Sensibilitate Senzorială (HSP)"
# Pol Stânga (0): Tanc / Insensibil / Rezistent
# Pol Dreapta (100): HSP / Hipersensibil / Delicat

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
    # Punctaj: 0 = Tanc (Insensibil), 100 = HSP (Hipersensibil)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Mediu/Zgomot) ---
        (
            "Cum te simți într-un mediu foarte aglomerat, cu zgomot puternic și lumini intense (ex: mall aglomerat, concert, open space haotic)?",
            "Environment, Noise, Overwhelm", 
            1, 
            [
                ("A) Mă simt energizat, îmi place agitația.", 0), 
                ("B) Mă obișnuiesc, nu mă deranjează.", 30), 
                ("C) Mă obosește după o vreme.", 70), 
                ("D) Mă simt copleșit rapid și simt nevoia urgentă să plec într-un loc liniștit.", 100)
            ]
        ),
        (
            "Te deranjează lucrurile tactile precum etichetele de la haine, materialele aspre sau o pietricică în pantof?",
            "Tactile, Comfort, Irritation", 
            1, 
            [
                ("A) Deloc. Pot purta orice.", 0), 
                ("B) Rar observ așa ceva.", 30), 
                ("C) Da, tai etichetele dacă mă zgârie.", 70), 
                ("D) Extrem de tare. Nu pot să mă concentrez la nimic altceva până nu rezolv disconfortul.", 100)
            ]
        ),
        (
            "Cât de ușor te sperii dacă cineva se furișează în spatele tău sau se aude un zgomot brusc?",
            "Startle Response, Nerves", 
            1, 
            [
                ("A) Greu. Am nervi de oțel.", 0), 
                ("B) Normal.", 30), 
                ("C) Tresar destul de ușor.", 70), 
                ("D) Sar în sus de spaimă. Am un reflex de tresărire foarte puternic.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Detalii/Muncă) ---
        (
            "La locul de muncă, dacă ai de făcut mai multe lucruri deodată și ești întrerupt des, cum reacționezi?",
            "Multitasking, Stress, Focus", 
            2, 
            [
                ("A) Mă descurc excelent, îmi place ritmul alert.", 0), 
                ("B) Mă organizez și le fac pe rând.", 30), 
                ("C) Devin stresat și ineficient.", 70), 
                ("D) Mă blochez total ('shutdown'). Creierul meu refuză să mai proceseze.", 100)
            ]
        ),
        (
            "Observi detalii subtile în mediul tău pe care alții le ratează (un miros vag, o schimbare de lumină, o mutare de mobilă)?",
            "Perception, Details, Awareness", 
            2, 
            [
                ("A) Nu, sunt atent la imaginea de ansamblu.", 0), 
                ("B) Uneori.", 30), 
                ("C) Da, am spirit de observație bun.", 70), 
                ("D) Da, observ totul. Uneori aș vrea să pot ignora detaliile.", 100)
            ]
        ),
        (
            "Cât de mult te afectează foamea? (Devii 'Hangry' - nervos din cauza foamei?)",
            "Physiology, Mood, Hunger", 
            2, 
            [
                ("A) Pot să sar peste mese fără probleme.", 0), 
                ("B) Mi se face foame, dar sunt calm.", 30), 
                ("C) Devin puțin irascibil.", 70), 
                ("D) Da, îmi schimbă complet personalitatea și nu mă pot concentra.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Autism / Anxietate / Burnout) ---
        (
            "Ai nevoie să te retragi în pat sau într-o cameră întunecată după o zi plină pentru a-ți reveni?",
            "Decompression, Solitude, Energy", 
            3, 
            [
                ("A) Nu, ies în oraș să mă relaxez.", 0), 
                ("B) Mă uit la TV.", 30), 
                ("C) Uneori am nevoie de liniște.", 70), 
                ("D) Da. Sistemul meu nervos este 'prăjit' și am nevoie de izolare totală.", 100)
            ]
        ),
        (
            "Eviți să te uiți la filme violente sau la știri negative pentru că te afectează prea profund?",
            "Empathy, Media Sensitivity", 
            3, 
            [
                ("A) Nu, îmi plac filmele horror/acțiune.", 0), 
                ("B) Mă uit, e doar un film.", 30), 
                ("C) Nu îmi plac cele foarte sângeroase.", 70), 
                ("D) Da. Imaginile violente mă bântuie zile întregi.", 100)
            ]
        ),
        (
            "Cât de sensibil ești la efectele cofeinei, alcoolului sau medicamentelor?",
            "Substance Sensitivity, Body", 
            3, 
            [
                ("A) Am o toleranță foarte mare.", 0), 
                ("B) Medie.", 30), 
                ("C) Destul de sensibil.", 60), 
                ("D) Foarte sensibil. O cafea după-amiaza îmi distruge somnul.", 100)
            ]
        ),
        (
            "Simți că procesezi informațiile mai profund decât ceilalți, analizând toate nuanțele înainte de a acționa?",
            "Processing Depth, Caution", 
            3, 
            [
                ("A) Nu, sunt impulsiv și rapid.", 0), 
                ("B) Gândesc normal.", 30), 
                ("C) Da, sunt analitic.", 70), 
                ("D) Da. Reflectez profund la orice, ceea ce mă face să par lent sau ezitant.", 100)
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