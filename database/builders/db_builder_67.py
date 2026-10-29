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
AXIS_ID = 67
AXIS_NAME = "Exprimare Emoțională"
# Pol Stânga (0): Închis / Poker Face / Rezervat
# Pol Dreapta (100): Expresiv / Deschis / Expansiv

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
    # Punctaj: 0 = Închis, 100 = Expresiv
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Vizibilitate) ---
        (
            "Oamenii își dau seama ușor ce simți (dacă ești bucuros sau supărat) doar privindu-ți fața?",
            "Body Language, Visibility, Facial Expression", 
            1, 
            [
                ("A) Nu. Am o față imobilă ('Poker Face').", 0), 
                ("B) Doar cei foarte apropiați.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Da. Sunt ca o carte deschisă, nu pot ascunde nimic.", 100)
            ]
        ),
        (
            "Cât de des vorbești despre sentimentele tale cu prietenii sau familia?",
            "Communication, Sharing, Vulnerability", 
            1, 
            [
                ("A) Foarte rar sau niciodată. Le țin pentru mine.", 0), 
                ("B) Doar dacă am o problemă gravă.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Tot timpul. Îmi place să împărtășesc ce simt.", 100)
            ]
        ),
        (
            "Când ești entuziasmat de o veste bună, cum reacționezi?",
            "Positive Emotion, Reaction, Behavior", 
            1, 
            [
                ("A) Zâmbesc discret sau rămân calm.", 0), 
                ("B) Spun 'ce bine' pe un ton normal.", 30), 
                ("C) Râd și vorbesc mai repede.", 70), 
                ("D) Sar în sus de bucurie, strig, îmbrățișez pe cineva.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Negativ / Gesturi) ---
        (
            "Dacă ești supărat pe partener sau pe un prieten, îi spui direct ce simți sau te retragi în tăcere?",
            "Conflict, Communication Style, Silent Treatment", 
            2, 
            [
                ("A) Mă retrag și tac ('Silent Treatment').", 0), 
                ("B) Aștept să îmi treacă înainte să vorbesc.", 30), 
                ("C) Îi spun că sunt supărat.", 70), 
                ("D) Îmi vărs oful imediat, verbalizez tot.", 100)
            ]
        ),
        (
            "Cât de mult gesticulezi atunci când vorbești?",
            "Non-verbal, Gestures, Energy", 
            2, 
            [
                ("A) Deloc. Stau nemișcat.", 0), 
                ("B) Puțin, pentru accentuare.", 30), 
                ("C) Destul de mult.", 60), 
                ("D) Foarte mult. Vorbesc cu tot corpul.", 100)
            ]
        ),
        (
            "Cât de greu îți este să faci complimente emoționale sau declarații de afecțiune (ex: 'Te iubesc', 'Însemni mult pentru mine')?",
            "Affection, Verbalizing", 
            2, 
            [
                ("A) Foarte greu. Mi se blochează cuvintele în gât.", 0), 
                ("B) Le spun rar, la ocazii speciale.", 30), 
                ("C) Le spun când simt nevoia.", 70), 
                ("D) Foarte ușor. Le spun des celor dragi.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Alexitimie / Autism / Histrionic) ---
        (
            "Poți să îți păstrezi calmul aparent chiar dacă fierbi pe interior, astfel încât nimeni să nu bănuiască nimic?",
            "Emotional Control, Suppression, Masking", 
            3, 
            [
                ("A) Da, perfect. Sunt un maestru al disimulării.", 0), 
                ("B) De cele mai multe ori da.", 30), 
                ("C) Îmi tremură vocea sau mă înroșesc.", 70), 
                ("D) Nu. Emoțiile 'dau pe afară' instantaneu.", 100)
            ]
        ),
        (
            "Ai plâns vreodată de față cu alți oameni (colegi, cunoștințe) sau ți se pare inacceptabil?",
            "Crying, Social Norms, Vulnerability", 
            3, 
            [
                ("A) Niciodată. Aș intra în pământ de rușine.", 0), 
                ("B) M-am abținut cu greu.", 20), 
                ("C) S-a întâmplat, sunt om.", 70), 
                ("D) Da, nu am nicio problemă să plâng dacă sunt trist.", 100)
            ]
        ),
        (
            "Te consideri o persoană 'misterioasă' pe care ceilalți se chinuie să o descifreze?",
            "Self-Image, Mystery vs Transparency", 
            3, 
            [
                ("A) Da, îmi place să fiu greu de citit.", 0), 
                ("B) Sunt rezervat.", 30), 
                ("C) Sunt destul de clar.", 70), 
                ("D) Nu. 'What you see is what you get'.", 100)
            ]
        ),
        (
            "Când povestești ceva, tinzi să fii concis și sec, sau descrii și cum te-ai simțit în detaliu?",
            "Storytelling, Emotional Detail", 
            3, 
            [
                ("A) Concis. Fapte, nu sentimente.", 0), 
                ("B) Mă limitez la esențial.", 30), 
                ("C) Adaug și impresii personale.", 60), 
                ("D) Descriu tot spectrul emoțional al experienței.", 100)
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