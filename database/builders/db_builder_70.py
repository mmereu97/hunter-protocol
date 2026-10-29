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
AXIS_ID = 70
AXIS_NAME = "Atașament Anxios"
# Pol Stânga (0): Sigur / Independent / Încrezător
# Pol Dreapta (100): Anxios / Dependent / Frică de Abandon

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
    # Punctaj: 0 = Sigur, 100 = Anxios
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Reacție la Distanță/Tăcere) ---
        (
            "Dacă trimiți un mesaj unei persoane apropiate și nu primești răspuns timp de câteva ore (deși vezi că a fost activă), ce gândești?",
            "Communication, Anxiety, Overthinking", 
            1, 
            [
                ("A) Că e ocupată. Nu mă îngrijorez.", 0), 
                ("B) Mă întreb ce face, dar îmi văd de treabă.", 30), 
                ("C) Încep să mă gândesc dacă am supărat-o cu ceva.", 70), 
                ("D) Intru în panică. Sigur mă ignoră sau vrea să rupă legătura.", 100)
            ]
        ),
        (
            "Cât de des simți nevoia să întrebi partenerul sau prietenii: 'Ești supărat pe mine?' sau 'Mă mai iubești?'",
            "Reassurance, Validation, Insecurity", 
            1, 
            [
                ("A) Niciodată. Știu unde stau.", 0), 
                ("B) Rar, doar după o ceartă.", 30), 
                ("C) Destul de des, am nevoie de confirmare.", 70), 
                ("D) Zilnic. Dacă nu îmi spun, cred că nu le mai pasă.", 100)
            ]
        ),
        (
            "Cât de mult te îngrijorezi că persoanele importante din viața ta te vor părăsi sau își vor pierde interesul pentru tine?",
            "Fear of Abandonment, Future Anxiety", 
            1, 
            [
                ("A) Deloc. Relațiile mele sunt solide.", 0), 
                ("B) Uneori am dubii trecătoare.", 30), 
                ("C) Este o frică recurentă.", 70), 
                ("D) Este cea mai mare frică a mea. Mă gândesc constant la asta.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Comportament în Relații) ---
        (
            "Ți se pare dificil să le oferi celorlalți spațiu personal fără să te simți respins?",
            "Boundaries, Space, Rejection Sensitivity", 
            2, 
            [
                ("A) Nu, și eu am nevoie de spațiu.", 0), 
                ("B) Înțeleg nevoia de spațiu.", 20), 
                ("C) Mă simt puțin dat la o parte.", 60), 
                ("D) Da. Dacă vor spațiu, înseamnă că vor să scape de mine.", 100)
            ]
        ),
        (
            "Ai tendința să analizezi excesiv cuvintele, tonul sau gesturile partenerului, căutând semne de răceală?",
            "Hypervigilance, Analysis, Trust", 
            2, 
            [
                ("A) Nu, iau lucrurile așa cum sunt.", 0), 
                ("B) Doar dacă pare ceva ciudat.", 30), 
                ("C) Da, sunt atent la schimbări de ton.", 70), 
                ("D) Da, despic firul în 4. Orice schimbare mică mă alarmează.", 100)
            ]
        ),
        (
            "Cât de mult depinde starea ta de spirit de atenția pe care o primești de la partener/persoana favorită?",
            "Mood Dependency, Emotional Fusion", 
            2, 
            [
                ("A) Sunt independent emoțional.", 0), 
                ("B) Mă influențează, dar nu total.", 30), 
                ("C) Mult. Dacă e rece, sunt trist.", 70), 
                ("D) Total. Dacă nu îmi dă atenție, mă prăbușesc emoțional.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: BPD / Dependență Emoțională) ---
        (
            "Ai implorat vreodată pe cineva să nu te părăsească sau ai făcut promisiuni desperate pentru a menține o relație?",
            "Desperation, Dignity, Abandonment", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Nu, am demnitate.", 20), 
                ("C) Poate o dată, în tinerețe.", 60), 
                ("D) Da. Nu pot suporta ideea despărțirii.", 100)
            ]
        ),
        (
            "Ți s-a spus vreodată că iubești 'prea intens', că ești 'sufocant' sau 'lipicios' (clingy)?",
            "Feedback, Intensity, Boundaries", 
            3, 
            [
                ("A) Nu, sunt considerat echilibrat.", 0), 
                ("B) Mi s-a spus că sunt afectuos.", 20), 
                ("C) Uneori, că cer prea mult timp.", 70), 
                ("D) Da, acesta este motivul principal al despărțirilor mele.", 100)
            ]
        ),
        (
            "Ai tendința de a te atașa foarte rapid și profund de persoane pe care abia le-ai cunoscut?",
            "Speed of Attachment, Idealization", 
            3, 
            [
                ("A) Nu, încrederea se construiește în timp.", 0), 
                ("B) Sunt deschis, dar prudent.", 30), 
                ("C) Mă entuziasmez repede.", 60), 
                ("D) Da. Mă îndrăgostesc sau mă atașez instantaneu și total.", 100)
            ]
        ),
        (
            "Te simți incomplet, anxios sau fără valoare atunci când nu ești într-o relație?",
            "Self-Worth, Solitude Intolerance", 
            3, 
            [
                ("A) Nu, sunt bine și singur.", 0), 
                ("B) Prefer să fiu în relație, dar pot sta singur.", 30), 
                ("C) Mă simt singuratic.", 70), 
                ("D) Da. Singurătatea mă terifiază, am nevoie de cineva ca să exist.", 100)
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