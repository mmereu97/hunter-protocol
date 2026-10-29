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
AXIS_ID = 31
AXIS_NAME = "Curiozitate (Idei)"
# Pol Stânga (0): Tradiționalist / Fixist / Pratic
# Pol Dreapta (100): Intelectual / Curios / Filozof

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
    # Punctaj: 0 = Neinteresat (Pratic), 100 = Curios (Intelectual)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Interese Generale) ---
        (
            "Cât de des citești cărți de non-ficțiune, articole științifice sau te uiți la documentare despre istorie/natură?",
            "Reading, Knowledge, Hobbies", 
            1, 
            [
                ("A) Niciodată. Mă plictisesc groaznic.", 0), 
                ("B) Rar, doar dacă e un subiect viral.", 30), 
                ("C) Destul de des, îmi place să aflu lucruri noi.", 70), 
                ("D) Zilnic. Sunt avid de cunoaștere.", 100)
            ]
        ),
        (
            "Îți place să participi la discuții filozofice despre sensul vieții, viitorul tehnologiei sau politică globală?",
            "Philosophy, Debate, Abstract", 
            1, 
            [
                ("A) Nu, sunt vorbe goale. Să vorbim despre lucruri concrete.", 0), 
                ("B) Ascult, dar nu mă implic prea mult.", 30), 
                ("C) Îmi place, dacă interlocutorul e interesant.", 70), 
                ("D) Le ador! Aș putea dezbate ore în șir.", 100)
            ]
        ),
        (
            "Dacă întâlnești un cuvânt necunoscut sau un concept nou, ce faci?",
            "Learning, Curiosity, Internet", 
            1, 
            [
                ("A) Îl ignor și trec mai departe.", 0), 
                ("B) Întreb pe cineva, dacă e la îndemână.", 30), 
                ("C) Îl caut pe Google când am timp.", 70), 
                ("D) Opresc tot și îl caut imediat. Trebuie să știu ce înseamnă.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Rezolvare Probleme/Noutate) ---
        (
            "Preferi problemele care au o soluție clară și testată, sau pe cele care necesită o abordare creativă și neconvențională?",
            "Problem Solving, Routine vs Novelty", 
            2, 
            [
                ("A) Soluții clare. Nu vreau să reinventez roata.", 0), 
                ("B) Prefer metodele verificate, sunt mai sigure.", 30), 
                ("C) Îmi place să inovez uneori.", 70), 
                ("D) Cele creative. Mă incită să găsesc soluții noi.", 100)
            ]
        ),
        (
            "Cât de mult te interesează să înțelegi 'cum funcționează lucrurile' (mecanisme, sisteme sociale, universul)?",
            "Systems Thinking, Curiosity", 
            2, 
            [
                ("A) Deloc. Dacă merge, nu mă interesează cum.", 0), 
                ("B) Doar strictul necesar pentru jobul meu.", 30), 
                ("C) Sunt curios în domeniile mele de interes.", 70), 
                ("D) Fascinat. Vreau să înțeleg mecanismul din spate la orice.", 100)
            ]
        ),
        (
            "Ți se întâmplă să intri pe Wikipedia sau YouTube să cauți ceva și să ajungi să citești despre un subiect complet diferit 2 ore mai târziu?",
            "Rabbit Hole, Intellectual Flow", 
            2, 
            [
                ("A) Nu, nu pierd timpul așa.", 0), 
                ("B) Foarte rar.", 20), 
                ("C) Se mai întâmplă.", 70), 
                ("D) Da, frecvent. Curiozitatea mă poartă oriunde.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Rigiditate / Dogmatism vs Openness) ---
        (
            "Dacă descoperi o informație științifică care contrazice o credință veche a ta, cum reacționezi?",
            "Open-mindedness, Cognitive Flexibility, Dogma", 
            3, 
            [
                ("A) O resping. Știu eu mai bine.", 0), 
                ("B) Sunt sceptic, caut motive să o invalidez.", 30), 
                ("C) Sunt confuz, dar o analizez.", 70), 
                ("D) Îmi schimb părerea. Adevărul e mai important decât ego-ul.", 100)
            ]
        ),
        (
            "Consideri că arta, filozofia și literatura sunt domenii 'inutile' pentru că nu produc bani imediat?",
            "Pragmatism vs Culture, Values", 
            3, 
            [
                ("A) Da, sunt pierdere de vreme.", 0), 
                ("B) Sunt hobby-uri, nu priorități.", 30), 
                ("C) Au valoarea lor culturală.", 70), 
                ("D) Nu. Sunt esențiale pentru spiritul uman și civilizație.", 100)
            ]
        ),
        (
            "Îți place să rezolvi ghicitori, puzzle-uri logice sau să joci jocuri de strategie complexe?",
            "Intellectual Challenge, Gaming", 
            3, 
            [
                ("A) Nu, mă obosesc. Vreau relaxare.", 0), 
                ("B) Rar, prefer jocurile de noroc sau acțiune.", 30), 
                ("C) Da, îmi pun mintea la contribuție.", 70), 
                ("D) Da, caut activ provocări intelectuale.", 100)
            ]
        ),
        (
            "Te plictisești repede în discuțiile banale despre vreme, mâncare sau bârfe?",
            "Small Talk, Depth, Social", 
            3, 
            [
                ("A) Nu, sunt discuții normale și plăcute.", 0), 
                ("B) Sunt ok, fac parte din viață.", 30), 
                ("C) Prefer discuțiile mai serioase, dar mă adaptez.", 60), 
                ("D) Da, le detest. Vreau profunzime, nu suprafață.", 100)
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