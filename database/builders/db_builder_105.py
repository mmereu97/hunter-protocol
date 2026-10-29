import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 105
AXIS_NAME = "OCPD (Perfecționism Patologic)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = OCPD ACTIV
    questions_data = [
        # --- VALUL 1: SCREENING (Reguli / Ordine) ---
        (
            "Cât de mult timp petreci făcând liste, orare sau organizând detalii, până în punctul în care întârzii startul proiectului?",
            "Lists, Organization, Efficiency", 1, 
            [
                ("A) Deloc. Sunt spontan.", 0), 
                ("B) Fac o listă rapidă.", 30), 
                ("C) Sunt foarte organizat.", 60), 
                ("D) Mult. Organizarea devine mai importantă decât activitatea în sine.", 100)
            ]
        ),
        (
            "Crezi că există un singur mod 'corect' de a face lucrurile?",
            "Rigidity, Methods, Right Way", 1, 
            [
                ("A) Nu, contează rezultatul.", 0), 
                ("B) De obicei da, dar sunt flexibil.", 30), 
                ("C) Prefer metoda mea.", 70), 
                ("D) Da. Orice alt mod este greșit.", 100)
            ]
        ),
        (
            "Cât de greu îți este să arunci obiecte vechi sau inutile (chiar dacă nu au valoare sentimentală)?",
            "Hoarding, Utility, Letting Go", 1, 
            [
                ("A) Foarte ușor, fac curățenie des.", 0), 
                ("B) Păstrez doar ce e util.", 30), 
                ("C) Mai păstrez 'poate trebuie'.", 70), 
                ("D) Imposibil. 'S-ar putea să am nevoie într-o zi'.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Control / Muncă) ---
        (
            "Ai tendința de a refuza să delegi sarcini pentru că ceilalți nu le vor face la standardele tale?",
            "Delegation, Trust, Perfectionism", 2, 
            [
                ("A) Nu, deleg cu plăcere.", 0), 
                ("B) Verific după ei.", 30), 
                ("C) Prefer să fac eu dacă e important.", 70), 
                ("D) Da. Nimeni nu face treaba la fel de bine ca mine.", 100)
            ]
        ),
        (
            "Pui munca și productivitatea mai presus de prieteni, familie și relaxare?",
            "Workaholism, Priorities, Balance", 2, 
            [
                ("A) Nu, viața personală e prioritară.", 0), 
                ("B) Încerc să am un echilibru.", 30), 
                ("C) Munca e foarte importantă.", 70), 
                ("D) Da. Nu am timp de distracții când e de muncă.", 100)
            ]
        ),
        (
            "Ești foarte strict cu privire la cheltuirea banilor, atât pentru tine cât și pentru alții?",
            "Miserliness, Money, Control", 2, 
            [
                ("A) Nu, sunt generos.", 0), 
                ("B) Sunt chibzuit.", 30), 
                ("C) Sunt econom.", 60), 
                ("D) Da. Banii trebuie strânși pentru zile negre, orice cheltuială e dureroasă.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Rigiditate Morală / Obsesie) ---
        (
            "Te enervezi disproporționat dacă cineva întârzie câteva minute sau schimbă puțin planul?",
            "Punctuality, Control, Flexibility", 3, 
            [
                ("A) Nu, sunt relaxat.", 0), 
                ("B) Puțin, îmi place punctualitatea.", 30), 
                ("C) Mă deranjează.", 70), 
                ("D) Da. Este o lipsă de respect și disciplină inacceptabilă.", 100)
            ]
        ),
        (
            "Ești inflexibil în chestiuni de morală, etică sau valori (vezi lumea în alb și negru)?",
            "Morality, Black and White Thinking", 3, 
            [
                ("A) Nu, contextul contează.", 0), 
                ("B) Am principii, dar ascult.", 30), 
                ("C) Sunt destul de strict.", 70), 
                ("D) Da. Regulile sunt reguli și nu se încalcă niciodată.", 100)
            ]
        ),
        (
            "Simți o nevoie imperioasă de a controla tot ce se întâmplă în jurul tău?",
            "Control Freak, Anxiety", 3, 
            [
                ("A) Nu, îmi place surpriza.", 0), 
                ("B) Îmi place să fiu informat.", 30), 
                ("C) Mă simt mai sigur dacă dețin controlul.", 70), 
                ("D) Da. Haosul și imprevizibilul mă terifiază.", 100)
            ]
        ),
        (
            "Dacă un proiect este 99% gata, dar are un detaliu minor imperfect, îl consideri un eșec?",
            "Perfectionism, Satisfaction", 3, 
            [
                ("A) Nu, e suficient de bun.", 0), 
                ("B) Îl livrez și corectez apoi.", 30), 
                ("C) Mă roade, dar îl dau.", 70), 
                ("D) Da. Nu pot să livrez ceva imperfect. Mai lucrez la el.", 100)
            ]
        )
    ]

    try:
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
        log("db_conn", f"SUCCES: Întrebări OCPD inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()