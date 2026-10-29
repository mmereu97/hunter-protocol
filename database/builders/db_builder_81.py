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
AXIS_ID = 81
AXIS_NAME = "Libido"
# Pol Stânga (0): Scăzut / Asexual / Neinteresat
# Pol Dreapta (100): Ridicat / Intens / Pasional

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
    # Punctaj: 0 = Scăzut, 100 = Ridicat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Importanță Generală) ---
        (
            "Cât de importantă consideri că este componenta sexuală într-o relație de cuplu pe termen lung?",
            "Relationships, Values, Priority", 
            1, 
            [
                ("A) Puțin importantă. Alte lucruri contează.", 0), 
                ("B) E un bonus plăcut, dar nu esențial.", 30), 
                ("C) Este un pilon important.", 70), 
                ("D) Este crucială. Fără chimie intensă, relația moare.", 100)
            ]
        ),
        (
            "Cât de des te gândești la intimitate fizică sau simți dorință într-o zi obișnuită?",
            "Frequency, Drive, Mental Space", 
            1, 
            [
                ("A) Foarte rar sau deloc.", 0), 
                ("B) Ocazional.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Constant. Este o parte majoră a energiei mele zilnice.", 100)
            ]
        ),
        (
            "Dacă ai trece printr-o perioadă lungă de abstinență (fără intimitate), cum te-ai simți?",
            "Frustration Tolerance, Needs", 
            1, 
            [
                ("A) Nu m-ar deranja deloc.", 0), 
                ("B) Aș simți lipsa, dar m-aș adapta.", 30), 
                ("C) Aș fi frustrat și irascibil.", 70), 
                ("D) Insuportabil. Am nevoie de asta ca de aer.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Comportament/Inițiativă) ---
        (
            "În general, cine are inițiativa în relațiile tale când vine vorba de intimitate?",
            "Initiative, Assertiveness", 
            2, 
            [
                ("A) Aproape întotdeauna partenerul.", 0), 
                ("B) E un echilibru, sau aștept semnale.", 30), 
                ("C) Deseori eu.", 70), 
                ("D) Eu. Sunt foarte direct și pasional.", 100)
            ]
        ),
        (
            "Te consideri o persoană 'touchy' (tactilă), care simte nevoia să atingă și să fie atinsă des?",
            "Physical Touch, Love Language", 
            2, 
            [
                ("A) Nu, am nevoie de spațiu personal.", 0), 
                ("B) Doar în momente specifice.", 30), 
                ("C) Da, îmi place contactul fizic.", 70), 
                ("D) Da, am nevoie constantă de atingere.", 100)
            ]
        ),
        (
            "Cum ai reacționa dacă partenerul tău ar avea un nivel de energie mult mai scăzut decât al tău în acest domeniu?",
            "Compatibility, Conflict", 
            2, 
            [
                ("A) M-aș simți ușurat.", 0), 
                ("B) M-aș adapta la ritmul lui.", 30), 
                ("C) Ar fi o problemă de discutat.", 70), 
                ("D) Ar fi o sursă majoră de conflict și nefericire.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Hărțuire / Dezinhibiție / Dependență) ---
        (
            "Consideri că o viață sexuală activă și variată este esențială pentru sănătatea ta mentală?",
            "Mental Health, Coping Mechanism", 
            3, 
            [
                ("A) Nu are nicio legătură.", 0), 
                ("B) Ajută puțin la relaxare.", 30), 
                ("C) Este importantă pentru echilibru.", 70), 
                ("D) Da. Este principalul meu mod de a mă elibera de stres.", 100)
            ]
        ),
        (
            "Ai fost vreodată în situația de a lua decizii impulsive sau riscante din cauza unei atracții fizice intense?",
            "Impulsivity, Risk, Attraction", 
            3, 
            [
                ("A) Niciodată. Rațiunea primează.", 0), 
                ("B) Nu cred.", 20), 
                ("C) S-a întâmplat o dată.", 60), 
                ("D) Da, pasiunea mă face să îmi pierd capul.", 100)
            ]
        ),
        (
            "Te plictisești repede în relații dacă dispare noutatea și intensitatea de la început?",
            "Boredom, Novelty Seeking, Stability", 
            3, 
            [
                ("A) Nu, prefer confortul și familiaritatea.", 0), 
                ("B) E normal să scadă intensitatea.", 30), 
                ("C) Încerc să reaprind scânteia.", 60), 
                ("D) Da, am nevoie constantă de pasiune și noutate.", 100)
            ]
        ),
        (
            "Ți se întâmplă ca dorința fizică să îți distragă atenția de la muncă sau alte responsabilități?",
            "Focus, Distraction, Intensity", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Foarte rar.", 20), 
                ("C) Uneori îmi fuge mintea.", 60), 
                ("D) Da, am momente când nu mă pot concentra la nimic altceva.", 100)
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