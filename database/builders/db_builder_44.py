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
AXIS_ID = 44
AXIS_NAME = "Sensibilitate Artistică"
# Pol Stânga (0): Dur / Realist / Pragmatic (Tough-minded)
# Pol Dreapta (100): Rafinat / Sensibil / Intuitiv (Tender-minded)

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
    # Punctaj: 0 = Dur/Realist, 100 = Sensibil/Rafinat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe/Stil) ---
        (
            "Ce fel de filme sau cărți preferi în general?",
            "Preferences, Media, Tough vs Tender", 
            1, 
            [
                ("A) Acțiune, război, documentare tehnice. Lucruri concrete.", 0), 
                ("B) Comedii sau thrillere realiste.", 30), 
                ("C) Drame sau povești cu profunzime psihologică.", 70), 
                ("D) Filme de artă, poezie, povești romantice sau fantezie.", 100)
            ]
        ),
        (
            "Când iei o decizie, te bazezi mai mult pe fapte reci sau pe intuiție/sentiment?",
            "Decision Making, Logic vs Intuition", 
            1, 
            [
                ("A) Exclusiv pe fapte și logică. Intuiția e o prostie.", 0), 
                ("B) Încerc să fiu obiectiv.", 30), 
                ("C) Țin cont și de cum se 'simte' decizia.", 70), 
                ("D) Mă bazez total pe instinct și pe ce simt în acel moment.", 100)
            ]
        ),
        (
            "Cum te raportezi la oamenii care sunt foarte emotivi sau plâng ușor?",
            "Empathy, Judgment, Tolerance", 
            1, 
            [
                ("A) Mă irită. Îi consider slabi sau imaturi.", 0), 
                ("B) Nu știu cum să reacționez.", 30), 
                ("C) Îi înțeleg și încerc să fiu blând.", 70), 
                ("D) Empatizez imediat, adesea plâng și eu cu ei.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Mediu/Rafinament) ---
        (
            "Te deranjează vulgaritatea, mizeria sau mediile 'dure' (șantiere, baruri gălăgioase)?",
            "Environment, Refinement, Sensitivity", 
            2, 
            [
                ("A) Nu. Sunt obișnuit, e viața reală.", 0), 
                ("B) Prefer curățenia, dar mă adaptez.", 30), 
                ("C) Evit locurile neplăcute.", 70), 
                ("D) Da, mă afectează fizic. Am nevoie de frumos și armonie.", 100)
            ]
        ),
        (
            "Consideri că 'soft skills' (empatia, comunicarea) sunt la fel de importante ca abilitățile tehnice la muncă?",
            "Work Values, Hard vs Soft Skills", 
            2, 
            [
                ("A) Nu. Dacă știi meserie, restul sunt povești.", 0), 
                ("B) Sunt un bonus.", 30), 
                ("C) Sunt importante pentru echipă.", 70), 
                ("D) Sunt esențiale. Climatul emoțional contează cel mai mult.", 100)
            ]
        ),
        (
            "Când redecorezi o cameră, ce primează: utilitatea sau atmosfera?",
            "Aesthetics, Practicality, Atmosphere", 
            2, 
            [
                ("A) Utilitatea strictă. Să fie funcțional și durabil.", 0), 
                ("B) Să fie curat și practic.", 30), 
                ("C) Încerc să o fac primitoare.", 70), 
                ("D) Atmosfera, culorile, lumina. Trebuie să exprime o emoție.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Narcisism / Psihopatie vs Nevrotism) ---
        (
            "Te consideri o persoană 'cu picioarele pe pământ' sau 'cu capul în nori'?",
            "Self-Image, Groundedness", 
            3, 
            [
                ("A) Foarte realist. Nu-mi plac visătorii.", 0), 
                ("B) Pragmatic.", 30), 
                ("C) Am momente de visare.", 70), 
                ("D) Cu capul în nori. Imaginația e refugiul meu.", 100)
            ]
        ),
        (
            "Cât de des ești mișcat profund de o piesă muzicală sau de un apus de soare?",
            "Aesthetic Sensitivity, Emotion", 
            3, 
            [
                ("A) Niciodată. Sunt doar sunete sau fenomene optice.", 0), 
                ("B) Rar, dacă e ceva spectaculos.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Frecvent. Simt o conexiune profundă cu arta/natura.", 100)
            ]
        ),
        (
            "Îți place să analizezi 'de ce' se comportă oamenii într-un fel, căutând motivații psihologice ascunse?",
            "Psychology, Analysis, Nuance", 
            3, 
            [
                ("A) Nu. Oamenii sunt simpli, faptele vorbesc.", 0), 
                ("B) Uneori, dacă e cineva apropiat.", 30), 
                ("C) Da, îmi place psihologia.", 70), 
                ("D) Da, analizez constant nuanțele și subtextul emoțional.", 100)
            ]
        ),
        (
            "Dacă trebuie să dai o veste proastă, o spui direct sau o 'împachetezi'?",
            "Communication, Tact, Bluntness", 
            3, 
            [
                ("A) Direct, scurt și la obiect. Ca să terminăm repede.", 0), 
                ("B) Politicos, dar clar.", 30), 
                ("C) Cu grijă, pregătesc terenul.", 70), 
                ("D) Cu foarte mult tact, ocolind subiectul ca să nu rănesc.", 100)
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