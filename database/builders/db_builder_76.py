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
AXIS_ID = 76
AXIS_NAME = "Dezinhibiție (Impulsivitate Patologică)"
# Pol 0: Prudent / Controlat
# Pol 100: Dezinhibat / Riscant / Nesăbuit

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

    # Punctaj: 100 = DEZINHIBAT (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Control / Filtru) ---
        (
            "Cât de des spui lucruri pe care le regreți imediat după ce le-ai rostit?",
            "Verbal Impulsivity, Filter", 
            1, 
            [
                ("A) Niciodată. Gândesc înainte să vorbesc.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori, când sunt nervos.", 60), 
                ("D) Foarte des. Nu am 'filtru', zic ce-mi vine.", 100)
            ]
        ),
        (
            "Dacă îți vine o idee nebunească sau riscantă, cât de probabil este să o pui în practică?",
            "Risk Taking, Spontaneity", 
            1, 
            [
                ("A) Improbabil. Analizez riscurile.", 0), 
                ("B) Mă gândesc de două ori.", 30), 
                ("C) Destul de probabil.", 70), 
                ("D) O fac imediat! Viața e scurtă.", 100)
            ]
        ),
        (
            "Cum stai cu economiile și gestionarea banilor?",
            "Financial Impulsivity, Planning", 
            1, 
            [
                ("A) Sunt foarte chibzuit, am economii.", 0), 
                ("B) Cheltui rezonabil.", 30), 
                ("C) Cumpăr des lucruri de care nu am nevoie.", 70), 
                ("D) Cheltui tot ce am imediat. Trăiesc de la un salariu la altul.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Consecințe / Planificare) ---
        (
            "Te gândești la consecințele pe termen lung ale acțiunilor tale?",
            "Future Orientation, Consequences", 
            2, 
            [
                ("A) Întotdeauna. Viitorul e prioritar.", 0), 
                ("B) Da, de obicei.", 30), 
                ("C) Uneori, dar prefer prezentul.", 70), 
                ("D) Nu. Ce va fi, va fi. Trăiesc clipa.", 100)
            ]
        ),
        (
            "Ai tendința să faci promisiuni pe care apoi nu le poți respecta pentru că ți-ai schimbat starea de spirit?",
            "Reliability, Mood Instability", 
            2, 
            [
                ("A) Nu, cuvântul meu e sfânt.", 0), 
                ("B) Încerc să mă țin de ele.", 30), 
                ("C) Uneori mă entuziasmez prea tare.", 70), 
                ("D) Da. Promit orice pe moment, apoi uit sau nu mai am chef.", 100)
            ]
        ),
        (
            "Cât de ușor te plictisești de sarcini care necesită atenție susținută și rutină?",
            "Boredom, Focus, Disinhibition", 
            2, 
            [
                ("A) Rezist bine, am disciplină.", 0), 
                ("B) Mă plictisesc, dar termin.", 30), 
                ("C) Îmi pierd răbdarea repede.", 70), 
                ("D) Abandonez imediat. Nu suport plictiseala.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Risc Major / Iresponsabilitate) ---
        (
            "Ai avut vreodată probleme din cauza comportamentului sexual impulsiv sau riscant?",
            "Sexual Impulsivity, Risk", 
            3, 
            [
                ("A) Nu, sunt precaut și fidel.", 0), 
                ("B) Nu cred.", 20), 
                ("C) Am avut câteva aventuri neplanificate.", 60), 
                ("D) Da. Mă las dus de val ușor în situații intime.", 100)
            ]
        ),
        (
            "Dacă ești provocat, poți să te abții să nu reacționezi violent sau agresiv?",
            "Emotional Regulation, Aggression", 
            3, 
            [
                ("A) Da, am control total.", 0), 
                ("B) Mă abțin cu greu.", 30), 
                ("C) De obicei cedez și urlu.", 70), 
                ("D) Nu. Reacționez instantaneu, fără să gândesc.", 100)
            ]
        ),
        (
            "Ai condus vreodată cu viteză excesivă sau ai făcut depășiri periculoase doar pentru senzație?",
            "Reckless Driving, Danger", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Doar puțin peste limită.", 20), 
                ("C) Uneori îmi place viteza.", 60), 
                ("D) Da, conduc agresiv și riscant frecvent.", 100)
            ]
        ),
        (
            "Ai probleme cu abuzul de substanțe (alcool, etc) pentru că nu te poți opri odată ce ai început?",
            "Addiction, Self-Control", 
            3, 
            [
                ("A) Nu, consum responsabil sau deloc.", 0), 
                ("B) Îmi cunosc limita.", 20), 
                ("C) Uneori exagerez la petreceri.", 60), 
                ("D) Da. Dacă încep, nu mă pot opri până nu e gata totul.", 100)
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