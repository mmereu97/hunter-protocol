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
AXIS_ID = 71
AXIS_NAME = "Atașament Evitant"
# Pol Stânga (0): Conectat / Sigur / Vulnerabil
# Pol Dreapta (100): Evitant / Distant / Închis

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
    # Punctaj: 0 = Conectat, 100 = Evitant
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Intimitate/Spațiu) ---
        (
            "Cum te simți când o persoană (partener sau prieten) devine foarte dependentă emoțional de tine?",
            "Intimacy, Suffocation, Boundaries", 
            1, 
            [
                ("A) Mă simt bine să fiu de ajutor.", 0), 
                ("B) E ok, dar stabilesc limite.", 30), 
                ("C) Mă simt inconfortabil și presat.", 70), 
                ("D) Mă simt sufocat și prima reacție e să fug/mă distanțez.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să te deschizi și să vorbești despre vulnerabilitățile sau temerile tale?",
            "Vulnerability, Trust, Walls", 
            1, 
            [
                ("A) Foarte ușor cu oamenii apropiați.", 0), 
                ("B) Durează puțin până capăt încredere.", 30), 
                ("C) Evit subiectele sensibile.", 70), 
                ("D) Imposibil. Nu las pe nimeni să vadă punctele slabe.", 100)
            ]
        ),
        (
            "Preferi să rezolvi problemele singur sau să ceri ajutorul celor dragi?",
            "Independence, Reliance, Hyper-independence", 
            1, 
            [
                ("A) Cer ajutor, e normal.", 0), 
                ("B) Încerc singur, apoi cer ajutor.", 30), 
                ("C) Prefer să nu depind de nimeni.", 70), 
                ("D) Fac totul singur. A cere ajutor e un semn de slăbiciune.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Conflict/Comportament) ---
        (
            "În timpul unui conflict emoțional intens, care este reacția ta instinctivă?",
            "Conflict, Stonewalling, Fight/Flight", 
            2, 
            [
                ("A) Rămân și discut până rezolvăm.", 0), 
                ("B) Cer o pauză să mă calmez.", 30), 
                ("C) Mă închid în mine și tac.", 70), 
                ("D) Plec fizic sau ridic un zid de gheață (Stonewalling).", 100)
            ]
        ),
        (
            "Ți se pare că partenerii/prietenii vor adesea 'mai mult' de la tine decât ești dispus să oferi?",
            "Expectations, Closeness, Relationship", 
            2, 
            [
                ("A) Nu, suntem pe aceeași lungime de undă.", 0), 
                ("B) Rar.", 20), 
                ("C) Da, adesea mi se reproșează că sunt rece.", 70), 
                ("D) Mereu. Oamenii sunt prea needy și cer prea multă atenție.", 100)
            ]
        ),
        (
            "Te simți mai confortabil în relații superficiale/casual decât în cele profunde și angajante?",
            "Commitment, Depth, Safety", 
            2, 
            [
                ("A) Nu, caut profunzimea.", 0), 
                ("B) Îmi plac ambele.", 30), 
                ("C) Cele superficiale sunt mai puțin stresante.", 70), 
                ("D) Da. Angajamentele profunde sunt o capcană.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Schizoid / Narcisism / Alexitimie) ---
        (
            "Ai simțit vreodată o ușurare imensă imediat după ce ai terminat o relație, în loc de tristețe?",
            "Breakup, Relief, Deactivation", 
            3, 
            [
                ("A) Nu, despărțirile sunt dureroase.", 0), 
                ("B) Poate dacă relația era toxică.", 30), 
                ("C) Da, m-am simțit eliberat.", 70), 
                ("D) Da, libertatea mea e mai importantă decât orice relație.", 100)
            ]
        ),
        (
            "Crezi că a te baza pe alți oameni este o greșeală care duce inevitabil la dezamăgire?",
            "Trust, Cynicism, Philosophy", 
            3, 
            [
                ("A) Nu, interdependența e sănătoasă.", 0), 
                ("B) Trebuie să alegi oamenii cu grijă.", 30), 
                ("C) De cele mai multe ori, da.", 60), 
                ("D) Absolut. Singura persoană pe care te poți baza ești tu însuți.", 100)
            ]
        ),
        (
            "Când cineva încearcă să se apropie foarte mult de tine emoțional, tinzi să îi găsești defecte pentru a crea distanță?",
            "Deactivation Strategy, Sabotage", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Nu conștient.", 20), 
                ("C) Uneori mă focusez pe negativ.", 70), 
                ("D) Da. Imediat ce devine serios, 'mă răcesc' și îi văd doar defectele.", 100)
            ]
        ),
        (
            "Îți reprimi sentimentele de tristețe sau dorința de afecțiune până când ajungi să nu le mai simți?",
            "Suppression, Numbness, Emotional Needs", 
            3, 
            [
                ("A) Nu, le exprim.", 0), 
                ("B) Le gestionez privat.", 30), 
                ("C) Încerc să nu le dau importanță.", 70), 
                ("D) Da. Am învățat să nu am nevoie de nimeni și de nimic.", 100)
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