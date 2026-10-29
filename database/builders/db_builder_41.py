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
AXIS_ID = 41
AXIS_NAME = "Diplomație / Secretomanie"
# Pol Stânga (0): Deschis / Naiv / Direct
# Pol Dreapta (100): Calculat / Secretos / Diplomat

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
    # Punctaj: 0 = Naiv/Deschis, 100 = Calculat/Secretos
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Deschidere Generală) ---
        (
            "Cât de multe știu colegii sau cunoștințele tale despre viața ta personală și problemele tale?",
            "Privacy, Sharing, Boundaries", 
            1, 
            [
                ("A) Totul. Sunt o carte deschisă.", 0), 
                ("B) Știu destul de multe, sunt prietenos.", 30), 
                ("C) Știu doar strictul necesar.", 70), 
                ("D) Nimic. Viața mea privată este un mister total pentru ei.", 100)
            ]
        ),
        (
            "Dacă cineva îți pune o întrebare incomodă sau indiscretă, cum reacționezi?",
            "Social Skills, Evasion, Honesty", 
            1, 
            [
                ("A) Răspund sincer, nu am nimic de ascuns.", 0), 
                ("B) Mă fâstâcesc, dar răspund.", 30), 
                ("C) Schimb subiectul cu tact.", 70), 
                ("D) Îi întorc întrebarea sau dau un răspuns vag care nu zice nimic.", 100)
            ]
        ),
        (
            "Când ai o idee nouă sau un plan de viitor, când îl anunți celorlalți?",
            "Planning, Secrecy, Sharing", 
            1, 
            [
                ("A) Imediat, de entuziasm.", 0), 
                ("B) Pe parcurs, când prinde contur.", 30), 
                ("C) Doar când sunt sigur că va reuși.", 70), 
                ("D) După ce l-am realizat deja. Nu vorbesc înainte.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Strategie Socială) ---
        (
            "Te consideri o persoană 'diplomată', care știe să spună lucrurile astfel încât să cadă mereu în picioare?",
            "Diplomacy, Tact, Manipulation", 
            2, 
            [
                ("A) Nu, sunt direct și uneori brutal.", 0), 
                ("B) Încerc să fiu politicos.", 30), 
                ("C) Da, știu să ambalez adevărul.", 70), 
                ("D) Da, sunt maestru în a gestiona percepția celorlalți.", 100)
            ]
        ),
        (
            "Dacă un prieten îți cere părerea despre o ținută care nu îi stă bine, ce îi spui?",
            "White Lies, Social Grace", 
            2, 
            [
                ("A) 'Arăți oribil'. Sinceritatea e de aur.", 0), 
                ("B) Îi spun blând că nu e cea mai bună alegere.", 30), 
                ("C) Evit răspunsul direct.", 60), 
                ("D) Îi spun că arată bine. Nu câștig nimic dacă îl supăr.", 100)
            ]
        ),
        (
            "Cât de ușor pot citi oamenii pe fața ta ceea ce gândești sau simți?",
            "Poker Face, Authenticity", 
            2, 
            [
                ("A) Foarte ușor. Nu pot ascunde nimic.", 0), 
                ("B) Destul de ușor.", 30), 
                ("C) Pot să îmi controlez expresiile.", 70), 
                ("D) Imposibil. Am o față de poker perfectă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Machiavelism / Sabotor / Paranoia) ---
        (
            "Consideri că informația înseamnă putere și că e periculos să dezvălui prea multe despre tine?",
            "Information Control, Paranoia, Power", 
            3, 
            [
                ("A) Nu, transparența creează încredere.", 0), 
                ("B) E bine să fii prudent.", 30), 
                ("C) Da, ce spui poate fi folosit împotriva ta.", 70), 
                ("D) Absolut. Nu dau nimănui muniție împotriva mea.", 100)
            ]
        ),
        (
            "Ai tendința de a analiza 'agenda ascunsă' a oamenilor atunci când îți vorbesc?",
            "Suspicion, Analysis, Reading People", 
            3, 
            [
                ("A) Nu, iau lucrurile așa cum sunt.", 0), 
                ("B) Uneori, dacă persoana e dubioasă.", 30), 
                ("C) Da, mereu mă întreb 'de ce îmi spune asta acum?'.", 70), 
                ("D) Da. Nimic nu e întâmplător, totul e un joc de șah.", 100)
            ]
        ),
        (
            "Ești capabil să păstrezi un secret important ani de zile, chiar și față de cei apropiați?",
            "Secrecy, Trustworthiness, Isolation", 
            3, 
            [
                ("A) Nu prea, mă roade să îl spun.", 0), 
                ("B) Dacă mi se cere, da.", 30), 
                ("C) Da, sunt un mormânt.", 70), 
                ("D) Da. Am secrete pe care nu le voi spune nimănui, niciodată.", 100)
            ]
        ),
        (
            "Joci roluri diferite în funcție de persoana cu care ești (cameleonism social) pentru a te integra sau a obține ceva?",
            "Social Chameleon, Identity, Strategy", 
            3, 
            [
                ("A) Nu, sunt eu însumi peste tot.", 0), 
                ("B) Mă adaptez puțin contextului.", 30), 
                ("C) Da, îmi ajustez personalitatea.", 70), 
                ("D) Da, am măști diferite pentru fiecare grup. Nimeni nu mă cunoaște pe cel real.", 100)
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