import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 106
AXIS_NAME = "BPD (Borderline)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = BPD ACTIV
    questions_data = [
        # --- VALUL 1: SCREENING (Stabilitate Emoțională / Relații) ---
        (
            "Cât de repede ți se schimbă starea de spirit (de la bucurie la tristețe sau furie)?",
            "Mood Swings, Instability", 1, 
            [
                ("A) Sunt foarte stabil, rar am toane.", 0), 
                ("B) Am zile bune și zile proaste.", 20), 
                ("C) Se poate schimba de câteva ori pe zi.", 60), 
                ("D) E un rollercoaster continuu. Trec de la extaz la agonie în aceeași oră.", 100)
            ]
        ),
        (
            "În relațiile tale (prietenie sau romantice), tinzi să idealizezi persoana la început și apoi să fii profund dezamăgit?",
            "Splitting, Idealization/Devaluation", 1, 
            [
                ("A) Nu, văd oamenii realist de la început.", 0), 
                ("B) Uneori mă entuziasmez prea tare.", 30), 
                ("C) Da, mi se întâmplă des.", 70), 
                ("D) Da. Ori ești cel mai bun om din lume, ori ești un monstru. Nu există cale de mijloc.", 100)
            ]
        ),
        (
            "Cum reacționezi dacă simți că cineva apropiat te ignoră sau se îndepărtează de tine?",
            "Fear of Abandonment, Reaction", 1, 
            [
                ("A) Îi dau spațiu, e normal.", 0), 
                ("B) Îl întreb ce s-a întâmplat.", 30), 
                ("C) Mă îngrijorez și insist cu mesaje.", 70), 
                ("D) Intru în panică totală. Fac orice să nu mă părăsească (sau îl părăsesc eu primul).", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Identitate / Furie) ---
        (
            "Ai o imagine clară despre cine ești și ce vrei de la viață, sau aceasta se schimbă frecvent?",
            "Identity Disturbance, Self-Image", 2, 
            [
                ("A) Știu exact cine sunt.", 0), 
                ("B) Mai am dubii, dar am o direcție.", 30), 
                ("C) Mă caut încă.", 60), 
                ("D) Îmi schimb jobul, stilul, valorile și prietenii des. Nu știu cine este 'eu'.", 100)
            ]
        ),
        (
            "Ai izbucniri de furie intensă, greu de controlat, care par disproportionate față de motiv?",
            "Inappropriate Anger, Rage", 2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Rar, dacă sunt provocat grav.", 20), 
                ("C) Uneori țip și trântesc lucruri.", 60), 
                ("D) Da, am o furie 'oarbă' care distruge tot, apoi mă simt vinovat.", 100)
            ]
        ),
        (
            "Te simți adesea 'gol pe dinăuntru' (chronic emptiness)?",
            "Emptiness, Void", 2, 
            [
                ("A) Nu, mă simt împlinit.", 0), 
                ("B) Doar când sunt plictisit.", 20), 
                ("C) Uneori simt un gol.", 60), 
                ("D) Da, e un sentiment fizic de vid interior pe care încerc să-l umplu cu orice.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Impulsivitate Autodistructivă / Disociere) ---
        (
            "Când ești foarte stresat sau trist, faci lucruri impulsive care îți fac rău (cheltuit excesiv, condus imprudent, mâncat compulsiv)?",
            "Self-Damaging Impulsivity, Coping", 3, 
            [
                ("A) Nu, sunt precaut.", 0), 
                ("B) Poate mănânc puțină ciocolată.", 20), 
                ("C) Da, am făcut lucruri riscante.", 70), 
                ("D) Da, mă autosabotez constant prin comportamente periculoase.", 100)
            ]
        ),
        (
            "În momente de stres extrem, ai senzația că te detașezi de realitate sau că ieși din corp (paranoia/disociere)?",
            "Dissociation, Stress, Paranoia", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Doar sunt foarte obosit.", 20), 
                ("C) Uneori lucrurile par ireale.", 60), 
                ("D) Da, 'plec' mental sau devin paranoic că alții vor să-mi facă rău.", 100)
            ]
        ),
        (
            "Relațiile tale amoroase sau de prietenie sunt de obicei calme sau furtunoase?",
            "Relationship Stability, Chaos", 3, 
            [
                ("A) Calme și stabile.", 0), 
                ("B) Cu mici certuri normale.", 20), 
                ("C) Destul de intense.", 60), 
                ("D) Furtunoase. Multă pasiune, multă dramă, despărțiri și împăcări frecvente.", 100)
            ]
        ),
        (
            "Ai simțit vreodată nevoia să ameninți că îți faci rău ție însuți pentru a opri pe cineva să plece?",
            "Manipulation, Desperation, Crisis", 3, 
            [
                ("A) Niciodată. E inacceptabil.", 0), 
                ("B) Nu.", 0), 
                ("C) M-am gândit, dar nu am zis.", 60), 
                ("D) Da. Disperarea e atât de mare încât aș face orice.", 100)
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
        log("db_conn", f"SUCCES: Întrebări BPD inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()