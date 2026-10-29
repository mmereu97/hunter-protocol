import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 104
AXIS_NAME = "Autism (Spectru ASD)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = TRAIT ASD (RISC/SPECIFICITATE)
    questions_data = [
        # --- VALUL 1: SCREENING (Social / Rutină) ---
        (
            "Cum te descurci cu 'small talk' (discuții mărunte despre vreme, ce ai mai făcut) la petreceri?",
            "Social, Communication, Small Talk", 1, 
            [
                ("A) Îmi place, e relaxant.", 0), 
                ("B) Mă descurc, dar e plictisitor.", 30), 
                ("C) E obositor, nu știu ce să zic.", 70), 
                ("D) E un chin. Nu înțeleg rostul și evit sau mă blochez.", 100)
            ]
        ),
        (
            "Te deranjează dacă cineva îți schimbă planurile sau rutina zilnică în ultimul moment?",
            "Routine, Flexibility, Rigidity", 1, 
            [
                ("A) Nu, sunt spontan.", 0), 
                ("B) Puțin, dar mă adaptez.", 30), 
                ("C) Mă irită destul de tare.", 70), 
                ("D) Da, mă panichez sau mă enervez foarte rău. Ziua e ruinată.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să menții contactul vizual când vorbești cu cineva?",
            "Eye Contact, Non-verbal", 1, 
            [
                ("A) Foarte natural.", 0), 
                ("B) Uneori privesc în altă parte când gândesc.", 30), 
                ("C) Mă forțez să o fac, dar e inconfortabil.", 70), 
                ("D) Foarte greu. Evit ochii, mă uit la gură sau în pământ.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Interese / Senzorial) ---
        (
            "Ai un interes sau un hobby despre care ai putea vorbi ore în șir, acumulând o cantitate imensă de detalii tehnice?",
            "Special Interests, Focus", 2, 
            [
                ("A) Am hobby-uri normale.", 0), 
                ("B) Îmi place să aprofundez lucrurile.", 30), 
                ("C) Da, am o pasiune intensă.", 70), 
                ("D) Da. Prietenii spun că sunt obsedat și vorbesc doar despre asta.", 100)
            ]
        ),
        (
            "Cum reacționezi la zgomote puternice, lumini strălucitoare sau anumite texturi de haine?",
            "Sensory Sensitivity, Overload", 2, 
            [
                ("A) Nu mă deranjează.", 0), 
                ("B) Prefer liniștea.", 30), 
                ("C) Sunt sensibile la ele.", 70), 
                ("D) Îmi provoacă durere fizică sau panică (supraîncărcare).", 100)
            ]
        ),
        (
            "Ți se întâmplă să iei lucrurile prea literal și să nu înțelegi sarcasmul sau expresiile figurate?",
            "Literal Thinking, Communication", 2, 
            [
                ("A) Nu, înțeleg perfect umorul.", 0), 
                ("B) Rar, dacă e foarte subtil.", 30), 
                ("C) Uneori întreb 'glumești?'.", 70), 
                ("D) Da, des. Oamenii trebuie să îmi explice că a fost o glumă.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Social Exhaustion / Pattern Recognition) ---
        (
            "După o zi de interacțiune socială, simți nevoia să te retragi complet ('shutdown') pentru a-ți reveni?",
            "Social Battery, Masking, Burnout", 3, 
            [
                ("A) Nu, socializarea mă energizează.", 0), 
                ("B) Sunt doar puțin obosit.", 30), 
                ("C) Am nevoie de câteva ore de liniște.", 60), 
                ("D) Da, sunt epuizat total. Simt că mi-a căzut masca.", 100)
            ]
        ),
        (
            "Observi modele, tipare sau detalii mici pe care alții nu le văd (ex: numere, aranjamente)?",
            "Pattern Recognition, Details", 3, 
            [
                ("A) Văd ansamblul, nu detaliile.", 0), 
                ("B) Am spirit de observație mediu.", 30), 
                ("C) Observ des detalii ratate de alții.", 60), 
                ("D) Da, mintea mea scanează automat tipare și erori.", 100)
            ]
        ),
        (
            "Îți este greu să îți imaginezi ce simte sau ce gândește altă persoană (Teoria Minții)?",
            "Empathy, Theory of Mind", 3, 
            [
                ("A) Nu, sunt foarte empatic.", 0), 
                ("B) Mă descurc bine.", 30), 
                ("C) Uneori e confuz.", 70), 
                ("D) Da. Emoțiile altora sunt un mister logic pentru mine.", 100)
            ]
        ),
        (
            "Faci mișcări repetitive (legănat, pocnit degete, jucat cu obiecte) când ești stresat sau concentrat?",
            "Stimming, Repetitive Behavior", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Poate dau din picior.", 30), 
                ("C) Da, am ticuri nervoase.", 60), 
                ("D) Da, am nevoie de stimulare repetitivă ca să mă calmez.", 100)
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
        log("db_conn", f"SUCCES: Întrebări Autism inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()