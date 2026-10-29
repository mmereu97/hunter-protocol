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
AXIS_ID = 5
AXIS_NAME = "Frică Fizică"
# Pol Stânga (0): Curajos / Temerar / Riscant
# Pol Dreapta (100): Prudent / Temător / Siguranță

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
    # Punctaj: 0 = Curajos (Riscant), 100 = Fricos (Prudent)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General) ---
        (
            "Cum te simți în situații care implică un risc fizic minor (de exemplu, turbulențe în avion sau mers pe gheață)?",
            "Survival, Anxiety, Physical", 
            1, 
            [
                ("A) Nu mă afectează deloc, sunt relaxat.", 0), 
                ("B) Ușor alert, dar stăpân pe situație.", 30), 
                ("C) Destul de nervos/încordat.", 70), 
                ("D) Mă panichez sau evit complet situația.", 100)
            ]
        ),
        (
            "Cât de des te îngrijorezi că te-ai putea răni sau îmbolnăvi grav?",
            "Health, Hypochondria, Worry", 
            1, 
            [
                ("A) Aproape niciodată. Corpul rezistă.", 0), 
                ("B) Rar, doar dacă am simptome clare.", 30), 
                ("C) Destul de des, sunt atent la sănătate.", 70), 
                ("D) Foarte des, orice durere mă sperie.", 100)
            ]
        ),
        (
            "Dacă ai auzi un zgomot puternic și neașteptat noaptea în casă, care ar fi prima reacție?",
            "Startle Response, Fear, Instinct", 
            1, 
            [
                ("A) Mă duc imediat să verific, poate iau și ceva de apărare.", 0), 
                ("B) Ascult cu atenție înainte să acționez.", 30), 
                ("C) Mă sperii și mă blochez puțin.", 70), 
                ("D) Intru în panică și sun pe cineva sau mă ascund.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Activități/Adrenalină) ---
        (
            "Ce părere ai despre sporturile extreme (parașutism, bungee jumping, alpinism liber)?",
            "Risk Taking, Adrenaline, Hobby", 
            2, 
            [
                ("A) Le ador, aș încerca oricând.", 0), 
                ("B) Par interesante, poate aș încerca o dată controlat.", 30), 
                ("C) Nu m-aș risca, mi se par periculoase.", 70), 
                ("D) Sunt o nebunie curată, nu aș face asta niciodată.", 100)
            ]
        ),
        (
            "Cât de confortabil te simți la înălțimi mari (pe marginea unei prăpăstii sau pe o clădire înaltă)?",
            "Phobia, Heights, Physical", 
            2, 
            [
                ("A) Foarte confortabil, îmi place priveliștea.", 0), 
                ("B) Simt un mic gol în stomac, dar e ok.", 30), 
                ("C) Amețesc și prefer să stau mai în spate.", 70), 
                ("D) Mă blochez de frică, nu mă pot apropia.", 100)
            ]
        ),
        (
            "Dacă jobul tău ar implica manevrarea unor utilaje periculoase sau lucrul în medii toxice, dar bine plătit, ai accepta?",
            "Career, Risk vs Money, Safety", 
            2, 
            [
                ("A) Da, riscul face parte din viață.", 0), 
                ("B) Da, dacă protecția e decentă.", 30), 
                ("C) Aș ezita mult, sănătatea e prioritară.", 70), 
                ("D) Nu, niciun ban nu merită riscul fizic.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Neglijență vs Anxietate Extremă) ---
        (
            "Imaginează-ți că trebuie să treci noaptea printr-un cartier rău famat sau o zonă pustie. Ce faci?",
            "Danger, Street Smart, Fear", 
            3, 
            [
                ("A) Trec liniștit, știu să mă apăr.", 0), 
                ("B) Sunt foarte atent, merg repede.", 30), 
                ("C) Caut o rută ocolitoare, chiar dacă durează mai mult.", 70), 
                ("D) Refuz categoric să merg pe acolo, iau taxi sau nu mă duc.", 100)
            ]
        ),
        (
            "Cât de mult îți este frică de durerea fizică (injecții, dentis, lovituri)?",
            "Pain Tolerance, Resilience", 
            3, 
            [
                ("A) Deloc. Durerea e doar o senzație.", 0), 
                ("B) O suport dacă e nevoie.", 30), 
                ("C) Îmi este frică, amân procedurile medicale dureroase.", 70), 
                ("D) Sunt terifiat, leșin sau fac atac de panică.", 100)
            ]
        ),
        (
            "Ai tendința să verifici de mai multe ori dacă ai încuiat ușa sau ai oprit gazele de frica unui dezastru?",
            "Safety, OCD tendencies, Fear", 
            3, 
            [
                ("A) Nu, verific o dată și gata.", 0), 
                ("B) Uneori, dacă sunt distrat.", 30), 
                ("C) Da, verific des pentru siguranță.", 70), 
                ("D) Da, mă întorc din drum să verific, am o frică constantă.", 100)
            ]
        ),
        (
            "În caz de război sau calamitate naturală, crezi că ai fi capabil să acționezi eroic sau prioritatea ar fi să te ascunzi?",
            "Survival, Heroism, Fight or Flight", 
            3, 
            [
                ("A) Aș lupta / aș ajuta în prima linie.", 0), 
                ("B) Aș ajuta, dar cu prudență.", 30), 
                ("C) M-aș asigura întâi că familia mea e în siguranță.", 70), 
                ("D) M-aș ascunde și aș evita orice pericol. Supraviețuirea mea contează.", 100)
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