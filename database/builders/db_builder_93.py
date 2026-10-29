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
AXIS_ID = 93
AXIS_NAME = "Uncoachable (Refractar)"
# Pol 0: Deschis / Umil / Coachable
# Pol 100: Arogant / Refractar / Atotștiutor

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

    # Punctaj: 100 = UNCOACHABLE (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Reacția la Feedback) ---
        (
            "Cum te simți când un superior îți corectează munca sau îți spune să faci ceva altfel?",
            "Feedback, Authority, Ego", 
            1, 
            [
                ("A) Apreciez, așa învăț.", 0), 
                ("B) Ascult, chiar dacă nu îmi convine.", 30), 
                ("C) Mă simt criticat și mă enervez puțin.", 60), 
                ("D) Mă simt jignit. Știu eu mai bine cum se face.", 100)
            ]
        ),
        (
            "Cât de des ceri sfatul altora când nu ești sigur de o decizie?",
            "Asking for Help, Humility", 
            1, 
            [
                ("A) Foarte des. Mai multe minți gândesc mai bine.", 0), 
                ("B) Uneori, dacă e critic.", 30), 
                ("C) Rar, prefer să mă descurc singur.", 70), 
                ("D) Niciodată. Nu am nevoie de sfaturi.", 100)
            ]
        ),
        (
            "Ce faci când realizezi că ai greșit într-o discuție?",
            "Admitting Fault, Conflict", 
            1, 
            [
                ("A) Recunosc imediat și îmi cer scuze.", 0), 
                ("B) Recunosc, dar explic de ce am greșit.", 30), 
                ("C) Tac și schimb subiectul.", 70), 
                ("D) Insist că am dreptate sau că am fost înțeles greșit.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Învățare / Schimbare) ---
        (
            "Dacă firma implementează o metodă nouă de lucru, dar tu consideri că metoda ta veche e mai bună, ce faci?",
            "Change Management, Stubbornness", 
            2, 
            [
                ("A) Mă adaptez și învăț noua metodă.", 0), 
                ("B) O încerc, dar sunt sceptic.", 30), 
                ("C) O fac doar de formă, dar tot ca mine lucrez.", 70), 
                ("D) Refuz să o folosesc și le spun că e o prostie.", 100)
            ]
        ),
        (
            "Crezi că mai ai multe de învățat în domeniul tău sau consideri că ai atins nivelul de expert?",
            "Growth Mindset vs Fixed Mindset", 
            2, 
            [
                ("A) Învăț ceva nou în fiecare zi.", 0), 
                ("B) Mai am de învățat, dar sunt bun.", 30), 
                ("C) Sunt expert, puțini mă pot învăța ceva.", 70), 
                ("D) Nu mai am ce să învăț. Eu le predau altora.", 100)
            ]
        ),
        (
            "Când primești un feedback negativ la o evaluare, care e prima ta reacție?",
            "Evaluation, Defense Mechanism", 
            2, 
            [
                ("A) 'Ce pot îmbunătăți?'.", 0), 
                ("B) Mă întristez.", 20), 
                ("C) Mă gândesc cum să mă apăr.", 60), 
                ("D) 'Evaluatorul e un idiot care nu înțelege nimic'.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Aroganță Extremă / Conflict cu Autoritatea) ---
        (
            "Ți s-a întâmplat să intri în conflict cu un manager pentru că ai refuzat să faci ceva 'stupid'?",
            "Insubordination, Conflict, Ego", 
            3, 
            [
                ("A) Nu, respect ierarhia.", 0), 
                ("B) Am discutat contradictoriu, dar am executat.", 30), 
                ("C) Da, am refuzat sarcini ilogice.", 70), 
                ("D) Da, des. Nu execut ordine de la incompetenți.", 100)
            ]
        ),
        (
            "Consideri că succesul tău este limitat doar de incompetența celor din jur?",
            "External Blame, Narcissism", 
            3, 
            [
                ("A) Nu, succesul depinde de mine.", 0), 
                ("B) Uneori mediul contează.", 30), 
                ("C) Deseori sunt tras în jos de alții.", 70), 
                ("D) Da. Dacă aș lucra singur sau cu oameni ca mine, aș fi departe.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să ai dreptate într-o discuție?",
            "Winning Argument, Need for Control", 
            3, 
            [
                ("A) Mai puțin important decât relația.", 0), 
                ("B) Îmi place să am dreptate, dar cedez.", 30), 
                ("C) Foarte important.", 70), 
                ("D) Crucial. Nu suport să pierd o dezbatere.", 100)
            ]
        ),
        (
            "Dacă un coleg mai tânăr sau nou îți dă un sfat, îl asculți?",
            "Openness, Status, Pride", 
            3, 
            [
                ("A) Da, oricine poate avea o idee bună.", 0), 
                ("B) Îl ascult din politețe.", 30), 
                ("C) Sunt sceptic.", 60), 
                ("D) Nu. Ce știe el? Eu am experiența.", 100)
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