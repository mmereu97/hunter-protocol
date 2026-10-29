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
AXIS_ID = 28
AXIS_NAME = "Dorința de Realizare"
# Pol Stânga (0): Neambițios / Relaxat / Mulțumit
# Pol Dreapta (100): Ambițios / Competitiv / Orientat spre Succes

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
    # Punctaj: 0 = Neambițios, 100 = Ambițios
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Obiective/Muncă) ---
        (
            "Cum te raportezi la ideea de a avansa în carieră (promovări, funcții înalte)?",
            "Career, Ambition, Promotion", 
            1, 
            [
                ("A) Nu mă interesează. Vreau doar un salariu decent și liniște.", 0), 
                ("B) Dacă se întâmplă, e bine, dar nu mă zbat.", 30), 
                ("C) Este important pentru mine să evoluez.", 70), 
                ("D) Este scopul meu principal. Vreau să ajung în vârf.", 100)
            ]
        ),
        (
            "Te simți satisfăcut dacă faci doar strictul necesar la un proiect?",
            "Standards, Effort, Mediocrity", 
            1, 
            [
                ("A) Da, de ce să muncesc în plus?", 0), 
                ("B) Uneori, dacă sunt obosit.", 30), 
                ("C) Nu prea, îmi place să fac lucrurile bine.", 70), 
                ("D) Niciodată. Vreau să exceleze în tot ce fac.", 100)
            ]
        ),
        (
            "Ce te motivează mai mult: relaxarea sau sentimentul de a atinge un obiectiv dificil?",
            "Motivation, Goals vs Leisure", 
            1, 
            [
                ("A) Relaxarea, clar.", 0), 
                ("B) Relaxarea, dar îmi plac și micile victorii.", 30), 
                ("C) Atingerea obiectivelor.", 70), 
                ("D) Provocarea. Fără obiective grele mă plictisesc.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Competiție/Sacrificiu) ---
        (
            "Ești o persoană competitivă? Îți place să fii mai bun decât ceilalți?",
            "Competition, Comparison, Drive", 
            2, 
            [
                ("A) Deloc. Competiția mă stresează.", 0), 
                ("B) Puțin, dar prefer cooperarea.", 30), 
                ("C) Da, competiția mă motivează.", 70), 
                ("D) Da, vreau să câștig mereu. Locul 2 e primul perdant.", 100)
            ]
        ),
        (
            "Cât timp liber ești dispus să sacrifici pentru succesul profesional?",
            "Sacrifice, Work-Life Balance", 
            2, 
            [
                ("A) Niciun minut. Timpul meu e sacru.", 0), 
                ("B) Ocazional, dacă e o urgență.", 30), 
                ("C) Sunt dispus să fac ore suplimentare pentru carieră.", 70), 
                ("D) Tot timpul necesar. Succesul cere sacrificii.", 100)
            ]
        ),
        (
            "Cum te simți când vezi pe cineva de vârsta ta care a realizat mult mai multe decât tine?",
            "Envy, Inspiration, Comparison", 
            2, 
            [
                ("A) Nu mă afectează, fiecare cu ritmul lui.", 0), 
                ("B) Mă bucur pentru el.", 30), 
                ("C) Mă simt motivat să trag mai tare.", 70), 
                ("D) Mă simt frustrat și invidios, simt că am rămas în urmă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Workaholism / Narcisism / Burnout) ---
        (
            "Te definești în primul rând prin munca și realizările tale?",
            "Identity, Self-Worth, Work", 
            3, 
            [
                ("A) Nu, munca e doar ce fac ca să am bani.", 0), 
                ("B) Sunt doar o parte din mine.", 30), 
                ("C) Sunt o parte importantă a identității mele.", 70), 
                ("D) Da. Sunt ceea ce realizez.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să neglijezi familia, prietenii sau sănătatea pentru a atinge un obiectiv?",
            "Obsession, Priorities, Neglect", 
            3, 
            [
                ("A) Nu, prioritățile mele sunt clare (viața personală).", 0), 
                ("B) Foarte rar.", 30), 
                ("C) Da, în perioadele aglomerate.", 70), 
                ("D) Da, des. Succesul are un preț.", 100)
            ]
        ),
        (
            "Dacă nu ai un scop clar sau un proiect în desfășurare, te simți inutil sau anxios?",
            "Restlessness, Purpose, Anxiety", 
            3, 
            [
                ("A) Nu, mă bucur de liniște.", 0), 
                ("B) Mă plictisesc puțin.", 30), 
                ("C) Simt nevoia să găsesc ceva de făcut.", 70), 
                ("D) Da, mă simt groaznic dacă nu progresez.", 100)
            ]
        ),
        (
            "Îți setezi standarde atât de înalte încât ești rareori mulțumit de rezultate?",
            "Perfectionism, Satisfaction, High Standards", 
            3, 
            [
                ("A) Nu, mă mulțumesc cu 'suficient de bun'.", 0), 
                ("B) Sunt realist.", 30), 
                ("C) Am standarde înalte, dar mă bucur de succes.", 60), 
                ("D) Da, nimic nu e niciodată suficient de bun. Vreau mai mult.", 100)
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