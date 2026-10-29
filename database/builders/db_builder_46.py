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
AXIS_ID = 46
AXIS_NAME = "Visare (Abstractedness)"
# Pol Stânga (0): Prezent / Atent / Practic
# Pol Dreapta (100): Distrat / Visător / Cu capul în nori

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
    # Punctaj: 0 = Prezent, 100 = Visător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Atenție la Mediu) ---
        (
            "Cât de des ți se întâmplă să mergi pe stradă și să nu observi cunoscuții sau schimbările din peisaj pentru că ești pierdut în gânduri?",
            "Awareness, Environment, Daydreaming", 
            1, 
            [
                ("A) Niciodată. Sunt foarte observator.", 0), 
                ("B) Rar, dacă sunt foarte preocupat.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Zilnic. Merg pe pilot automat, mintea mea e altundeva.", 100)
            ]
        ),
        (
            "Ți se întâmplă să intri într-o cameră și să uiți complet de ce ai venit?",
            "Memory, Focus, Doorway Effect", 
            1, 
            [
                ("A) Nu, sunt foarte organizat mental.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori.", 60), 
                ("D) Da, mi se întâmplă constant.", 100)
            ]
        ),
        (
            "În timpul unei conversații, cât de ușor îți este să urmărești firul discuției fără să îți zboare mintea?",
            "Listening, Attention Span", 
            1, 
            [
                ("A) Sunt atent 100%.", 0), 
                ("B) Mă concentrez bine.", 30), 
                ("C) Uneori mă pierd în asocieri de idei.", 70), 
                ("D) Foarte greu. Adesea dau din cap aprobator dar mă gândesc la altceva.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Practic vs Teoretic) ---
        (
            "Cum te descurci cu detaliile practice și administrative (plata facturilor, formulare, organizarea actelor)?",
            "Admin, Practicality, Organization", 
            2, 
            [
                ("A) Excelent, totul e la zi.", 0), 
                ("B) Le fac la timp.", 30), 
                ("C) Le amân sau le uit uneori.", 70), 
                ("D) Sunt un dezastru. Uită de ele sau le greșesc din neatenție.", 100)
            ]
        ),
        (
            "Te împiedici des, scapi obiecte din mână sau te lovești de mobilă?",
            "Coordination, Awareness, Clumsiness", 
            2, 
            [
                ("A) Nu, am reflexe bune.", 0), 
                ("B) Rar, doar dacă sunt obosit.", 30), 
                ("C) Mai des decât media.", 70), 
                ("D) Da, sunt destul de neîndemânatic pentru că nu sunt atent la corp.", 100)
            ]
        ),
        (
            "Ce te atrage mai mult: implementarea concretă a unui proiect sau faza de idei și concepte?",
            "Work Style, Ideas vs Execution", 
            2, 
            [
                ("A) Implementarea. Vreau să văd rezultatul.", 0), 
                ("B) Îmi plac ambele.", 30), 
                ("C) Prefer ideile.", 70), 
                ("D) Conceptele abstracte. Detaliile de execuție mă plictisesc groaznic.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: ADHD-Inattentive / Disociere) ---
        (
            "Ți s-a reproșat vreodată că ești 'cu capul în nori' sau că nu ești conectat la realitate?",
            "Feedback, Reputation, Groundedness", 
            3, 
            [
                ("A) Niciodată. Sunt considerat foarte pragmatic.", 0), 
                ("B) Poate în glumă.", 30), 
                ("C) Da, de câteva ori.", 70), 
                ("D) Da, este principala critică pe care o primesc.", 100)
            ]
        ),
        (
            "Ai pățit să uiți oala pe foc, apa curgând sau fierul de călcat în priză pentru că te-ai pierdut în gânduri?",
            "Safety, Neglect, Attention", 
            3, 
            [
                ("A) Doamne ferește, nu! Sunt foarte precaut.", 0), 
                ("B) Verific mereu.", 20), 
                ("C) O dată mi s-a întâmplat.", 70), 
                ("D) Da, am avut incidente din cauza asta.", 100)
            ]
        ),
        (
            "Ai o viață interioară atât de intensă și bogată încât lumea exterioară ți se pare uneori ștearsă sau neinteresantă?",
            "Inner World, Introversion, Imagination", 
            3, 
            [
                ("A) Nu, viața reală e cea care contează.", 0), 
                ("B) Îmi place să visez, dar realitatea e prioritară.", 30), 
                ("C) Uneori prefer lumea mea.", 70), 
                ("D) Da. Mă refugiez constant în mintea mea, e mult mai fascinant acolo.", 100)
            ]
        ),
        (
            "Ți se întâmplă să conduci mașina (sau să mergi pe jos) pe o distanță lungă și să nu îți amintești nimic din drumul parcurs?",
            "Autopilot, Dissociation", 
            3, 
            [
                ("A) Nu, sunt atent la trafic.", 0), 
                ("B) Rar, pe drumuri foarte cunoscute.", 30), 
                ("C) Uneori intru pe pilot automat.", 60), 
                ("D) Da, mă 'trezesc' la destinație fără să știu cum am ajuns.", 100)
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