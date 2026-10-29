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
AXIS_ID = 75
AXIS_NAME = "Alexitimie (Orbire Emoțională)"
# Pol 0: Conectat / Introspectiv
# Pol 100: Alexitimic / Robot / Deconectat

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

    # Punctaj: 100 = ALEXITIMIE (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Identificare Emoții) ---
        (
            "Când ești întrebat 'Ce simți acum?', cât de ușor îți este să răspunzi specific?",
            "Emotional Awareness, Vocabulary", 
            1, 
            [
                ("A) Foarte ușor. Pot descrie nuanțe fine.", 0), 
                ("B) Pot spune dacă e bine sau rău.", 30), 
                ("C) E greu. De obicei zic doar 'ok' sau 'obosit'.", 70), 
                ("D) Nu știu. Emoțiile sunt un mister pentru mine.", 100)
            ]
        ),
        (
            "Ți se întâmplă să ai reacții fizice (dureri de stomac, inimă care bate tare) fără să știi ce emoție le-a provocat?",
            "Somatic vs Emotional, Confusion", 
            1, 
            [
                ("A) Nu, știu mereu cauza.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori cred că sunt bolnav, dar doctorii zic că e stres.", 70), 
                ("D) Da, des. Simt totul în corp, nu în minte.", 100)
            ]
        ),
        (
            "Partenerii sau prietenii ți-au reproșat vreodată că ești 'rece', 'distant' sau că nu vorbești despre sentimente?",
            "Social Feedback, Coldness", 
            1, 
            [
                ("A) Nu, sunt considerat foarte cald.", 0), 
                ("B) Nu, sunt normal.", 20), 
                ("C) Mi s-a spus că sunt prea logic.", 60), 
                ("D) Da, des. Nu înțeleg ce vor de la mine.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Gândire Concretă / Lipsă Fantezie) ---
        (
            "Preferi să vorbești despre fapte concrete și activități zilnice decât despre trăiri interioare sau visuri?",
            "Concrete Thinking, External Oriented", 
            2, 
            [
                ("A) Nu, ador discuțiile profunde despre suflet.", 0), 
                ("B) Îmi place un echilibru.", 30), 
                ("C) Prefer lucrurile concrete.", 60), 
                ("D) Da. Discuțiile despre sentimente sunt pierdere de timp.", 100)
            ]
        ),
        (
            "Cât de des visezi cu ochii deschiși sau îți folosești imaginația pentru a crea scenarii?",
            "Fantasy Life, Imagination", 
            2, 
            [
                ("A) Tot timpul. Am o lume interioară bogată.", 0), 
                ("B) Ocazional.", 30), 
                ("C) Rar.", 70), 
                ("D) Niciodată. Mă gândesc doar la probleme reale.", 100)
            ]
        ),
        (
            "Dacă vezi pe cineva plângând, înțelegi intuitiv de ce sau trebuie să analizezi logic situația?",
            "Empathy, Intuition vs Logic", 
            2, 
            [
                ("A) Simt imediat durerea lor.", 0), 
                ("B) Înțeleg contextul.", 30), 
                ("C) Trebuie să întreb ce s-a întâmplat.", 60), 
                ("D) Mă simt confuz și nu știu cum să reacționez. E ilogic.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Deconectare Totală / Confuzie) ---
        (
            "Ți se întâmplă să plângi și să nu ai nicio idee de ce?",
            "Emotional Disconnection, Confusion", 
            3, 
            [
                ("A) Nu, știu mereu motivul.", 0), 
                ("B) Poate de oboseală.", 30), 
                ("C) Mi s-a întâmplat.", 60), 
                ("D) Da. Corpul reacționează, dar mintea mea e goală.", 100)
            ]
        ),
        (
            "Uneori nu poți face diferența între senzația de foame, oboseală și o emoție negativă (tristețe/furie)?",
            "Interoception, Affect Differentiation", 
            3, 
            [
                ("A) Le deosebesc perfect.", 0), 
                ("B) Uneori sunt 'hangry' (nervos de foame).", 20), 
                ("C) Deseori le confund.", 70), 
                ("D) Da, pentru mine totul e doar o stare de disconfort general.", 100)
            ]
        ),
        (
            "Consideri că emoțiile sunt o slăbiciune inutilă și că oamenii ar trebui să fie ca niște calculatoare?",
            "Beliefs, Logic vs Emotion", 
            3, 
            [
                ("A) Nu, emoțiile ne fac oameni.", 0), 
                ("B) Emoțiile sunt utile, dar trebuie controlate.", 30), 
                ("C) Ar fi mai simplu fără ele.", 60), 
                ("D) Da. Emoțiile sunt erori de sistem ilogice.", 100)
            ]
        ),
        (
            "Te simți ca un spectator în propria viață, privind evenimentele fără să fii implicat afectiv?",
            "Detachment, Depersonalization", 
            3, 
            [
                ("A) Nu, trăiesc intens.", 0), 
                ("B) Doar când sunt foarte stresat.", 20), 
                ("C) Uneori mă simt amorțit.", 60), 
                ("D) Da. Sunt ca un robot care execută sarcini.", 100)
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