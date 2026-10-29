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
AXIS_ID = 84
AXIS_NAME = "Sadism Cotidian"
# Pol 0: Empatic / Blând
# Pol 100: Sadic / Cruzime / Plăcere în suferință

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

    # Punctaj: 100 = SADISM (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Schadenfreude / Umor Negru) ---
        (
            "Când vezi videoclipuri pe internet cu oameni care se lovesc sau cad (fail compilation), care e reacția ta?",
            "Schadenfreude, Humor, Empathy", 
            1, 
            [
                ("A) Mă strâmb de durere, nu pot privi.", 0), 
                ("B) Nu mi se par amuzante.", 20), 
                ("C) Râd dacă nu e nimic grav.", 60), 
                ("D) Râd cu lacrimi, mai ales dacă se lovesc tare. E hilar.", 100)
            ]
        ),
        (
            "În jocurile video (sau filme), îți place să joci rolul personajului negativ care face rău gratuit?",
            "Gaming, Roleplay, Fantasy", 
            1, 
            [
                ("A) Nu, joc mereu eroul salvator.", 0), 
                ("B) Rar, de curiozitate.", 30), 
                ("C) Uneori e distractiv să fii 'bad guy'.", 60), 
                ("D) Da, ador să chinui NPC-urile sau să distrug tot.", 100)
            ]
        ),
        (
            "Ai simțit vreodată o satisfacție interioară când ai văzut pe cineva antipatic suferind o umilință publică?",
            "Vindictiveness, Satisfaction", 
            1, 
            [
                ("A) Nu, mi s-a făcut milă de el.", 0), 
                ("B) Indiferență.", 30), 
                ("C) Poate o mică satisfacție de moment.", 60), 
                ("D) Da, m-am bucurat enorm. Merita să sufere.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Comportament Social / Trolling) ---
        (
            "Îți place să trollezi oamenii pe internet sau să îi enervezi în discuții doar pentru a le vedea reacția?",
            "Trolling, Provocation, Social", 
            2, 
            [
                ("A) Nu, e o pierdere de timp și e răutăcios.", 0), 
                ("B) Doar dacă spun prostii mari.", 30), 
                ("C) Uneori e amuzant să îi agiți puțin.", 70), 
                ("D) Da, ador să îi văd cum își pierd cumpătul.", 100)
            ]
        ),
        (
            "Dacă ai ocazia să faci o glumă răutăcioasă despre cineva, chiar de față cu el, o faci?",
            "Cruelty, Humor, Bullying", 
            2, 
            [
                ("A) Nu, nu vreau să rănesc pe nimeni.", 0), 
                ("B) Mă abțin.", 30), 
                ("C) Dacă e o glumă foarte bună, poate îmi scapă.", 70), 
                ("D) Da, dacă e amuzant, nu contează cine se supără.", 100)
            ]
        ),
        (
            "Ai simțit vreodată nevoia să domini pe cineva fizic sau psihic doar pentru a-ți demonstra puterea?",
            "Dominance, Power, Control", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Poate în situații competitive (sport).", 30), 
                ("C) Uneori îmi place să dețin controlul.", 70), 
                ("D) Da, e o senzație puternică să vezi frica în ochii cuiva.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Patologie / Cruzime Fizică) ---
        (
            "În copilărie sau adolescență, ai chinuit vreodată insecte sau animale intenționat?",
            "Animal Cruelty, History, Psychopathology", 
            3, 
            [
                ("A) Nu! Iubesc animalele.", 0), 
                ("B) Poate am omorât furnici, dar nimic serios.", 30), 
                ("C) Am făcut câteva experimente din curiozitate.", 80), 
                ("D) Da, îmi făcea plăcere să le văd suferind.", 100)
            ]
        ),
        (
            "Dacă ai fi soldat în război, crezi că ai putea răni un inamic capturat dacă asta ți s-ar ordona?",
            "Violence, Authority, Cruelty", 
            3, 
            [
                ("A) Nu, aș refuza ordinul.", 0), 
                ("B) Doar dacă e absolut necesar pentru informații.", 40), 
                ("C) Probabil că da, e război.", 70), 
                ("D) Sincer, cred că m-ar incita ideea puterii absolute asupra lui.", 100)
            ]
        ),
        (
            "Te-ai simțit vreodată excitat sau energizat după ce ai făcut pe cineva să plângă?",
            "Emotional Sadism, Power", 
            3, 
            [
                ("A) Nu, m-am simțit groaznic și vinovat.", 0), 
                ("B) M-am simțit ciudat.", 30), 
                ("C) Am simțit că am câștigat argumentul.", 70), 
                ("D) Da, a fost un moment intens și satisfăcător.", 100)
            ]
        ),
        (
            "Consideri că lumea e împărțită în 'prădători' și 'pradă', și e mai bine să fii prădător?",
            "Worldview, Social Darwinism", 
            3, 
            [
                ("A) Nu, lumea e bazată pe cooperare.", 0), 
                ("B) E o viziune cam extremă.", 30), 
                ("C) Există un sâmbure de adevăr.", 60), 
                ("D) Da. Mila e pentru cei slabi.", 100)
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