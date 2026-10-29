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
AXIS_ID = 109
AXIS_NAME = "Mobilitate (Stil de Viață)"
# Pol Stânga (0): Sedentar / Stabil / Casnic / Birou Fix
# Pol Dreapta (100): Nomad / Dinamic / Călător / Teren

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
    # Punctaj: 0 = Stabil (Sedentar), 100 = Mobil (Nomad)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Job/Casă) ---
        (
            "Cum arată jobul ideal pentru tine din punct de vedere al locației?",
            "Career, Location, Preferences", 
            1, 
            [
                ("A) Același birou/locație zilnic. Îmi place rutina.", 0), 
                ("B) Hibrid, dar majoritar de acasă/birou.", 30), 
                ("C) Muncă de teren sau vizite la clienți.", 70), 
                ("D) Digital Nomad sau delegații internaționale constante.", 100)
            ]
        ),
        (
            "Cât de mult îți place să călătorești?",
            "Travel, Hobby, Lifestyle", 
            1, 
            [
                ("A) Deloc. 'Nicăieri nu-i ca acasă'.", 0), 
                ("B) O dată pe an, în concediu, e suficient.", 30), 
                ("C) Îmi plac city-break-urile frecvente.", 70), 
                ("D) Trăiesc pentru a călători. Aș sta mereu pe drumuri.", 100)
            ]
        ),
        (
            "Dacă firma îți propune o poziție care implică deplasări 50% din timp, ce zici?",
            "Work Travel, Availability", 
            1, 
            [
                ("A) Refuz. Am nevoie de stabilitate.", 0), 
                ("B) Accept doar dacă e temporar sau bine plătit.", 30), 
                ("C) Accept, sună interesant.", 70), 
                ("D) Accept entuziasmat! Urăsc să stau la birou.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Adaptabilitate/Confort) ---
        (
            "Cum te simți când dormi în alte locuri decât în patul tău (hoteluri, la prieteni)?",
            "Comfort, Adaptability, Sleep", 
            2, 
            [
                ("A) Groaznic. Nu mă odihnesc deloc.", 0), 
                ("B) Mă acomodez greu.", 30), 
                ("C) Destul de bine.", 70), 
                ("D) Perfect. Mă simt acasă oriunde îmi pun rucsacul.", 100)
            ]
        ),
        (
            "Cât de atașat ești de orașul sau cartierul în care locuiești?",
            "Roots, Stability, Attachment", 
            2, 
            [
                ("A) Foarte atașat. Aici sunt rădăcinile mele.", 0), 
                ("B) Îmi place, nu aș vrea să plec.", 30), 
                ("C) M-aș muta dacă apare o oportunitate.", 70), 
                ("D) Deloc. Sunt cetățean al lumii, azi aici, mâine acolo.", 100)
            ]
        ),
        (
            "Te deranjează să faci naveta sau să conduci mult timp?",
            "Driving, Commute, Patience", 
            2, 
            [
                ("A) Da, e timp pierdut.", 0), 
                ("B) Mă obosește dacă e zilnic.", 30), 
                ("C) Nu, ascult muzică/podcast-uri.", 70), 
                ("D) Nu, îmi place să fiu în mișcare/la volan.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Flight Risk / Instabilitate / Neliniște) ---
        (
            "Te simți 'blocat' sau sufocat dacă stai în același loc prea mult timp (Cabin Fever)?",
            "Restlessness, Boredom, Freedom", 
            3, 
            [
                ("A) Nu, mă simt în siguranță.", 0), 
                ("B) Rar, poate după o iarnă lungă.", 30), 
                ("C) Da, am nevoie de ieșiri.", 70), 
                ("D) Da, am o nevoie fizică de a evada și de a schimba peisajul.", 100)
            ]
        ),
        (
            "Ai putea trăi fericit într-o rulotă, călătorind constant, fără o adresă fixă?",
            "Van Life, Minimalism, Adventure", 
            3, 
            [
                ("A) Niciodată. Am nevoie de confort și stabilitate.", 0), 
                ("B) Poate o săptămână de vacanță.", 20), 
                ("C) M-ar tenta experiența pentru un an.", 70), 
                ("D) Da, este visul meu!", 100)
            ]
        ),
        (
            "Când te muți într-un loc nou, cât de repede te plictisești și vrei altceva?",
            "Novelty Seeking, Stability", 
            3, 
            [
                ("A) Nu mă plictisesc, vreau să rămân.", 0), 
                ("B) Durează ani de zile.", 30), 
                ("C) După 1-2 ani simt nevoia de schimbare.", 70), 
                ("D) Foarte repede. Noutatea dispare în câteva luni.", 100)
            ]
        ),
        (
            "Ești dispus să îți sacrifici viața socială stabilă și prietenii vechi pentru a explora locuri noi?",
            "Sacrifice, Priorities, Detachment", 
            3, 
            [
                ("A) Nu, relațiile sunt mai importante.", 0), 
                ("B) Aș ezita mult.", 30), 
                ("C) Aș păstra legătura online.", 70), 
                ("D) Da. Oamenii noi sunt peste tot, experiențele contează.", 100)
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