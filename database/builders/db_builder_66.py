import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS & IMPORTS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 66
AXIS_NAME = "Auto-reglare (Control)"
# Pol Stânga (0): Impulsiv / Reactiv / Slabă voință
# Pol Dreapta (100): Controlat / Disciplinat / Abținere

# 3. FUNCȚIA DE HASHING
def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu a fost găsită la: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", f"Populăm Axa {AXIS_ID}: {AXIS_NAME}...")

    # 4. DATASET-UL
    # Punctaj: 0 = Impulsiv, 100 = Controlat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Tentații/Răbdare) ---
        (
            "Dacă încerci să ții o dietă sau să economisești bani, cât de des cedezi primei tentații (o prăjitură, o reducere)?",
            "Willpower, Diet, Spending", 
            1, 
            [
                ("A) Aproape imediat. Nu mă pot abține.", 0), 
                ("B) Rezist o perioadă, apoi cedez.", 30), 
                ("C) De obicei mă țin de plan.", 70), 
                ("D) Niciodată. Dacă am decis ceva, așa rămâne.", 100)
            ]
        ),
        (
            "Ești la o petrecere și știi că trebuie să conduci sau să lucrezi dimineața. Te oprești din băut/distracție la timp?",
            "Limits, Responsibility, Self-Control", 
            1, 
            [
                ("A) Nu, mă las dus de val și regret a doua zi.", 0), 
                ("B) Îmi e greu să plec.", 30), 
                ("C) Plec la ora stabilită.", 70), 
                ("D) Da, am limite stricte pe care nu le încalc.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să te concentrezi pe o sarcină plictisitoare când telefonul sună sau primești notificări?",
            "Focus, Distraction, Discipline", 
            1, 
            [
                ("A) Imposibil. Verific imediat.", 0), 
                ("B) Mă uit, apoi încerc să revin.", 30), 
                ("C) Ignor notificările o vreme.", 70), 
                ("D) Telefonul e pe silent. Nu mă întrerup.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Obiceiuri/Impuls) ---
        (
            "Dacă te enervezi într-o discuție, îți poți opri reacția fizică (gesturi, ton ridicat) înainte să se manifeste?",
            "Anger Management, Impulse Control", 
            2, 
            [
                ("A) Nu, reacționez instantaneu.", 0), 
                ("B) Uneori îmi scapă gesturi nervoase.", 30), 
                ("C) Mă controlez destul de bine.", 70), 
                ("D) Da, rămân imobil și calm exterior.", 100)
            ]
        ),
        (
            "Ai obiceiuri proaste (fumat, unghii roase, jocuri) de care ai încercat să scapi și nu ai reușit?",
            "Habits, Addiction, Willpower", 
            2, 
            [
                ("A) Da, am multe și nu pot renunța.", 0), 
                ("B) Mă lupt cu ele constant.", 30), 
                ("C) Am reușit să elimin câteva.", 70), 
                ("D) Nu, dacă un obicei e nociv, îl opresc imediat.", 100)
            ]
        ),
        (
            "Preferi o recompensă mică acum (ex: 100 lei) sau una dublă peste o lună (200 lei)?",
            "Delayed Gratification, Patience", 
            2, 
            [
                ("A) Acum. Cine știe ce e peste o lună?", 0), 
                ("B) Probabil acum, am nevoie.", 30), 
                ("C) Aș aștepta o lună.", 70), 
                ("D) Aștept oricât e nevoie pentru câștigul maxim.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Dezinhibiție / Adicție / ADHD) ---
        (
            "Ți se întâmplă să faci cumpărături impulsive de valori mari, pe care apoi le regreți sau le returnezi?",
            "Impulsive Buying, Regret", 
            3, 
            [
                ("A) Da, des. Nu mă pot opri.", 0), 
                ("B) Uneori cheltui peste buget.", 30), 
                ("C) Rar, sunt chibzuit.", 70), 
                ("D) Niciodată. Fiecare cheltuială e planificată.", 100)
            ]
        ),
        (
            "Ai tendința să întrerupi oamenii pentru că ți-a venit o idee și ți-e teamă că o uiți?",
            "Social Impulsivity, Conversation", 
            3, 
            [
                ("A) Da, mereu. E mai puternic decât mine.", 0), 
                ("B) Deseori.", 30), 
                ("C) Încerc să îmi notez ideea.", 70), 
                ("D) Nu, am răbdare să termine.", 100)
            ]
        ),
        (
            "Dacă ai o zi liberă fără niciun plan, ce faci?",
            "Structure, Initiative, Laziness", 
            3, 
            [
                ("A) Lenevesc toată ziua, pierd timpul.", 0), 
                ("B) Fac ce am chef pe moment.", 30), 
                ("C) Fac câteva treburi casnice.", 70), 
                ("D) Îmi structurez ziua productiv chiar și în vacanță.", 100)
            ]
        ),
        (
            "Cât de des acționezi pe baza vorbei 'O viață avem' pentru a justifica o decizie riscantă sau nesănătoasă?",
            "Rationalization, Risk, Hedonism", 
            3, 
            [
                ("A) Foarte des. Trebuie să te bucuri.", 0), 
                ("B) La petreceri.", 30), 
                ("C) Rar.", 70), 
                ("D) Niciodată. Prudența și sănătatea sunt prioritare.", 100)
            ]
        )
    ]

    try:
        # 5. CURĂȚARE
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"Curățat întrebări vechi pentru Axa {AXIS_ID}.")

        # 6. INSERARE
        count = 0
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
            count += 1

        conn.commit()
        log("db_conn", f"SUCCES: {count} întrebări inserate pentru {AXIS_NAME}.")

    except Exception as e:
        log_error(f"Eroare Axa {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()