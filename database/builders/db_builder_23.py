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
AXIS_ID = 23
AXIS_NAME = "Încredere în Oameni"
# Pol Stânga (0): Cinic / Suspicios / Vigilent
# Pol Dreapta (100): Încrezător / Deschis / Naiv

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
    # Punctaj: 0 = Cinic (Suspicios), 100 = Încrezător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Străini/General) ---
        (
            "Când cunoști o persoană nouă, care este atitudinea ta implicită?",
            "First Impressions, Strangers, Default Trust", 
            1, 
            [
                ("A) Sunt precaut. Încrederea se câștigă greu.", 0), 
                ("B) Observ și analizez înainte să mă deschid.", 30), 
                ("C) Sunt deschis, îi acord prezumția de bună-credință.", 70), 
                ("D) Am încredere din start. Un străin e un prieten pe care nu-l cunosc.", 100)
            ]
        ),
        (
            "Dacă un coleg îți face un favor nesolicitat (ex: îți aduce o cafea), ce gândești?",
            "Hidden Motives, Cynicism, Work", 
            1, 
            [
                ("A) 'Ce vrea de la mine? Nimic nu e gratis'.", 0), 
                ("B) Mă întreb care e ocazia.", 30), 
                ("C) Mă bucur și îi mulțumesc.", 70), 
                ("D) Ce gest drăguț! Oamenii sunt amabili.", 100)
            ]
        ),
        (
            "Cât de confortabil te simți să împrumuți obiecte personale (cărți, haine, unelte) prietenilor?",
            "Lending, Possessions, Trust", 
            1, 
            [
                ("A) Deloc. De obicei nu le mai primesc înapoi sau le strică.", 0), 
                ("B) Doar celor foarte apropiați și cu rețineri.", 30), 
                ("C) Le împrumut, dar țin evidența.", 70), 
                ("D) Sigur, le dau cu drag. Nu sunt atașat de lucruri.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Delegație/Securitate) ---
        (
            "Lași laptopul sau telefonul nesupravegheat pe masă la o cafenea cât mergi la baie?",
            "Safety, Risk, Theft", 
            2, 
            [
                ("A) Niciodată. Ar dispărea în 3 secunde.", 0), 
                ("B) Rog pe cineva să se uite, dar mă grăbesc.", 30), 
                ("C) Îl las dacă e lume civilizată în jur.", 70), 
                ("D) Da, fără griji. Majoritatea oamenilor sunt cinstiți.", 100)
            ]
        ),
        (
            "Când trebuie să delegi o sarcină importantă altcuiva, cum te simți?",
            "Control, Micromanagement, Delegation", 
            2, 
            [
                ("A) Foarte stresat. Prefer să o fac eu ca să iasă bine.", 0), 
                ("B) Îl verific des pe parcurs.", 30), 
                ("C) Îi explic clar și aștept rezultatul.", 70), 
                ("D) Am încredere totală că se va descurca.", 100)
            ]
        ),
        (
            "Dacă cineva îți spune un secret despre altcineva, ce presupui despre propriile tale secrete?",
            "Gossip, Integrity, Paranoia", 
            2, 
            [
                ("A) Că sigur mă bârfește și pe mine. Oamenii sunt falși.", 0), 
                ("B) Devin mai atent la ce îi spun.", 30), 
                ("C) Sper că pe ale mele le ține.", 70), 
                ("D) Nu fac legătura. Am încredere în discreția lui.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Cinism / Paranoia / Micromanagement) ---
        (
            "Care este viziunea ta fundamentală asupra naturii umane?",
            "Worldview, Philosophy, Cynicism", 
            3, 
            [
                ("A) Oamenii sunt egoiști și ar face orice pentru propriul interes.", 0), 
                ("B) Majoritatea își urmăresc interesul, trebuie să fii atent.", 30), 
                ("C) Oamenii sunt în general decenți.", 70), 
                ("D) Oamenii sunt buni, iubitori și cooperanți.", 100)
            ]
        ),
        (
            "Dacă partenerul tău primește un mesaj târziu în noapte, simți nevoia să verifici cine e?",
            "Jealousy, Privacy, Relationship Trust", 
            3, 
            [
                ("A) Da, verific telefonul când nu e atent. Nu am încredere oarbă.", 0), 
                ("B) Îl întreb direct cine e, cu suspiciune.", 20), 
                ("C) Sunt curios, dar nu verific.", 70), 
                ("D) Nu. Am încredere totală în partener.", 100)
            ]
        ),
        (
            "Când semnezi un contract, citești termenii și condițiile?",
            "Legal, Prudence, Formal Trust", 
            3, 
            [
                ("A) Citesc fiecare cuvânt mic. Vor să mă păcălească sigur.", 0), 
                ("B) Citesc atent clauzele principale.", 30), 
                ("C) Arunc o privire rapidă.", 70), 
                ("D) Semnez pe încredere dacă ne-am înțeles verbal.", 100)
            ]
        ),
        (
            "Ai fost vreodată înșelat (scam, împrumut nereturnat) pentru că ai avut prea multă încredere?",
            "History, Gullibility, Naivety", 
            3, 
            [
                ("A) Nu, sunt prea vigilent pentru asta.", 0), 
                ("B) O dată, demult. Am învățat lecția.", 30), 
                ("C) De câteva ori.", 60), 
                ("D) Destul de des. Mă las convins ușor de povești triste.", 100)
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