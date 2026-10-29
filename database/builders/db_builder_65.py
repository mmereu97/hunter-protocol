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
AXIS_ID = 65
AXIS_NAME = "Locus of Control"
# Pol Stânga (0): Extern (Soarta / Noroc / Pasiv)
# Pol Dreapta (100): Intern (Eu decid / Efort / Activ)

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
    # Punctaj: 0 = Extern (Soarta), 100 = Intern (Eu)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Succes/Eșec General) ---
        (
            "Când cineva are un succes profesional rapid, care crezi că este, de obicei, cauza principală?",
            "Success Attribution, Luck vs Effort", 
            1, 
            [
                ("A) A avut noroc, pile sau a fost la locul potrivit.", 0), 
                ("B) Un amestec de șansă și muncă.", 30), 
                ("C) Munca și pregătirea lui.", 70), 
                ("D) Efortul susținut și abilitatea. Norocul ți-l faci singur.", 100)
            ]
        ),
        (
            "Când lucrurile merg prost în viața ta, care este primul gând?",
            "Failure Analysis, Blame", 
            1, 
            [
                ("A) 'De ce mi se întâmplă mereu mie?'.", 0), 
                ("B) 'E o perioadă proastă'.", 30), 
                ("C) 'Ce nu am prevăzut?'.", 70), 
                ("D) 'Ce am greșit și cum pot repara?'.", 100)
            ]
        ),
        (
            "Cât de mult crezi că poți influența cursul vieții tale prin deciziile pe care le iei?",
            "Agency, Destiny, Control", 
            1, 
            [
                ("A) Puțin. Multe lucruri sunt predestinate.", 0), 
                ("B) Pot influența unele aspecte, dar contextul contează.", 30), 
                ("C) Mult. Alegerile mele contează.", 70), 
                ("D) Total. Sunt 100% responsabil de unde ajung.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Carieră/Relații) ---
        (
            "Dacă nu primești o promovare pe care ți-o doreai, ce concluzie tragi?",
            "Career, Promotion, Responsibility", 
            2, 
            [
                ("A) Șeful are preferați sau sistemul e corupt.", 0), 
                ("B) Poate nu a fost momentul potrivit.", 30), 
                ("C) Trebuie să mă pregătesc mai bine data viitoare.", 70), 
                ("D) Nu am performat suficient. Trebuie să întreb ce să îmbunătățesc.", 100)
            ]
        ),
        (
            "Crezi că notele la școală sau evaluările la muncă depind mai mult de cât înveți/muncești sau de cât de mult te place profesorul/șeful?",
            "Evaluation, Subjectivity vs Merit", 
            2, 
            [
                ("A) De cât de mult te place șeful. Totul e politic.", 0), 
                ("B) E un mix, subiectivismul există.", 30), 
                ("C) În mare parte de efortul meu.", 70), 
                ("D) Exclusiv de performanța mea. Rezultatele nu mint.", 100)
            ]
        ),
        (
            "Când ești într-o relație conflictuală, consideri că celălalt este sursa problemei?",
            "Relationships, Blame, Self-Reflection", 
            2, 
            [
                ("A) Da, dacă el/ea s-ar schimba, totul ar fi bine.", 0), 
                ("B) De obicei celălalt începe.", 30), 
                ("C) Vina e mereu la mijloc.", 60), 
                ("D) Mă uit întâi la ce am făcut eu greșit.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Victimizare / Fatalism / Depresie) ---
        (
            "Ce părere ai despre afirmația: 'Oamenii săraci rămân săraci pentru că sistemul nu le dă nicio șansă'?",
            "Societal View, Victimhood, System", 
            3, 
            [
                ("A) Adevărat. Nu ai cum să ieși din sărăcie.", 0), 
                ("B) E foarte greu, sistemul e rigid.", 30), 
                ("C) E greu, dar se poate cu efort.", 70), 
                ("D) Fals. Oricine poate reuși dacă muncește suficient și e deștept.", 100)
            ]
        ),
        (
            "Te simți adesea neputincios în fața evenimentelor din viața ta?",
            "Helplessness, Anxiety, Coping", 
            3, 
            [
                ("A) Da, sunt purtat de val.", 0), 
                ("B) Uneori mă simt copleșit.", 30), 
                ("C) Rar.", 70), 
                ("D) Nu. Întotdeauna există o soluție sau o acțiune de luat.", 100)
            ]
        ),
        (
            "Crezi în noroc sau ghinion ca forțe care îți guvernează ziua?",
            "Superstition, Luck", 
            3, 
            [
                ("A) Da, am zile cu ghinion clar.", 0), 
                ("B) Uneori pare că universul e împotrivă.", 30), 
                ("C) Norocul e când pregătirea întâlnește oportunitatea.", 70), 
                ("D) Nu există noroc. Există cauză și efect.", 100)
            ]
        ),
        (
            "Dacă îți faci un plan detaliat, te aștepți să funcționeze?",
            "Planning, Confidence, Outcome", 
            3, 
            [
                ("A) Nu, oricum apare ceva neprevăzut și îl strică.", 0), 
                ("B) Sunt sceptic.", 30), 
                ("C) De obicei funcționează.", 70), 
                ("D) Da, pentru că îl voi face să funcționeze.", 100)
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