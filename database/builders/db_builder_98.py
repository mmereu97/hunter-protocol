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
AXIS_ID = 98
AXIS_NAME = "Victimizare (Martir)"
# Pol 0: Asumat / Responsabil
# Pol 100: Victimă / Dă vina pe alții

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
    log("sys", f"Populăm Monstrul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = VICTIMIZARE (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Locus of Control / Noroc) ---
        (
            "Când lucrurile merg prost în viața ta, care crezi că este cauza principală?",
            "Locus of Control, Failure analysis", 
            1, 
            [
                ("A) Alegerile mele greșite. Îmi asum.", 0), 
                ("B) Un amestec de greșeli și circumstanțe.", 30), 
                ("C) Ghinionul sau incompetența altora.", 70), 
                ("D) Sistemul, soarta sau oamenii răi care mă sabotează.", 100)
            ]
        ),
        (
            "Consideri că ai avut parte de oportunități egale cu ale celorlalți?",
            "Fairness, Envy, Victimhood", 
            1, 
            [
                ("A) Da, mi-am creat singur norocul.", 0), 
                ("B) În mare parte da.", 30), 
                ("C) Nu prea, alții au avut 'pile'.", 70), 
                ("D) Nu. Viața a fost extrem de nedreaptă cu mine comparativ cu alții.", 100)
            ]
        ),
        (
            "Cum reacționezi la un feedback negativ sau o critică constructivă?",
            "Feedback, Defense, Ego", 
            1, 
            [
                ("A) Încerc să învăț din el.", 0), 
                ("B) Mă supără, dar ascult.", 30), 
                ("C) Mă simt atacat pe nedrept.", 70), 
                ("D) 'Au ceva cu mine'. Este o persecuție personală.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Relații / Trecut) ---
        (
            "Gândește-te la ultimele tale conflicte majore (acasă sau la muncă). Cine a fost de vină?",
            "Conflict, Blame, Self-Awareness", 
            2, 
            [
                ("A) Eu, în multe cazuri.", 0), 
                ("B) Vina a fost împărțită.", 30), 
                ("C) Ceilalți, de cele mai multe ori.", 70), 
                ("D) Ei. Eu am fost mereu bine intenționat, dar am fost tratat rău.", 100)
            ]
        ),
        (
            "Simți adesea că muncești mai mult decât alții, dar ești mai puțin apreciat?",
            "Martyrdom, Work, Appreciation", 
            2, 
            [
                ("A) Nu, sunt evaluat corect.", 0), 
                ("B) Uneori simt asta, dar îmi trece.", 30), 
                ("C) Da, se întâmplă des.", 70), 
                ("D) Da! Duc tot greul în spate și nimeni nu vede.", 100)
            ]
        ),
        (
            "Cât de des te plângi prietenilor sau familiei despre problemele tale?",
            "Complaining, Venting, Negativity", 
            2, 
            [
                ("A) Rar. Prefer să găsesc soluții.", 0), 
                ("B) Când am o zi proastă.", 30), 
                ("C) Destul de des, mă descarc.", 70), 
                ("D) Zilnic. Am atâtea probleme încât trebuie să le spun cuiva.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Paranoia / Neputință învățată) ---
        (
            "Ai senzația că Universul sau o forță superioară îți pune bețe în roate intenționat?",
            "Fatalism, Paranoia, Superstition", 
            3, 
            [
                ("A) Nu, eu îmi fac destinul.", 0), 
                ("B) Uneori am ghinion, asta e statistică.", 20), 
                ("C) Da, parcă sunt blestemat.", 70), 
                ("D) Absolut. Nimic nu îmi iese, oricât aș încerca.", 100)
            ]
        ),
        (
            "Când cineva îți oferă o soluție la o problemă de-a ta, ce faci?",
            "Help-Rejecting Complainer, Passive", 
            3, 
            [
                ("A) O aplic imediat.", 0), 
                ("B) O iau în considerare.", 20), 
                ("C) Îi explic de ce nu va funcționa în cazul meu.", 70), 
                ("D) Mă enervez. Ei nu înțeleg cât de complicată e situația mea ('Da, dar...').", 100)
            ]
        ),
        (
            "Te consideri o persoană 'bună' care pățește mereu lucruri rele?",
            "Identity, Victim Narrative", 
            3, 
            [
                ("A) Nu mă consider special.", 0), 
                ("B) Sunt un om normal cu probleme normale.", 20), 
                ("C) Da, sunt prea bun pentru lumea asta.", 70), 
                ("D) Da. Profita toți de bunătatea mea.", 100)
            ]
        ),
        (
            "Cât de mult depinde fericirea ta de acțiunile altor oameni (șef, partener, guvern)?",
            "Dependency, External Locus", 
            3, 
            [
                ("A) Deloc. Fericirea e internă.", 0), 
                ("B) Puțin, e normal să influențeze.", 30), 
                ("C) Mult. Dacă ei nu se schimbă, eu nu pot fi bine.", 70), 
                ("D) Total. Sunt nefericit din cauza lor.", 100)
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