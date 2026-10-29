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
AXIS_ID = 74
AXIS_NAME = "Anhedonie (Lipsă Plăcere)"
# Pol 0: Bucuros de viață / Vital
# Pol 100: Gol interior / Aplatizat / Mort sufletește

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
    log("sys", f"Populăm Clinicul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = ANHEDONIC (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Plăceri Simple) ---
        (
            "Mai simți plăcere când mănânci felul tău preferat de mâncare?",
            "Physical Pleasure, Taste, Appetite", 
            1, 
            [
                ("A) Da, e delicios!", 0), 
                ("B) Da, dar parcă nu ca înainte.", 30), 
                ("C) Mănânc doar de nevoie, nu are gust.", 70), 
                ("D) Nu simt nimic. Parcă mestec carton.", 100)
            ]
        ),
        (
            "Cât de mult te bucuri de hobby-urile sau activitățile care înainte te pasionau?",
            "Interests, Hobbies, Motivation", 
            1, 
            [
                ("A) La fel de mult, mă relaxează.", 0), 
                ("B) Le fac mai rar, dar e ok.", 30), 
                ("C) Le fac din inerție, dar mă plictisesc.", 70), 
                ("D) Le-am abandonat. Nu mai văd niciun rost în ele.", 100)
            ]
        ),
        (
            "Când ești cu prietenii sau familia, te simți conectat sau izolat?",
            "Social Connection, Isolation, Feeling", 
            1, 
            [
                ("A) Mă simt bine, râdem, povestim.", 0), 
                ("B) Uneori sunt obosit, dar e plăcut.", 30), 
                ("C) Mă prefac că mă simt bine, dar abia aștept să plec.", 70), 
                ("D) Mă simt ca un străin între ei. Sunt acolo fizic, dar mort interior.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Aplatizare / Anticipare) ---
        (
            "Simți entuziasm când urmează să se întâmple ceva bun (o vacanță, un eveniment)?",
            "Anticipatory Anhedonia, Future", 
            2, 
            [
                ("A) Da, abia aștept!", 0), 
                ("B) Sunt curios.", 30), 
                ("C) Nu simt mare lucru, e doar o altă zi.", 70), 
                ("D) Îmi este complet indiferent. Poate să nu se mai întâmple.", 100)
            ]
        ),
        (
            "Cum ai descrie gama ta de emoții din ultima vreme?",
            "Emotional Range, Flatness", 
            2, 
            [
                ("A) Variată: bucurie, tristețe, furie, entuziasm.", 0), 
                ("B) Puțin mai ștearsă, dar funcțională.", 30), 
                ("C) Predomină tristețea.", 60), 
                ("D) 'Flatline'. Nu sunt nici trist, nici fericit. Sunt gol.", 100)
            ]
        ),
        (
            "Mai ai interes pentru intimitate fizică sau sex?",
            "Libido, Physical Connection", 
            2, 
            [
                ("A) Da, normal.", 0), 
                ("B) Poate puțin scăzut din cauza stresului.", 30), 
                ("C) Scăzut semnificativ.", 70), 
                ("D) Zero. Ideea îmi este complet străină sau respingătoare.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Depresie Severă / Existențial) ---
        (
            "Ți se întâmplă să zâmbești sau să râzi doar 'social', fără să simți nicio bucurie reală?",
            "Masking, Fake Emotion", 
            3, 
            [
                ("A) Nu, râsul meu e sincer.", 0), 
                ("B) Uneori, din politețe.", 20), 
                ("C) Deseori port o mască.", 70), 
                ("D) Da, tot timpul. Dacă nu m-aș preface, fața mea ar fi de piatră.", 100)
            ]
        ),
        (
            "Simți că lumea din jurul tău și-a pierdut culorile și a devenit gri?",
            "Perception, Depression, Worldview", 
            3, 
            [
                ("A) Nu, lumea e vie.", 0), 
                ("B) Sunt zile mai gri, zile mai bune.", 20), 
                ("C) Totul pare șters.", 70), 
                ("D) Da. Totul e cenușiu, fad și lipsit de viață.", 100)
            ]
        ),
        (
            "Te simți amorțit emoțional (numbness), ca și cum ai fi sub anestezie?",
            "Numbness, Dissociation, Clinical", 
            3, 
            [
                ("A) Nu, simt totul intens.", 0), 
                ("B) Nu.", 0), 
                ("C) Uneori, ca o ceață.", 60), 
                ("D) Da. Aș vrea să pot plânge sau să mă bucur, dar nu pot simți nimic.", 100)
            ]
        ),
        (
            "Ai sentimentul că nimic din ce faci nu contează și că efortul nu aduce nicio recompensă emoțională?",
            "Reward System, Motivation", 
            3, 
            [
                ("A) Nu, sunt mândru de ce fac.", 0), 
                ("B) Uneori e greu să te motivezi.", 30), 
                ("C) Deseori simt că trag în gol.", 70), 
                ("D) Da. Nu există nicio recompensă. Totul e zadarnic.", 100)
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