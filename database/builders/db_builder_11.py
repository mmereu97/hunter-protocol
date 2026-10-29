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
AXIS_ID = 11
AXIS_NAME = "Impulsivitate"
# Pol Stânga (0): Controlat / Deliberat / Disciplinat
# Pol Dreapta (100): Impulsiv / Reactiv / Grăbit

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
    # Punctaj: 0 = Controlat, 100 = Impulsiv
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Cumpărături/Discuții) ---
        (
            "Când vezi ceva ce îți place foarte mult în magazin, dar e scump, ce faci?",
            "Shopping, Money, Gratification", 
            1, 
            [
                ("A) Mă duc acasă și mă gândesc 24h dacă am nevoie.", 0), 
                ("B) Analizez bugetul înainte să decid.", 30), 
                ("C) De obicei îl cumpăr, mă descurc eu cu banii.", 70), 
                ("D) Îl iau instant. O viață avem!", 100)
            ]
        ),
        (
            "În timpul unei discuții aprinse, ți se întâmplă să întrerupi interlocutorul sau să vorbești peste el?",
            "Communication, Patience, Interrupting", 
            1, 
            [
                ("A) Niciodată. Ascult până la capăt.", 0), 
                ("B) Rar, doar dacă spune ceva absurd.", 30), 
                ("C) Da, dacă am o idee bună, o zic imediat.", 70), 
                ("D) Des. Îmi vine greu să îmi aștept rândul.", 100)
            ]
        ),
        (
            "Când trebuie să iei o decizie rapidă, preferi să analizezi toate datele sau să mergi pe instinct?",
            "Decision Making, Gut Feeling", 
            1, 
            [
                ("A) Analizez tot, chiar dacă pierd timp.", 0), 
                ("B) Verific rapid punctele cheie.", 30), 
                ("C) Merg pe instinct de cele mai multe ori.", 70), 
                ("D) Acționez pe loc, nu am răbdare cu detaliile.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Tentații/Trafic/Mâncare) ---
        (
            "Cât de greu îți este să te abții de la mâncăruri nesănătoase, dulciuri sau alte mici vicii dacă le ai în față?",
            "Diet, Self-Control, Cravings", 
            2, 
            [
                ("A) Foarte ușor. Am o voință de fier.", 0), 
                ("B) Rezist dacă mi-am propus.", 30), 
                ("C) E greu, de multe ori cedez.", 70), 
                ("D) Imposibil. Dacă e acolo, îl consum.", 100)
            ]
        ),
        (
            "Ești în trafic sau la o coadă care nu se mișcă. Cum reacționezi?",
            "Patience, Traffic, Anger", 
            2, 
            [
                ("A) Aștept calm, ascult muzică.", 0), 
                ("B) Mă uit la ceas, dar stau liniștit.", 30), 
                ("C) Mă enervez și încep să mă agit.", 70), 
                ("D) Claxonez, înjur sau îmi vine să las totul baltă și să plec.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să spui ceva regretabil 'la nervi' și să îți pară rău imediat după?",
            "Regret, Anger Management, Verbal", 
            2, 
            [
                ("A) Nu, îmi controlez mereu cuvintele.", 0), 
                ("B) Foarte rar.", 20), 
                ("C) Da, mi se întâmplă uneori.", 70), 
                ("D) Da, 'gura o ia înaintea minții' frecvent.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Hărțuire / Agresivitate / Adicție) ---
        (
            "Dacă cineva te provoacă sau te jignește direct, care e prima reacție?",
            "Conflict, Fight or Flight, Aggression", 
            3, 
            [
                ("A) Ignor și plec. Nu merită efortul.", 0), 
                ("B) Îl întreb calm care e problema.", 30), 
                ("C) Îl jignesc și eu înapoi.", 70), 
                ("D) Reacționez fizic sau urlu. Nu permit așa ceva.", 100)
            ]
        ),
        (
            "Te plictisești repede de proiecte sau hobby-uri și le abandonezi pentru ceva nou și mai interesant?",
            "Consistency, Boredom, Novelty", 
            3, 
            [
                ("A) Nu, termin mereu ce încep.", 0), 
                ("B) Uneori, dacă chiar nu îmi place.", 30), 
                ("C) Da, am multe proiecte începute și neterminate.", 70), 
                ("D) Da, am nevoie constantă de noutate, rutina mă omoară.", 100)
            ]
        ),
        (
            "Ai tendința de a face lucruri riscante (viteză, pariuri, aventuri) doar pentru senzația de moment?",
            "Risk Taking, Thrill, Adrenaline", 
            3, 
            [
                ("A) Nu, sunt o persoană prudentă.", 0), 
                ("B) Iau riscuri calculate.", 30), 
                ("C) Uneori, îmi place adrenalina.", 70), 
                ("D) Da, trăiesc pentru moment, nu mă gândesc la consecințe.", 100)
            ]
        ),
        (
            "Cât de des acționezi sub impulsul momentului, fără să te gândești la consecințele pe termen lung?",
            "Planning, Consequences, Lifestyle", 
            3, 
            [
                ("A) Niciodată. Planific totul.", 0), 
                ("B) Rar, la lucruri mici.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Aproape mereu. Viitorul e departe, prezentul contează.", 100)
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