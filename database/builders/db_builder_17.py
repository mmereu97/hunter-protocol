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
AXIS_ID = 17
AXIS_NAME = "Căutarea Senzațiilor"
# Pol Stânga (0): Prudent / Casnic / Evită Stimularea
# Pol Dreapta (100): Aventurier / Adrenalină / Caută Stimularea

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
    # Punctaj: 0 = Prudent, 100 = Aventurier
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Timp Liber/Preferințe) ---
        (
            "Cum arată vacanța ideală pentru tine?",
            "Travel, Lifestyle, Relaxation vs Thrill", 
            1, 
            [
                ("A) O cabană liniștită, o carte bună, zero agitație.", 0), 
                ("B) Vizitarea unui oraș, muzee, plimbări.", 30), 
                ("C) O stațiune animată, cu viață de noapte.", 70), 
                ("D) Safari, rafting, sporturi extreme, explorare sălbatică.", 100)
            ]
        ),
        (
            "Ce părere ai despre muzica tare, luminile puternice și locurile aglomerate (cluburi, concerte mari)?",
            "Sensory Stimulation, Social Environment", 
            1, 
            [
                ("A) Le evit, mă obosesc și îmi dau dureri de cap.", 0), 
                ("B) Sunt ok pentru scurt timp, la ocazii speciale.", 30), 
                ("C) Îmi plac, mă încarcă cu energie.", 70), 
                ("D) Le ador! Acolo mă simt cel mai viu.", 100)
            ]
        ),
        (
            "Cât de repede te plictisești dacă nu ai nimic 'interesant' de făcut?",
            "Boredom, Need for Stimulation", 
            1, 
            [
                ("A) Niciodată. Îmi găsesc mereu ceva liniștit de făcut.", 0), 
                ("B) Rezist destul de bine la rutină.", 30), 
                ("C) Încep să caut activitate după o zi de leneveală.", 70), 
                ("D) Foarte repede. Simt o neliniște fizică dacă nu e acțiune.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Risc/Viteză/Noutate) ---
        (
            "Îți place să conduci cu viteză mare?",
            "Driving, Speed, Risk", 
            2, 
            [
                ("A) Nu, conduc prudent și respect limitele strict.", 0), 
                ("B) Doar pe autostradă, în siguranță.", 30), 
                ("C) Da, îmi place să simt motorul.", 70), 
                ("D) Da, viteza îmi dă o stare de euforie.", 100)
            ]
        ),
        (
            "Ai încerca mâncăruri exotice foarte ciudate sau picante?",
            "Novelty, Food, Experience", 
            2, 
            [
                ("A) Nu, prefer mâncarea cu care sunt obișnuit.", 0), 
                ("B) Poate, dacă nu arată dezgustător.", 30), 
                ("C) Da, îmi place să experimentez gusturi noi.", 70), 
                ("D) Absolut, încerc orice măcar o dată!", 100)
            ]
        ),
        (
            "Ce simți când te dai într-un montagne russe (rollercoaster) sau într-un carusel rapid?",
            "Thrill, Fear vs Fun", 
            2, 
            [
                ("A) Groază și greață. Nu mă urc.", 0), 
                ("B) O ușoară teamă combinată cu distracție.", 30), 
                ("C) Îmi place, e distractiv.", 70), 
                ("D) Extaz pur! Aș sta toată ziua acolo.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Dezinhibiție / Manie / ADHD) ---
        (
            "Ai face ceva periculos (sărituri de la înălțime, explorări urbane ilegale) doar pentru fiorul momentului?",
            "Physical Danger, Recklessness", 
            3, 
            [
                ("A) Exclus. Siguranța e pe primul loc.", 0), 
                ("B) Doar în cadru organizat și asigurat.", 30), 
                ("C) M-ar tenta, depinde de riscuri.", 70), 
                ("D) Da, trăiesc pentru momentele alea de adrenalină.", 100)
            ]
        ),
        (
            "Simți nevoia constantă de schimbare (job, casă, partener, look) pentru că 'vechiul' devine insuportabil?",
            "Change, Stability, Restlessness", 
            3, 
            [
                ("A) Nu, stabilitatea îmi oferă confort.", 0), 
                ("B) Fac schimbări mici ca să nu mă plictisesc.", 30), 
                ("C) Uneori simt nevoia de un nou început.", 60), 
                ("D) Da, rutina mă omoară. Trebuie să schimb decorul des.", 100)
            ]
        ),
        (
            "Te-ai descrie ca o persoană care 'se aruncă cu capul înainte' fără să verifice apa?",
            "Impulsivity, Adventure, Planning", 
            3, 
            [
                ("A) Niciodată. Planific totul.", 0), 
                ("B) Sunt calculat în general.", 30), 
                ("C) Uneori, spontaneitatea e bună.", 70), 
                ("D) Da, cele mai bune povești așa încep.", 100)
            ]
        ),
        (
            "Îți plac jocurile de noroc sau pariurile cu mize mari?",
            "Gambling, Risk, Reward", 
            3, 
            [
                ("A) Nu, sunt o risipă de bani.", 0), 
                ("B) Joc rar, sume mici, de distracție.", 30), 
                ("C) Îmi place suspansul când aștept rezultatul.", 70), 
                ("D) Da, senzația când câștigi (sau pierzi) mult e unică.", 100)
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