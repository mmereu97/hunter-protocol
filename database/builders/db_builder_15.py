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
AXIS_ID = 15
AXIS_NAME = "Sociabilitate"
# Pol Stânga (0): Introvertit / Pustnic / Solitar
# Pol Dreapta (100): Extrovertit / Gregar / Sociabil

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
    # Punctaj: 0 = Introvertit, 100 = Extrovertit
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Baterie Socială/Preferințe) ---
        (
            "După o săptămână lungă și obositoare de muncă, cum preferi să îți petreci seara de vineri?",
            "Recharge, Social Battery, Lifestyle", 
            1, 
            [
                ("A) Singur acasă, cu o carte sau un film. Am nevoie de liniște.", 0), 
                ("B) Doar cu partenerul sau familia restrânsă.", 30), 
                ("C) O ieșire la cină cu câțiva prieteni apropiați.", 70), 
                ("D) Într-un club sau la o petrecere mare. Vreau să văd lume!", 100)
            ]
        ),
        (
            "Cum te simți după 3-4 ore de socializare intensă (o nuntă, un eveniment de networking)?",
            "Energy Drain, Introversion", 
            1, 
            [
                ("A) Epuizat total. Am nevoie să mă retrag imediat.", 0), 
                ("B) Obosit, dar a fost ok.", 30), 
                ("C) Încă am energie, dar m-aș duce acasă.", 70), 
                ("D) Energizat! Aș mai sta încă pe atât.", 100)
            ]
        ),
        (
            "Ce părere ai despre 'small talk' (discuții mărunte despre vreme, trafic) cu necunoscuți?",
            "Communication, Social Skills", 
            1, 
            [
                ("A) Le urăsc. Le evit cu orice preț.", 0), 
                ("B) Le tolerez dacă e nevoie de politețe.", 30), 
                ("C) Îmi plac, e un mod ușor de a conecta.", 70), 
                ("D) Le ador! Vorbesc cu oricine, oriunde.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Mediu de Lucru/Prieteni) ---
        (
            "La locul de muncă, ce tip de mediu preferi?",
            "Work Environment, Open Space", 
            2, 
            [
                ("A) Un birou privat, liniște deplină, ușa închisă.", 0), 
                ("B) Un birou mic împărțit cu 1-2 colegi liniștiți.", 30), 
                ("C) Un spațiu comun, dar nu foarte gălăgios.", 70), 
                ("D) Open space, agitație, brainstorming constant.", 100)
            ]
        ),
        (
            "Când mergi la o petrecere unde nu cunoști multă lume, ce faci?",
            "Party, Strangers, Mingling", 
            2, 
            [
                ("A) Stau într-un colț, pe telefon, sau plec repede.", 0), 
                ("B) Mă țin scai de singura persoană pe care o cunosc.", 30), 
                ("C) Mă prezint la câțiva oameni noi.", 70), 
                ("D) Mă plimb prin sală și fac cunoștință cu toată lumea.", 100)
            ]
        ),
        (
            "Câți prieteni apropiați ai spune că ai?",
            "Friendship, Social Circle", 
            2, 
            [
                ("A) 1 sau 2, și îmi este suficient.", 0), 
                ("B) Un grup mic și stabil (3-5).", 30), 
                ("C) Un grup destul de mare.", 70), 
                ("D) Zeci. Cunosc pe toată lumea și toată lumea mă știe.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Izolare Extremă vs Dependență de Grup) ---
        (
            "Cât de mult poți rezista fără să vorbești cu nimeni (nici telefon, nici mesaje) înainte să te simți singur?",
            "Solitude Tolerance, Isolation", 
            3, 
            [
                ("A) Săptămâni întregi. Iubesc singurătatea.", 0), 
                ("B) Câteva zile sunt binevenite.", 30), 
                ("C) O zi, maxim două.", 70), 
                ("D) Câteva ore. Simt nevoia să contactez pe cineva imediat.", 100)
            ]
        ),
        (
            "Îți place să lucrezi în echipă sau preferi proiectele individuale?",
            "Teamwork, Collaboration", 
            3, 
            [
                ("A) Individual. Ceilalți mă încetinesc sau mă distrag.", 0), 
                ("B) Prefer singur, dar colaborez la nevoie.", 30), 
                ("C) Îmi place echipa, e mai dinamic.", 70), 
                ("D) Doar în echipă. Nu îmi place să lucrez izolat.", 100)
            ]
        ),
        (
            "Dacă sună soneria la ușă neașteptat, care e prima reacție?",
            "Privacy, Unexpected Guests", 
            3, 
            [
                ("A) Mă prefac că nu sunt acasă. Nu vreau musafiri.", 0), 
                ("B) Verific pe vizor cu suspiciune.", 30), 
                ("C) Sunt curios cine e.", 70), 
                ("D) Deschid imediat, poate e cineva în vizită!", 100)
            ]
        ),
        (
            "Te consideri o persoană 'de casă' sau 'de lume'?",
            "Lifestyle, Going Out", 
            3, 
            [
                ("A) De casă, 100%. Casa e sanctuarul meu.", 0), 
                ("B) Mai mult de casă, ies rar.", 30), 
                ("C) Îmi place să ies regulat.", 70), 
                ("D) De lume. Nu suport să stau în casă, trebuie să se întâmple ceva.", 100)
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