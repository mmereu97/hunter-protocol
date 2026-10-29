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
AXIS_ID = 110
AXIS_NAME = "Stil de Atenție (Focus)"
# Pol Stânga (0): Multitasking / Distributiv / Distras
# Pol Dreapta (100): Deep Work / Focusat / Monahal

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
    # Punctaj: 0 = Multitasking/Distras, 100 = Deep Work/Focusat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Mediu și Obiceiuri) ---
        (
            "Când trebuie să te concentrezi la ceva dificil, ce mediu preferi?",
            "Environment, Noise, Focus", 
            1, 
            [
                ("A) O cafenea, un birou aglomerat, cu muzică sau TV pe fundal.", 0), 
                ("B) Puțin zgomot de fundal nu mă deranjează.", 30), 
                ("C) Prefer liniștea, dar mă pot adapta.", 70), 
                ("D) Liniște absolută. Orice zgomot îmi rupe ritmul.", 100)
            ]
        ),
        (
            "Cât de des îți verifici telefonul sau notificările în timp ce lucrezi?",
            "Distraction, Dopamine, Habit", 
            1, 
            [
                ("A) La fiecare câteva minute. Nu pot să nu mă uit.", 0), 
                ("B) Destul de des, la fiecare pauză mică.", 30), 
                ("C) O dată la oră sau când termin un task.", 70), 
                ("D) Niciodată. Îl pun pe 'Do Not Disturb' sau în altă cameră.", 100)
            ]
        ),
        (
            "Te consideri o persoană care face multitasking eficient sau preferi să faci un singur lucru odată?",
            "Multitasking vs Single-tasking, Work Style", 
            1, 
            [
                ("A) Multitasking. Fac 3 lucruri deodată și îmi place.", 0), 
                ("B) Pot jongla cu sarcini dacă e nevoie.", 30), 
                ("C) Prefer să termin una înainte să încep alta.", 60), 
                ("D) Single-tasking total. Multitasking-ul este ineficient și obositor.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Flow și Întreruperi) ---
        (
            "Dacă ești întrerupt în mijlocul unei sarcini complexe, cât de greu îți este să revii la nivelul de concentrare anterior?",
            "Interruption Cost, Cognitive Load", 
            2, 
            [
                ("A) Ușor. Mă mut de la o idee la alta instant.", 0), 
                ("B) Îmi ia un minut să mă reorientez.", 30), 
                ("C) E frustrant, îmi ia ceva timp.", 70), 
                ("D) Foarte greu. Îmi ia 15-20 de minute să reintru în starea de flux.", 100)
            ]
        ),
        (
            "Cât timp poți rămâne concentrat pe o singură sarcină dificilă fără să simți nevoia de o pauză sau distragere?",
            "Attention Span, Stamina", 
            2, 
            [
                ("A) Maxim 15-20 de minute.", 0), 
                ("B) Cam 45 de minute.", 30), 
                ("C) O oră sau două.", 70), 
                ("D) 3-4 ore sau mai mult. Uit să mănânc.", 100)
            ]
        ),
        (
            "Cât de des intri în starea de 'flux' (flow), unde uiți complet de timp și de tine în timp ce lucrezi?",
            "Flow State, Immersion", 
            2, 
            [
                ("A) Rar sau niciodată. Mă uit des la ceas.", 0), 
                ("B) Uneori, dacă îmi place foarte mult task-ul.", 30), 
                ("C) Destul de des.", 60), 
                ("D) Zilnic. Este modul meu standard de lucru.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: ADHD / Procrastinare / Burnout) ---
        (
            "Simți că mintea ta este ca un browser cu 50 de tab-uri deschise simultan?",
            "Racing Thoughts, Mental Chaos", 
            3, 
            [
                ("A) Da, mereu. Sar de la un gând la altul.", 0), 
                ("B) Deseori e aglomerat acolo sus.", 30), 
                ("C) Uneori, când sunt stresat.", 70), 
                ("D) Nu. Mă pot focaliza laser pe un singur tab.", 100)
            ]
        ),
        (
            "Te plictisești dacă trebuie să te ocupi de un singur subiect aprofundat timp de câteva ore?",
            "Boredom, Depth vs Breadth", 
            3, 
            [
                ("A) Da, am nevoie de varietate și noutate.", 0), 
                ("B) Încep să mă foiesc.", 30), 
                ("C) Rezist dacă e interesant.", 60), 
                ("D) Nu. Ador să sap în profunzime.", 100)
            ]
        ),
        (
            "Simți o nevoie compulsivă de a căuta informații noi sau de a schimba activitatea (scroll, click) la fiecare câteva minute?",
            "Dopamine Seeking, Popcorn Brain", 
            3, 
            [
                ("A) Da, e o nevoie fizică de stimulare.", 0), 
                ("B) Da, verific des știrile/social media.", 30), 
                ("C) Mă pot abține.", 70), 
                ("D) Nu. Pot sta liniștit cu gândurile mele sau cu o carte.", 100)
            ]
        ),
        (
            "Dacă lucrezi într-un birou Open Space gălăgios, cât de productiv ești?",
            "Environment Sensitivity, Efficiency", 
            3, 
            [
                ("A) Foarte productiv. Îmi dă energie.", 0), 
                ("B) Mă descurc, ignor zgomotul.", 30), 
                ("C) Îmi pun căști, altfel e greu.", 70), 
                ("D) Productivitate zero. Nu pot gândi în zgomot.", 100)
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