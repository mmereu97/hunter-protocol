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
AXIS_ID = 7
AXIS_NAME = "Dependență Emoțională"
# Pol Stânga (0): Independent / Solo / Autonom
# Pol Dreapta (100): Dependent / Tribal / Nevoie de Suport

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
    # Punctaj: 0 = Independent, 100 = Dependent
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Muncă) ---
        (
            "Când te confrunți cu o problemă personală dificilă, care este primul impuls?",
            "Problem Solving, Coping, Autonomy", 
            1, 
            [
                ("A) O analizez singur și o rezolv. Nu implic pe alții.", 0), 
                ("B) Încerc singur, dar cer sfaturi dacă mă blochez.", 30), 
                ("C) Sun imediat un prieten sau un membru al familiei.", 70), 
                ("D) Mă simt pierdut fără cineva care să îmi spună ce să fac.", 100)
            ]
        ),
        (
            "La locul de muncă, cât de des ai nevoie de feedback sau validare din partea șefului pentru a ști că faci bine?",
            "Work, Validation, Confidence", 
            1, 
            [
                ("A) Rar. Știu când fac treabă bună.", 0), 
                ("B) La finalul proiectelor majore.", 30), 
                ("C) Destul de des, ca să fiu sigur.", 70), 
                ("D) Constant. Am nevoie de reasigurare zilnică.", 100)
            ]
        ),
        (
            "Cum te simți când trebuie să petreci un weekend întreg complet singur, fără contact social?",
            "Solitude, Social Battery, Independence", 
            1, 
            [
                ("A) Excelent. Îmi încarc bateriile.", 0), 
                ("B) E ok, îmi găsesc de lucru.", 30), 
                ("C) Mă plictisesc și devin neliniștit.", 70), 
                ("D) Mă simt deprimat și abandonat.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Decizii/Relații) ---
        (
            "Trebuie să iei o decizie majoră (ex: cumpărarea unei mașini sau schimbarea jobului). Cum procedezi?",
            "Decision Making, Reliance", 
            2, 
            [
                ("A) Decid singur, e viața mea.", 0), 
                ("B) Mă informez, apoi decid.", 30), 
                ("C) Mă consult cu toți apropiații înainte.", 70), 
                ("D) Nu pot decide până nu îmi spune cineva de încredere ce să fac.", 100)
            ]
        ),
        (
            "Dacă partenerul sau cel mai bun prieten pleacă din oraș pentru o săptămână, cum te afectează?",
            "Attachment, Separation, Mood", 
            2, 
            [
                ("A) Deloc. Viața merge înainte.", 0), 
                ("B) Îmi e dor, dar funcționez normal.", 30), 
                ("C) Mă simt puțin gol și trist.", 70), 
                ("D) Sunt anxios și mă simt incapabil să mă descurc singur.", 100)
            ]
        ),
        (
            "Cât de mult contează pentru tine să faci parte dintr-un grup sau o comunitate unită?",
            "Belonging, Tribalism, Identity", 
            2, 
            [
                ("A) Puțin. Sunt un lup singuratic.", 0), 
                ("B) E plăcut, dar păstrez distanța.", 30), 
                ("C) Important. Îmi place sentimentul de apartenență.", 70), 
                ("D) Esențial. Nu sunt nimic fără 'tribul' meu.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Loafing / Atașament Anxios) ---
        (
            "Ai tendința de a te plânge celorlalți despre problemele tale în speranța că ei le vor rezolva pentru tine?",
            "Victimization, Help Seeking, Passive", 
            3, 
            [
                ("A) Niciodată. Îmi rezolv singur problemele.", 0), 
                ("B) Mă plâng doar ca să mă descarc.", 30), 
                ("C) Uneori, sper la un ajutor concret.", 70), 
                ("D) Da, de multe ori mă simt neajutorat și aștept salvarea.", 100)
            ]
        ),
        (
            "Ți s-a spus vreodată că ești 'lipicios' (clingy) sau prea solicitant emoțional în relații?",
            "Relationships, Boundaries, Clinginess", 
            3, 
            [
                ("A) Nu, din contră, sunt considerat distant.", 0), 
                ("B) Nu cred.", 20), 
                ("C) Poate, în momente de stres mare.", 70), 
                ("D) Da, am pierdut relații din cauza asta.", 100)
            ]
        ),
        (
            "Cât de mult îți este frică să fii abandonat sau respins de cei apropiați?",
            "Fear of Abandonment, Insecurity", 
            3, 
            [
                ("A) Nu mă preocupă. Oamenii vin și pleacă.", 0), 
                ("B) Nu e o frică activă.", 30), 
                ("C) Mă îngrijorează uneori.", 70), 
                ("D) Este o groază constantă care îmi dictează acțiunile.", 100)
            ]
        ),
        (
            "Simți că identitatea ta este definită de persoanele cu care ești (ex: 'sunt soțul lui X', 'sunt angajat la Y')?",
            "Identity Fusion, Self-Worth", 
            3, 
            [
                ("A) Nu. Eu sunt eu, indiferent de context.", 0), 
                ("B) Într-o mică măsură, rolurile contează.", 30), 
                ("C) Da, relațiile mele mă definesc mult.", 70), 
                ("D) Total. Fără ei, nu știu cine sunt.", 100)
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