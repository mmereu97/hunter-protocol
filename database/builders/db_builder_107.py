import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 107
AXIS_NAME = "Anxietate Socială (Fobie)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = FOBIE SOCIALĂ
    questions_data = [
        # --- VALUL 1: SCREENING (Disconfort Social) ---
        (
            "Cât de tare te stresează ideea de a suna la o instituție sau de a vorbi cu un operator telefonic necunoscut?",
            "Phone Anxiety, Avoidance", 1, 
            [
                ("A) Deloc. Sun imediat.", 0), 
                ("B) Puțin, îmi repet ce am de zis.", 30), 
                ("C) Destul de mult, amân momentul.", 70), 
                ("D) Îngrozitor. Rog pe altcineva să sune sau nu sun deloc.", 100)
            ]
        ),
        (
            "Dacă trebuie să intri într-o cameră unde oamenii sunt deja așezați și discută, cum te simți?",
            "Spotlight Effect, Self-Consciousness", 1, 
            [
                ("A) Relaxat, salut pe toată lumea.", 0), 
                ("B) Ușor conștient de mine.", 30), 
                ("C) Încordat, simt că toți se uită la mine.", 70), 
                ("D) Paralizat. Îmi vine să plec sau să intru invizibil.", 100)
            ]
        ),
        (
            "Eviți să mănânci sau să bei în public de teamă că te vei face de râs (ex: îți tremură mâna)?",
            "Public Eating, Scrutiny", 1, 
            [
                ("A) Nu, mănânc oriunde.", 0), 
                ("B) Doar dacă e ceva complicat de mâncat.", 20), 
                ("C) Prefer locurile retrase.", 60), 
                ("D) Da, nu pot înghiți dacă simt că sunt privit.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Simptome Fizice / Ruminare) ---
        (
            "În situații sociale, ai simptome fizice vizibile (roșeață intensă, transpirație, tremurat, voce gâtuită)?",
            "Somatic Symptoms, Blushing", 2, 
            [
                ("A) Nu.", 0), 
                ("B) Rar, la emoții mari.", 20), 
                ("C) Da, roșesc des și mă jenează.", 70), 
                ("D) Da, simt că leșin sau fac atac de panică.", 100)
            ]
        ),
        (
            "După o interacțiune socială, cât timp petreci analizând ce ai spus și criticându-te ('am zis o prostie', 'am părut ciudat')?",
            "Post-Event Rumination, Shame", 2, 
            [
                ("A) Deloc. Trec mai departe.", 0), 
                ("B) Câteva minute.", 20), 
                ("C) Câteva ore.", 60), 
                ("D) Zile întregi. Mă chinuie amintirea.", 100)
            ]
        ),
        (
            "Te temi că ceilalți vor observa cât de anxios ești și te vor judeca pentru asta?",
            "Fear of Anxiety Symptoms", 2, 
            [
                ("A) Nu, și dacă observă, nu-mi pasă.", 0), 
                ("B) Sper să nu observe.", 30), 
                ("C) Da, asta mă stresează și mai tare.", 70), 
                ("D) Da, este cea mai mare frică a mea (frică de frică).", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Evitare Totală / Impact Viață) ---
        (
            "Ai refuzat joburi, promovări sau cursuri doar pentru că implicau vorbit în public sau interacțiune socială?",
            "Career Impact, Avoidance", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Am avut rețineri, dar am acceptat.", 30), 
                ("C) Da, am refuzat câteva oportunități.", 70), 
                ("D) Da, cariera mea este blocată din cauza asta.", 100)
            ]
        ),
        (
            "Folosești alcoolul sau substanțe ca pe o 'cârjă' pentru a putea face față situațiilor sociale?",
            "Coping Mechanism, Substance Use", 3, 
            [
                ("A) Nu, nu am nevoie.", 0), 
                ("B) Un pahar ajută, dar mă descurc și fără.", 20), 
                ("C) Mă simt mult mai sigur dacă beau ceva înainte.", 60), 
                ("D) Nu pot socializa deloc dacă sunt complet treaz.", 100)
            ]
        ),
        (
            "Dacă trebuie să folosești o toaletă publică și mai sunt și alții acolo, te blochezi (paruresis)?",
            "Shy Bladder, Social Phobia Specific", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Prefer să fiu singur, dar merge.", 20), 
                ("C) Uneori mă blochez.", 60), 
                ("D) Da, e imposibil. Aștept să plece toți.", 100)
            ]
        ),
        (
            "Cât de puternică este dorința de a fi invizibil când ești într-un grup?",
            "Invisibility, Shame", 3, 
            [
                ("A) Deloc. Îmi place să fiu văzut.", 0), 
                ("B) Uneori e bine să fii discret.", 20), 
                ("C) Prefer să nu fiu observat.", 60), 
                ("D) Copleșitoare. Aș vrea să dispar pur și simplu.", 100)
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
        log("db_conn", f"SUCCES: Întrebări Anxietate Socială inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()