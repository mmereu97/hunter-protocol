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
AXIS_ID = 21
AXIS_NAME = "Flexibilitate"
# Pol Stânga (0): Încăpățânat / Rigid / Fixist
# Pol Dreapta (100): Flexibil / Adaptabil / Compromis

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
    # Punctaj: 0 = Rigid (Încăpățânat), 100 = Flexibil
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Schimbări/Opinii) ---
        (
            "Dacă planurile tale sunt date peste cap în ultimul moment din cauze externe, cum reacționezi?",
            "Adaptability, Plans, Stress", 
            1, 
            [
                ("A) Mă enervez cumplit și refuz să particip la noul plan.", 0), 
                ("B) Sunt vizibil iritat și mă plâng.", 30), 
                ("C) Sunt dezamăgit, dar mă repliez rapid.", 70), 
                ("D) Mă adaptez imediat, 'improvizez, mă adaptez, depășesc'.", 100)
            ]
        ),
        (
            "Când ai o discuție în contradictoriu și îți dai seama că s-ar putea să nu ai dreptate, ce faci?",
            "Debate, Ego, Admit Fault", 
            1, 
            [
                ("A) Continui să argumentez. Nu pot să pierd.", 0), 
                ("B) Schimb subiectul ca să nu recunosc.", 30), 
                ("C) Recunosc parțial, dar cu rezerve.", 70), 
                ("D) Recunosc deschis: 'Ai dreptate, am greșit'.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine ca lucrurile să fie făcute exact în felul tău?",
            "Control, Methods, Perfectionism", 
            1, 
            [
                ("A) Crucial. Metoda mea e singura corectă.", 0), 
                ("B) Prefer să fie ca mine, insist destul de mult.", 30), 
                ("C) Dacă rezultatul e bun, nu contează metoda.", 70), 
                ("D) Sunt deschis la orice metodă care funcționează.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Compromis) ---
        (
            "La locul de muncă se introduce un soft nou sau o procedură nouă care schimbă rutina. Ce gândești?",
            "Change Management, Work, Tech", 
            2, 
            [
                ("A) 'O prostie. Vechiul sistem era mai bun'. Rezist schimbării.", 0), 
                ("B) Sunt sceptic și critic.", 30), 
                ("C) Îl testez să văd dacă e eficient.", 70), 
                ("D) Sunt curios și dornic să învăț ceva nou.", 100)
            ]
        ),
        (
            "Într-un proiect de grup, majoritatea decide o direcție cu care nu ești de acord. Ce faci?",
            "Teamwork, Cooperation, Stubbornness", 
            2, 
            [
                ("A) Mă retrag sau blochez proiectul.", 0), 
                ("B) Îmi exprim nemulțumirea constant pe parcurs.", 30), 
                ("C) Accept decizia democratică, deși nu-mi convine.", 70), 
                ("D) Mă aliniez total și susțin echipa pentru succes.", 100)
            ]
        ),
        (
            "Ce părere ai despre compromis într-o negociere sau relație?",
            "Compromise, Negotiation, Values", 
            2, 
            [
                ("A) Este un semn de slăbiciune. Totul sau nimic.", 0), 
                ("B) Fac compromisuri doar dacă primesc ceva mai mult la schimb.", 30), 
                ("C) Este necesar pentru a menține pacea.", 70), 
                ("D) Este esențial. Nimeni nu deține adevărul absolut.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Uncoachable / OCPD) ---
        (
            "Dacă cineva îți oferă un sfat nesolicitat despre cum să faci ceva mai eficient, cum te simți?",
            "Feedback, Coachability, Ego", 
            3, 
            [
                ("A) Mă simt jignit. Știu eu ce fac.", 0), 
                ("B) Îl ignor politicos.", 30), 
                ("C) Îl ascult, poate are dreptate.", 70), 
                ("D) Îi mulțumesc și încerc sugestia.", 100)
            ]
        ),
        (
            "Ai tendința de a purta pică cuiva doar pentru că are opinii politice sau sociale diferite de ale tale?",
            "Tolerance, Open-mindedness, Bias", 
            3, 
            [
                ("A) Da, nu pot fi prieten cu cineva care gândește greșit.", 0), 
                ("B) Discutăm în contradictoriu des.", 30), 
                ("C) Evit subiectele sensibile.", 70), 
                ("D) Nu. Apreciez diversitatea de opinii.", 100)
            ]
        ),
        (
            "Ți s-a spus vreodată că ești 'capos' sau dificil de convins?",
            "Reputation, Self-Awareness, Stubbornness", 
            3, 
            [
                ("A) Da, și sunt mândru. Înseamnă că am principii.", 0), 
                ("B) Uneori, când știu că am dreptate.", 30), 
                ("C) Rar.", 70), 
                ("D) Nu, sunt considerat o persoană flexibilă.", 100)
            ]
        ),
        (
            "Ești la un restaurant și nu au felul tău preferat de mâncare. Ți se strică seara?",
            "Rigidity, Expectations, Mood", 
            3, 
            [
                ("A) Da, plec la alt restaurant sau sunt morocănos.", 0), 
                ("B) Sunt dezamăgit vizibil.", 30), 
                ("C) Întreb ce altceva recomandă.", 70), 
                ("D) Nu, comand altceva. Îmi place să experimentez.", 100)
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