import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# DEFINIȚII
AXIS_ID = 99
AXIS_NAME = "Dezirabilitate Socială (Lie Scale)"
# Pol 0: Autentic / Sincer / Realist
# Pol 100: Minciună / Falsitate / "Sfânt"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm Controlul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = MINCIUNĂ (FAKE GOOD)
    questions_data = [
        # --- VALUL 1: SCREENING (Micile defecte universale) ---
        (
            "Ai bârfit vreodată pe cineva sau ai vorbit despre cineva pe la spate?",
            "Gossip, Common Faults, Lie Check", 
            1, 
            [
                ("A) Da, mi se întâmplă uneori.", 0),   # Onest
                ("B) Rar, dar am făcut-o.", 20), 
                ("C) Foarte rar.", 60), 
                ("D) Niciodată în viața mea.", 100)     # Minciună (Toată lumea a bârfit măcar o dată)
            ]
        ),
        (
            "Ți s-a întâmplat vreodată să întârzii la o întâlnire, chiar și câteva minute?",
            "Punctuality, Perfection, Lie Check", 
            1, 
            [
                ("A) Da, se mai întâmplă.", 0),         # Onest
                ("B) Foarte rar.", 20), 
                ("C) Doar din cauze de forță majoră.", 60), 
                ("D) Niciodată. Sunt mereu punctual.", 100) # Minciună statistică
            ]
        ),
        (
            "Ai simțit vreodată invidie față de succesul cuiva, chiar și pentru o secundă?",
            "Envy, Emotion, Lie Check", 
            1, 
            [
                ("A) Da, e un sentiment uman.", 0),      # Onest
                ("B) Uneori.", 20), 
                ("C) Aproape niciodată.", 60), 
                ("D) Niciodată. Mă bucur mereu sincer pentru alții.", 100) # Minciună
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Virtuți Exagerate) ---
        (
            "Ai mințit vreodată pe cineva pentru a evita o situație neplăcută sau pentru a nu răni sentimente?",
            "White Lies, Honesty", 
            2, 
            [
                ("A) Da, 'minciuni albe'.", 0), 
                ("B) Rar.", 20), 
                ("C) Foarte rar.", 60), 
                ("D) Nu. Spun întotdeauna adevărul pur, indiferent de consecințe.", 100)
            ]
        ),
        (
            "Te-ai înfuriat sau iritat vreodată pe cineva fără un motiv foarte serios?",
            "Anger, Emotion, Lie Check", 
            2, 
            [
                ("A) Da, am și eu toane.", 0), 
                ("B) Uneori, când sunt obosit.", 20), 
                ("C) Încerc să nu.", 60), 
                ("D) Niciodată. Sunt mereu calm și rațional.", 100)
            ]
        ),
        (
            "Îți plac absolut toți oamenii pe care îi cunoști?",
            "Social, Liking, Lie Check", 
            2, 
            [
                ("A) Nu, unii mă enervează.", 0), 
                ("B) Majoritatea îmi plac.", 20), 
                ("C) Găsesc ceva bun în fiecare.", 60), 
                ("D) Da, iubesc pe toată lumea în egală măsură.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Absolutism Moral) ---
        (
            "Ai profitat vreodată de cineva sau ai manipulat o situație în favoarea ta?",
            "Manipulation, History", 
            3, 
            [
                ("A) Da, am făcut greșeli.", 0), 
                ("B) Poate inconștient.", 20), 
                ("C) Nu cred.", 60), 
                ("D) Niciodată. Sunt corect 100% din timp.", 100)
            ]
        ),
        (
            "Ai râs vreodată la o glumă nepoliticoasă sau răutăcioasă?",
            "Humor, Morality", 
            3, 
            [
                ("A) Da, dacă a fost amuzantă.", 0), 
                ("B) Uneori.", 20), 
                ("C) Nu îmi plac.", 60), 
                ("D) Niciodată. Nu tolerez așa ceva.", 100)
            ]
        ),
        (
            "Ai judecat vreodată pe cineva după prima impresie și te-ai înșelat?",
            "Judgment, Prejudice", 
            3, 
            [
                ("A) Da, mi se întâmplă.", 0), 
                ("B) Uneori.", 20), 
                ("C) Încerc să nu judec.", 60), 
                ("D) Nu. Nu am prejudecăți niciodată.", 100)
            ]
        ),
        (
            "Ai amânat vreodată o sarcină neplăcută până în ultimul moment?",
            "Procrastination, Habit", 
            3, 
            [
                ("A) Da, des.", 0), 
                ("B) Uneori.", 20), 
                ("C) Foarte rar.", 60), 
                ("D) Niciodată. Fac totul imediat.", 100)
            ]
        )
    ]

    try:
        # CLEANUP & INSERT
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))

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
        
        conn.commit()
        log("db_conn", f"SUCCES: {len(questions_data)} întrebări inserate pentru {AXIS_NAME}.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()