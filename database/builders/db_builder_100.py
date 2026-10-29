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
AXIS_ID = 100
AXIS_NAME = "Micromanagement"
# Pol 0: Delegă / Încredere
# Pol 100: Control Freak / Micromanagement

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

    # Punctaj: 100 = MICROMANAGER (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Delegare / Stil de Lucru) ---
        (
            "Când delegi o sarcină unui subaltern sau coleg, cât de des verifici progresul?",
            "Delegation, Trust, Monitoring", 
            1, 
            [
                ("A) Stabilim un termen și verific doar la final.", 0), 
                ("B) Stabilim niște puncte de control intermediare.", 30), 
                ("C) Verific zilnic, să fiu sigur că e bine.", 70), 
                ("D) Verific constant, pas cu pas. Nu vreau surprize.", 100)
            ]
        ),
        (
            "Ce simți când cineva rezolvă o sarcină folosind o metodă diferită de a ta, dar ajunge la același rezultat?",
            "Flexibility, Control, Process", 
            1, 
            [
                ("A) Mă bucur că a fost creativ.", 0), 
                ("B) E ok, atâta timp cât rezultatul e bun.", 30), 
                ("C) Mă irită puțin, metoda mea era mai eficientă.", 70), 
                ("D) Nu accept. Trebuie făcută exact cum am spus eu.", 100)
            ]
        ),
        (
            "Cât de des te plângi că 'dacă vrei un lucru bine făcut, trebuie să-l faci singur'?",
            "Motto, Beliefs, Trust", 
            1, 
            [
                ("A) Niciodată. Cred în puterea echipei.", 0), 
                ("B) Rar, la chestii foarte specifice.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Zilnic. E motto-ul vieții mele profesionale.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Corectare / Detalii) ---
        (
            "Ai tendința să refaci munca altora (să rescrii emailuri, să reformatezi documente) fără să le spui?",
            "Redoing Work, Perfectionism", 
            2, 
            [
                ("A) Nu, le dau feedback să corecteze ei.", 0), 
                ("B) Doar dacă e o urgență majoră.", 30), 
                ("C) Da, e mai rapid decât să le explic.", 70), 
                ("D) Da, mereu. Nimeni nu are standardele mele.", 100)
            ]
        ),
        (
            "Când ești în concediu, cât de des verifici emailul sau suni la birou?",
            "Detachment, Trust, Anxiety", 
            2, 
            [
                ("A) Deloc. Au ei grijă.", 0), 
                ("B) Verific o dată la câteva zile.", 30), 
                ("C) Zilnic, dimineața.", 70), 
                ("D) Sunt conectat non-stop. Se prăbușește totul fără mine.", 100)
            ]
        ),
        (
            "Vrei să fii pus în CC la toate emailurile pe care le trimite echipa ta?",
            "Communication, Control, Insecurity", 
            2, 
            [
                ("A) Nu, doar la cele critice. Nu vreau spam.", 0), 
                ("B) Doar la începutul proiectelor.", 30), 
                ("C) Prefer să fiu în CC ca să fiu informat.", 70), 
                ("D) Obligatoriu la toate. Trebuie să monitorizez comunicarea.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Obsesie / Lipsă de Respect) ---
        (
            "Te simți neliniștit sau anxios când nu știi exact ce face fiecare membru al echipei în fiecare moment?",
            "Anxiety, Surveillance, Control", 
            3, 
            [
                ("A) Nu, mă interesează rezultatele, nu prezența.", 0), 
                ("B) Puțin, dar mă abțin să verific.", 30), 
                ("C) Da, vreau rapoarte de activitate detaliate.", 70), 
                ("D) Da, simt că dacă nu îi supraveghezi, nu muncesc.", 100)
            ]
        ),
        (
            "Consideri că rolul unui manager este să prindă greșelile angajaților înainte ca acestea să se întâmple?",
            "Management Style, Error Prevention", 
            3, 
            [
                ("A) Nu, rolul e să îi dezvolte și să îi ghideze.", 0), 
                ("B) Trebuie să prevină riscurile mari.", 30), 
                ("C) Da, trebuie să filtreze tot.", 70), 
                ("D) Da, trebuie să fie un 'filtru absolut'. Nimic nu iese fără aprobarea mea.", 100)
            ]
        ),
        (
            "Cât de greu îți este să lași pe altcineva să ia o decizie finală?",
            "Decision Making, Power Hoarding", 
            3, 
            [
                ("A) Ușor, dacă e responsabilitatea lui.", 0), 
                ("B) Depinde de miza deciziei.", 30), 
                ("C) Greu, prefer să am ultimul cuvânt.", 70), 
                ("D) Imposibil. Eu semnez tot.", 100)
            ]
        ),
        (
            "Ai fost vreodată acuzat de angajați sau colegi că îi 'sufoci' sau că nu le dai spațiu?",
            "Feedback, Awareness", 
            3, 
            [
                ("A) Nu, dimpotrivă.", 0), 
                ("B) Poate în glumă.", 30), 
                ("C) Mi s-a sugerat să deleg mai mult.", 70), 
                ("D) Da, dar ei nu înțeleg cât de importantă e calitatea.", 100)
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