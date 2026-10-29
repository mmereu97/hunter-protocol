import sqlite3
import hashlib
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 103
AXIS_NAME = "ADHD (Disfuncție Executivă)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = ADHD ACTIV
    questions_data = [
        # --- VALUL 1: SCREENING (Atenție / Organizare) ---
        (
            "Cât de des ai dificultăți în a-ți menține atenția la sarcini plictisitoare sau repetitive (ex: rapoarte, curățenie)?",
            "Focus, Boredom", 1, 
            [("A) Niciodată. Am răbdare.", 0), ("B) Uneori îmi zboară gândul.", 30), ("C) Deseori, trebuie să mă forțez.", 70), ("D) Foarte des. Mintea mea pleacă singură după 5 minute.", 100)]
        ),
        (
            "Când cineva îți vorbește direct, ți se întâmplă să nu auzi ce zice, deși pare că asculți?",
            "Listening, Zoning Out", 1, 
            [("A) Nu, sunt atent.", 0), ("B) Rar.", 20), ("C) Uneori, dacă sunt obosit.", 60), ("D) Da, des. Îmi spun 'pământul către tine?'.", 100)]
        ),
        (
            "Cât de des pierzi sau rătăcești lucruri necesare (chei, telefon, ochelari)?",
            "Memory, Objects", 1, 
            [("A) Niciodată.", 0), ("B) Rar.", 20), ("C) Destul de des.", 60), ("D) Zilnic. E frustrant.", 100)]
        ),

        # --- VALUL 2: CONFIRMARE (Hiperactivitate / Impulsivitate) ---
        (
            "Simți adesea o neliniște interioară, ca și cum ai fi condus de un motor, și nu poți sta locului?",
            "Restlessness, Hyperactivity", 2, 
            [("A) Nu, sunt calm.", 0), ("B) Doar la stres.", 20), ("C) Da, dau din picior sau mă foiesc.", 70), ("D) Da, e o nevoie fizică de a mă mișca.", 100)]
        ),
        (
            "Ai tendința să termini propozițiile altora sau să intervii în discuție înainte să îți vină rândul?",
            "Impulsivity, Conversation", 2, 
            [("A) Nu, sunt politicos.", 0), ("B) Încerc să mă abțin.", 30), ("C) Uneori, de entuziasm.", 60), ("D) Da, nu am răbdare să termine ideea.", 100)]
        ),
        (
            "Cât de greu îți este să te apuci de o sarcină care necesită mult efort mental susținut?",
            "Procrastination, Executive Function", 2, 
            [("A) O fac imediat.", 0), ("B) O planific și mă țin de plan.", 20), ("C) Amân până la limită.", 70), ("D) E un chin. Paralizez și fac orice altceva.", 100)]
        ),

        # --- VALUL 3: DEEP DIVE (Disfuncție Executivă Gravă) ---
        (
            "Ai multe proiecte începute și neterminate?",
            "Completion, Project Management", 3, 
            [("A) Nu, termin ce încep.", 0), ("B) Câteva.", 30), ("C) Da, mă entuziasmez la început apoi abandonez.", 70), ("D) Da, viața mea e un cimitir de proiecte neterminate.", 100)]
        ),
        (
            "Ți se întâmplă să faci greșeli din neglijență la detalii, deși știai cum să faci corect?",
            "Careless Mistakes, Details", 3, 
            [("A) Nu, verific.", 0), ("B) Rar.", 20), ("C) Uneori, din grabă.", 60), ("D) Da, omit detalii evidente constant.", 100)]
        ),
        (
            "Uiți des întâlniri, obligații sau promisiuni, chiar dacă erau importante?",
            "Memory, Reliability", 3, 
            [("A) Nu, am agendă.", 0), ("B) Rar, dacă nu notez.", 30), ("C) Mi se mai întâmplă.", 70), ("D) Da, îmi afectează relațiile și munca.", 100)]
        ),
        (
            "Te simți copleșit de sarcinile administrative (birocrație, formulare, organizare)?",
            "Admin, Overwhelm", 3, 
            [("A) Nu, mă descurc.", 0), ("B) Nu îmi plac, dar le fac.", 30), ("C) Le amân la infinit.", 70), ("D) Da, mă blochez total în fața lor.", 100)]
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
        log("db_conn", f"SUCCES: Întrebări ADHD inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()