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
AXIS_ID = 6
AXIS_NAME = "Anxietate"
# Pol Stânga (0): Calm / Relaxat / Stabil
# Pol Dreapta (100): Îngrijorat / Tensionat / Panicat

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
    # Punctaj: 0 = Calm, 100 = Anxios
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Zilnic) ---
        (
            "Cât de des te surprinzi îngrijorându-te pentru lucruri mărunte care probabil nu se vor întâmpla?",
            "Worry, Overthinking, Daily Life", 
            1, 
            [
                ("A) Niciodată. Iau lucrurile așa cum vin.", 0), 
                ("B) Rar, doar dacă e ceva important.", 30), 
                ("C) Destul de des, mintea mea fuge la scenarii.", 70), 
                ("D) Tot timpul. Îmi fac griji pentru orice.", 100)
            ]
        ),
        (
            "Când ai o perioadă liberă sau o vacanță, cât de ușor îți este să te relaxezi complet?",
            "Relaxation, Stress, Mindset", 
            1, 
            [
                ("A) Imediat. Mă deconectez total.", 0), 
                ("B) Îmi ia puțin timp, dar reușesc.", 30), 
                ("C) Greu. Mă gândesc tot la ce am de făcut.", 70), 
                ("D) Imposibil. Mă simt vinovat sau agitat dacă nu fac ceva.", 100)
            ]
        ),
        (
            "Cum reacționezi când apare o problemă neprevăzută la muncă sau acasă?",
            "Stress Response, Adaptability", 
            1, 
            [
                ("A) O rezolv calm, fără stres.", 0), 
                ("B) Mă enervez puțin, dar mă adun.", 30), 
                ("C) Mă stresez vizibil și devin agitat.", 70), 
                ("D) Intru în panică și mă blochez momentan.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Somatizare/Somn/Viitor) ---
        (
            "Ai probleme cu somnul din cauza gândurilor care nu îți dau pace noaptea?",
            "Sleep, Insomnia, Rumination", 
            2, 
            [
                ("A) Nu, dorm ca un prunc.", 0), 
                ("B) Ocazional, dacă am o zi grea a doua zi.", 30), 
                ("C) Destul de des adorm greu din cauza grijilor.", 70), 
                ("D) Da, am insomnii cronice din cauza stresului.", 100)
            ]
        ),
        (
            "Simți adesea o tensiune fizică inexplicabilă (nod în gât, dureri de cap, stomac strâns)?",
            "Somatic, Physical Symptoms, Tension", 
            2, 
            [
                ("A) Nu, mă simt bine fizic.", 0), 
                ("B) Rar, doar la oboseală mare.", 30), 
                ("C) Da, am des dureri de cap sau tensiune musculară.", 70), 
                ("D) Da, simt anxietatea fizic aproape zilnic.", 100)
            ]
        ),
        (
            "Când te gândești la viitorul îndepărtat (peste 5-10 ani), care este sentimentul dominant?",
            "Future, Optimism vs Pessimism", 
            2, 
            [
                ("A) Entuziasm și încredere.", 0), 
                ("B) Curiozitate și planificare.", 30), 
                ("C) Nesiguranță și o ușoară teamă.", 70), 
                ("D) Frică. Simt că se va întâmpla ceva rău.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Sindrom Impostor / Burnout / Depresie) ---
        (
            "Ți se întâmplă să verifici obsesiv telefonul sau email-ul de teamă să nu fi primit o veste proastă?",
            "Hypervigilance, Fear of Bad News", 
            3, 
            [
                ("A) Nu. Verific când am timp.", 0), 
                ("B) Verific des, dar din plictiseală.", 20), 
                ("C) Da, am o strângere de inimă când sună telefonul.", 70), 
                ("D) Da, trăiesc cu teama constantă a unei catastrofe.", 100)
            ]
        ),
        (
            "Ai avut vreodată senzația că pierzi controlul sau că 'o iei razna' din cauza presiunii?",
            "Panic Attack, Mental Health, Breakdown", 
            3, 
            [
                ("A) Niciodată. Sunt stâncă.", 0), 
                ("B) M-am simțit copleșit, dar nu am pierdut controlul.", 30), 
                ("C) Am avut momente la limită.", 70), 
                ("D) Da, am avut atacuri de panică sau căderi nervoase.", 100)
            ]
        ),
        (
            "Cât de mult te afectează părerea celorlalți despre tine?",
            "Social Anxiety, Validation, Ego", 
            3, 
            [
                ("A) Deloc. Știu cine sunt.", 0), 
                ("B) Țin cont de ea, dar nu mă consum.", 30), 
                ("C) Mă îngrijorează să nu fac o impresie proastă.", 70), 
                ("D) Enorm. Analizez fiecare cuvânt spus de teama ridicolului.", 100)
            ]
        ),
        (
            "Dacă un prieten sau un membru al familiei întârzie și nu răspunde la telefon, ce gândești?",
            "Catastrophizing, Attachment, Worry", 
            3, 
            [
                ("A) Că e ocupat sau a rămas fără baterie.", 0), 
                ("B) Mă irită puțin lipsa de punctualitate.", 30), 
                ("C) Încep să mă îngrijorez după o oră.", 60), 
                ("D) Mă gândesc automat la accidente sau tragedii.", 100)
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