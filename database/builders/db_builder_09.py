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
AXIS_ID = 9
AXIS_NAME = "Depresie"
# Pol Stânga (0): Optimist / Vesel
# Pol Dreapta (100): Trist / Descurajat

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
    # Punctaj: 0 = Optimist (Sănătos), 100 = Depresiv (Risc)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Mood) ---
        (
            "Cum ți-ai descrie starea de spirit generală în ultimele săptămâni?",
            "Mood, General Wellbeing", 
            1, 
            [
                ("A) Excelentă, plină de energie și optimism.", 0), 
                ("B) Bună, cu suișuri și coborâșuri normale.", 30), 
                ("C) Ușor apatică sau melancolică.", 70), 
                ("D) Foarte proastă. Mă simt trist aproape tot timpul.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să te motivezi să începi ziua dimineața?",
            "Motivation, Morning, Energy", 
            1, 
            [
                ("A) Mă trezesc gata de acțiune.", 0), 
                ("B) Am nevoie de o cafea, dar apoi e ok.", 30), 
                ("C) E greu. Trag de mine să ies din pat.", 70), 
                ("D) E o luptă. Aș prefera să stau în pat toată ziua.", 100)
            ]
        ),
        (
            "Când te gândești la viitorul tău pe termen scurt, ce simți?",
            "Outlook, Hope, Future", 
            1, 
            [
                ("A) Entuziasm. Am multe planuri.", 0), 
                ("B) Curiozitate și calm.", 30), 
                ("C) Îngrijorare sau indiferență.", 70), 
                ("D) Lipsă de speranță. Nu văd nimic bun venind.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Anhedonie/Oboseală) ---
        (
            "Mai simți plăcere făcând activitățile care obișnuiau să îți placă (hobby-uri, ieșiri)?",
            "Anhedonia, Pleasure, Hobbies", 
            2, 
            [
                ("A) Da, mă bucur de ele la fel de mult.", 0), 
                ("B) În mare parte da, poate puțin mai rar.", 30), 
                ("C) Nu prea. Le fac din inerție.", 70), 
                ("D) Nu simt nicio plăcere. Totul pare gri și inutil.", 100)
            ]
        ),
        (
            "Cum stai cu nivelul de energie fizică și mentală?",
            "Fatigue, Energy, Physical", 
            2, 
            [
                ("A) Debordant. Nu stau locului.", 0), 
                ("B) Normal pentru vârsta mea.", 30), 
                ("C) Mă simt adesea obosit fără motiv.", 70), 
                ("D) Sunt epuizat constant. Orice efort e o corvoadă.", 100)
            ]
        ),
        (
            "Ai observat schimbări semnificative în apetit sau somn (prea mult sau prea puțin)?",
            "Somatic, Sleep, Appetite", 
            2, 
            [
                ("A) Nu, am un program stabil.", 0), 
                ("B) Mici variații cauzate de stres.", 30), 
                ("C) Da, dorm prost sau mănânc haotic.", 70), 
                ("D) Da, schimbări majore care îmi afectează sănătatea.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Demoralizare / Risc Suicidar - Profiling Only) ---
        (
            "Cât de des te simți vinovat sau inutil, chiar și pentru lucruri care nu sunt vina ta?",
            "Guilt, Self-Worth, Shame", 
            3, 
            [
                ("A) Niciodată. Am o stimă de sine bună.", 0), 
                ("B) Rar, dacă chiar am greșit.", 30), 
                ("C) Destul de des mă critic aspru.", 70), 
                ("D) Constant. Simt că sunt o povară pentru alții.", 100)
            ]
        ),
        (
            "Ți se întâmplă să simți un 'gol interior' sau o lipsă de sens care persistă?",
            "Void, Meaning, Existential", 
            3, 
            [
                ("A) Nu. Viața mea are sens.", 0), 
                ("B) Uneori îmi pun întrebări filozofice.", 30), 
                ("C) Da, am perioade de vid interior.", 70), 
                ("D) Da, simt un gol permanent și dureros.", 100)
            ]
        ),
        (
            "Ai simțit vreodată că viața nu merită trăită sau ți-ai dorit să adormi și să nu te mai trezești?",
            "Suicidal Ideation, Hopelessness, Critical Risk", 
            3, 
            [
                ("A) Niciodată. Iubesc viața.", 0), 
                ("B) Am avut gânduri trecătoare în momente grele, dar atât.", 40), 
                ("C) Mă gândesc uneori că ar fi o eliberare.", 80), 
                ("D) Da, mă gândesc des la asta.", 100)
            ]
        ),
        (
            "Cât de mult efort îți trebuie pentru a te concentra la sarcini simple (citit, urmărit un film)?",
            "Concentration, Brain Fog", 
            3, 
            [
                ("A) Niciun efort. Mă concentrez ușor.", 0), 
                ("B) Puțin efort dacă sunt obosit.", 30), 
                ("C) Îmi fuge mintea des, e greu să fiu atent.", 70), 
                ("D) Nu mă pot concentra deloc, mintea mea e în ceață.", 100)
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