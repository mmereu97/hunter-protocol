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
AXIS_ID = 42
AXIS_NAME = "Dominanță Agresivă"
# Pol Stânga (0): Pasiv / Submisiv / Ușor de condus
# Pol Dreapta (100): Autoritar / Șef / Dominator

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
    # Punctaj: 0 = Pasiv, 100 = Dominator
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Grupuri/Decizii) ---
        (
            "Într-un grup de prieteni sau colegi, cine ia de obicei decizia finală (unde mergeți, ce faceți)?",
            "Group Dynamics, Leadership, Control", 
            1, 
            [
                ("A) Ceilalți. Eu mă adaptez.", 0), 
                ("B) Discutăm și votăm.", 30), 
                ("C) Îmi spun părerea apăsat.", 70), 
                ("D) Eu. De obicei preiau comanda și decid pentru toți.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să câștigi o dispută verbală?",
            "Conflict, Ego, Winning", 
            1, 
            [
                ("A) Deloc. Prefer liniștea.", 0), 
                ("B) Nu e un scop în sine.", 30), 
                ("C) Important, dacă am dreptate.", 70), 
                ("D) Foarte important. Nu suport să fiu învins verbal.", 100)
            ]
        ),
        (
            "Dacă cineva greșește sau este lent, îi spui în față pe un ton ferm?",
            "Feedback, Directness, Aggression", 
            1, 
            [
                ("A) Nu, nu vreau să îl supăr.", 0), 
                ("B) Îl ajut sau îi spun blând.", 30), 
                ("C) Îi spun direct.", 60), 
                ("D) Da, imediat. Trebuie scuturat ca să se trezească.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Autoritate/Opoziție) ---
        (
            "Cum reacționezi când cineva îți contestă autoritatea sau o decizie pe care ai luat-o?",
            "Authority, Challenge, Reaction", 
            2, 
            [
                ("A) Mă îndoiesc de mine și cedez.", 0), 
                ("B) Ascult contra-argumentele.", 30), 
                ("C) Mă irită, dar discut.", 70), 
                ("D) Îl pun la punct imediat. Nu permit insubordonarea.", 100)
            ]
        ),
        (
            "Îți place să dai ordine și să organizezi oamenii, chiar dacă nu ești oficial șeful lor?",
            "Natural Leader, Bossiness", 
            2, 
            [
                ("A) Nu, mă simt inconfortabil.", 0), 
                ("B) Doar dacă e haos total.", 30), 
                ("C) Da, îmi vine natural.", 70), 
                ("D) Da, ador să am controlul și să coordonez.", 100)
            ]
        ),
        (
            "În negocieri sau discuții, tinzi să fii cooperant sau dur?",
            "Negotiation, Style, Cooperation", 
            2, 
            [
                ("A) Cooperant, caut 'win-win'.", 0), 
                ("B) Flexibil.", 30), 
                ("C) Ferm pe poziții.", 70), 
                ("D) Dur. Vreau să obțin maximul posibil, cu orice preț.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Narcisism / Psihopatie / Agresivitate) ---
        (
            "Folosești vreodată intimidarea (privirea, tonul vocii, amenințări subtile) pentru a obține ce vrei?",
            "Intimidation, Manipulation, Fear", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Nu conștient.", 20), 
                ("C) Uneori e nevoie să arăți cine e șeful.", 70), 
                ("D) Da. Frica este un motivator excelent.", 100)
            ]
        ),
        (
            "Crezi că într-o relație (de cuplu sau profesională) trebuie să existe întotdeauna un 'șef' și un 'subaltern'?",
            "Power Dynamics, Hierarchy, Equality", 
            3, 
            [
                ("A) Nu, cred în egalitate totală.", 0), 
                ("B) Rolurile pot alterna.", 30), 
                ("C) Cineva trebuie să conducă.", 60), 
                ("D) Da. Și eu sunt acela care conduce.", 100)
            ]
        ),
        (
            "Te simți bine când observi că oamenii sunt puțin temători sau foarte reținuți în prezența ta?",
            "Respect vs Fear, Ego", 
            3, 
            [
                ("A) Nu, vreau să se simtă bine.", 0), 
                ("B) Prefer să fiu respectat, nu temut.", 30), 
                ("C) Îmi place să impun respect.", 60), 
                ("D) Da, înseamnă că îmi recunosc puterea.", 100)
            ]
        ),
        (
            "Dacă știi că ai greșit, recunoști public sau încerci să domini discuția ca să pari că ai avut dreptate?",
            "Admitting Fault, Vulnerability, Gaslighting", 
            3, 
            [
                ("A) Recunosc și îmi cer scuze.", 0), 
                ("B) Recunosc, dar explic contextul.", 30), 
                ("C) Nu recunosc deschis, schimb subiectul.", 70), 
                ("D) Nu recunosc niciodată. Slăbiciunea nu se arată.", 100)
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