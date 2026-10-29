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
AXIS_ID = 86
AXIS_NAME = "Motivație Financiară"
# Pol Stânga (0): Misionar / Sens / Pasiune
# Pol Dreapta (100): Mercenar / Bani / Statut

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
    # Punctaj: 0 = Sens (Misionar), 100 = Bani (Mercenar)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Alegeri de Carieră) ---
        (
            "Dacă ai avea de ales între două joburi: unul prost plătit dar care îți place la nebunie și ajută lumea, și unul plictisitor dar plătit triplu, ce alegi?",
            "Career, Values, Passion vs Money", 
            1, 
            [
                ("A) Cel prost plătit. Fericirea nu are preț.", 0), 
                ("B) Probabil cel cu pasiune, dacă mă descurc cu banii.", 30), 
                ("C) Cel bine plătit. Pasiunea o fac în weekend.", 70), 
                ("D) Cel plătit triplu. Banii sunt libertate.", 100)
            ]
        ),
        (
            "Ce înseamnă pentru tine 'succesul' în viață?",
            "Success Definition, Values", 
            1, 
            [
                ("A) Să las ceva bun în urmă, să fiu iubit.", 0), 
                ("B) Să am echilibru și liniște.", 30), 
                ("C) Să am o carieră solidă și recunoaștere.", 70), 
                ("D) Să fiu bogat și puternic. Cifrele din cont nu mint.", 100)
            ]
        ),
        (
            "Cât de mult contează pachetul salarial atunci când aplici pentru un job nou?",
            "Job Hunting, Priorities", 
            1, 
            [
                ("A) E secundar. Echipa și misiunea contează.", 0), 
                ("B) E important, dar nu decisiv.", 30), 
                ("C) Foarte important.", 70), 
                ("D) Este singurul criteriu care contează cu adevărat.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Stil de Viață/Negociere) ---
        (
            "Te-ai simți jignit dacă ai afla că un coleg cu aceleași responsabilități câștigă mai mult decât tine?",
            "Comparison, Equity, Envy", 
            2, 
            [
                ("A) Nu, dacă își face treaba bine.", 0), 
                ("B) Puțin, aș cere explicații.", 30), 
                ("C) Da, m-ar frustra.", 70), 
                ("D) Da, aș pleca imediat sau aș face scandal. E inacceptabil.", 100)
            ]
        ),
        (
            "Ești dispus să lucrezi ore suplimentare neplătite pentru un proiect în care crezi?",
            "Volunteering, Dedication, Transactional", 
            2, 
            [
                ("A) Da, oricând.", 0), 
                ("B) Uneori, dacă e critic.", 30), 
                ("C) Rar. Timpul meu costă bani.", 70), 
                ("D) Niciodată. Nu lucrez pe gratis.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să ai obiecte care să îți arate statutul financiar (mașină, ceas, haine de brand)?",
            "Status, Materialism, Image", 
            2, 
            [
                ("A) Deloc. Sunt superficiale.", 0), 
                ("B) Nu pun preț pe ele.", 30), 
                ("C) Îmi place calitatea, care costă.", 60), 
                ("D) Foarte important. Haina face omul și arată cine ești.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Flight Risk / Lăcomie / Corupție) ---
        (
            "Dacă o companie concurentă (pe care o disprețuiești moral) ți-ar oferi dublul salariului actual, te-ai muta?",
            "Loyalty, Ethics, Selling Out", 
            3, 
            [
                ("A) Nu. Nu pot lucra pentru cineva în care nu cred.", 0), 
                ("B) Ar fi greu, aș refuza probabil.", 30), 
                ("C) M-aș gândi serios. Toți avem un preț.", 70), 
                ("D) Imediat. Morala nu plătește facturile.", 100)
            ]
        ),
        (
            "Ai accepta să faci o muncă pe care o consideri degradantă sau plictisitoare dacă plata ar fi extrem de mare?",
            "Dignity vs Money, Trade-off", 
            3, 
            [
                ("A) Nu, sănătatea mea mentală e mai importantă.", 0), 
                ("B) Poate pe termen scurt.", 30), 
                ("C) Da, pentru o perioadă, să strâng bani.", 70), 
                ("D) Da. Orice muncă e onorabilă dacă e bine plătită.", 100)
            ]
        ),
        (
            "Ce părere ai despre oamenii care aleg cariere vocaționale prost plătite (artiști, asistenți sociali)?",
            "Judgment, Value System", 
            3, 
            [
                ("A) Îi admir. Sunt curajoși.", 0), 
                ("B) Îi înțeleg.", 30), 
                ("C) Sunt puțin naivi.", 70), 
                ("D) Își ratează viața. Fără bani nu ești nimeni.", 100)
            ]
        ),
        (
            "Care este relația ta cu banii?",
            "Money Mindset", 
            3, 
            [
                ("A) Sunt un mijloc, nu un scop.", 0), 
                ("B) Sunt necesari pentru confort.", 30), 
                ("C) Sunt o prioritate.", 70), 
                ("D) Sunt măsura valorii mele ca om.", 100)
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