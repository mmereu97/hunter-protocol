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
AXIS_ID = 54
AXIS_NAME = "Percepție Emoțională (EQ)"
# Pol Stânga (0): Orb Emoțional / Insensibil
# Pol Dreapta (100): Empat / Intuitiv / Perceptiv

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
    # Punctaj: 0 = Orb Emoțional, 100 = Empat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Self & Others) ---
        (
            "Cât de ușor îți este să îți dai seama exact ce emoție simți într-un moment dat (să pui o etichetă precisă pe ea)?",
            "Self-Awareness, Emotional Granularity", 
            1, 
            [
                ("A) Foarte greu. De obicei simt doar 'bine' sau 'rău'.", 0), 
                ("B) Îmi ia ceva timp să analizez.", 30), 
                ("C) Destul de ușor.", 70), 
                ("D) Imediat. Pot distinge între frustrare, dezamăgire și furie.", 100)
            ]
        ),
        (
            "Când intri într-o cameră unde tocmai a avut loc o ceartă (dar acum e liniște), îți dai seama de tensiune?",
            "Reading the Room, Atmosphere", 
            1, 
            [
                ("A) Nu, dacă nu vorbește nimeni, nu observ nimic.", 0), 
                ("B) Poate dacă văd fețe încruntate.", 30), 
                ("C) Simt că ceva e în neregulă.", 70), 
                ("D) Da, 'tensiunea se poate tăia cu cuțitul'. O simt fizic.", 100)
            ]
        ),
        (
            "Dacă cineva îți spune 'Sunt bine', dar tonul vocii și privirea spun altceva, ce crezi?",
            "Verbal vs Non-Verbal, Lie Detection", 
            1, 
            [
                ("A) Cred ce mi-a spus. De ce ar minți?", 0), 
                ("B) Am o mică îndoială.", 30), 
                ("C) Bănuiesc că ascunde ceva.", 70), 
                ("D) Știu sigur că nu e bine și probabil știu și de ce.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Limbaj Corporal / Empatie) ---
        (
            "Cât de mult te bazezi pe limbajul trupului (poziție, gesturi) pentru a înțelege o persoană?",
            "Body Language, Communication", 
            2, 
            [
                ("A) Deloc. Ascult doar cuvintele.", 0), 
                ("B) Uneori observ gesturi evidente.", 30), 
                ("C) Este o sursă importantă de informație.", 70), 
                ("D) Este principalul mod în care citesc oamenii.", 100)
            ]
        ),
        (
            "Ți se întâmplă des să fii surprins de reacțiile emoționale ale celorlalți (ex: cineva izbucnește în plâns și nu te așteptai)?",
            "Prediction, Empathy Gap", 
            2, 
            [
                ("A) Da, oamenii sunt imprevizibili și ilogici.", 0), 
                ("B) Uneori nu îi înțeleg.", 30), 
                ("C) Rar, de obicei văd semnele.", 70), 
                ("D) Niciodată. Văd semnele acumulării emoționale cu mult înainte.", 100)
            ]
        ),
        (
            "Când te uiți la un film, îți dai seama ce simt personajele doar din priviri, fără dialog?",
            "Movies, Empathy, Decoding", 
            2, 
            [
                ("A) Nu, mă plictisesc scenele fără dialog.", 0), 
                ("B) Dacă actorii joacă foarte expresiv, da.", 30), 
                ("C) Înțeleg contextul.", 70), 
                ("D) Da, pot citi o poveste întreagă într-o privire.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Alexitimie / Autism / Psihopatie) ---
        (
            "Ai dificultăți în a deosebi senzațiile fizice (foame, oboseală) de emoții (tristețe, anxietate)?",
            "Alexithymia Check, Interoception", 
            3, 
            [
                ("A) Da, adesea sunt confuz. (Risc Alexitimie)", 0), 
                ("B) Uneori, când sunt epuizat.", 30), 
                ("C) Rar.", 70), 
                ("D) Niciodată. Știu exact diferența.", 100)
            ]
        ),
        (
            "Prietenii ți-au spus vreodată că ești 'insensibil' sau că nu 'prinzi' aluziile subtile?",
            "Feedback, Social Blindness", 
            3, 
            [
                ("A) Da, mi se reproșează des.", 0), 
                ("B) Mi s-a spus că sunt prea direct.", 30), 
                ("C) Nu prea.", 70), 
                ("D) Nu, dimpotrivă, sunt considerat foarte intuitiv.", 100)
            ]
        ),
        (
            "Poți simți când cineva te minte sau te manipulează doar după 'vibrația' pe care o transmite?",
            "Intuition, Gut Feeling", 
            3, 
            [
                ("A) Nu, am nevoie de dovezi.", 0), 
                ("B) Uneori am o bănuială.", 30), 
                ("C) Deseori instinctul meu are dreptate.", 70), 
                ("D) Da, am un 'radar' infailibil pentru falsitate.", 100)
            ]
        ),
        (
            "Cât de des te 'contaminezi' cu starea emoțională a celor din jur (dacă ei sunt triști, devii și tu trist)?",
            "Emotional Contagion, Empathy", 
            3, 
            [
                ("A) Niciodată. Rămân detașat.", 0), 
                ("B) Doar cu familia.", 30), 
                ("C) Mă afectează atmosfera.", 60), 
                ("D) Foarte des. Sunt ca un burete emoțional.", 100)
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