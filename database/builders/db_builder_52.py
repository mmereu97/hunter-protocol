import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 52
AXIS_NAME = "Narcisism"
# Pol Stânga (0): Modest / Umil
# Pol Dreapta (100): Arogant / Grandios / Narcisist

# 3. HASHING
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
    # Punctaj: 0 = Modest, 100 = Narcisist
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Imagine de sine) ---
        (
            "Cum reacționezi când nu primești atenția sau recunoașterea pe care consideri că o meriți?",
            "Validation, Ego, Reaction", 
            1, 
            [
                ("A) Nu mă deranjează, nu caut faimă.", 0), 
                ("B) Sunt puțin dezamăgit, dar trece.", 30), 
                ("C) Mă simt frustrat și neapreciat.", 70), 
                ("D) Mă înfurii. Oamenii sunt incompetenți dacă nu văd valoarea mea.", 100)
            ]
        ),
        (
            "Te surprinzi des visând la un succes nelimitat, putere absolută sau frumusețe ideală?",
            "Fantasies, Grandiosity, Daydreaming", 
            1, 
            [
                ("A) Nu, am visuri realiste.", 0), 
                ("B) Uneori visez să câștig la loto.", 30), 
                ("C) Da, îmi imaginez des că sunt faimos.", 70), 
                ("D) Da, știu că sunt destinat să fac lucruri mărețe.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să arăți mai bine, să ai haine mai scumpe sau o mașină mai bună decât cei din jurul tău?",
            "Status, Comparison, Image", 
            1, 
            [
                ("A) Deloc. Nu mă compar cu alții.", 0), 
                ("B) Îmi place să arăt bine, dar pentru mine.", 30), 
                ("C) Este important să am un statut vizibil.", 70), 
                ("D) Esențial. Trebuie să fiu cel mai bun din încăpere.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Relații/Superioritate) ---
        (
            "Consideri că regulile obișnuite nu ar trebui să se aplice oamenilor excepționali ca tine?",
            "Entitlement, Rules, Superiority", 
            2, 
            [
                ("A) Nu. Regulile sunt egale pentru toți.", 0), 
                ("B) În general da, dar uneori birocrația e proastă.", 30), 
                ("C) Uneori simt că merit o excepție.", 70), 
                ("D) Da. Oamenii de top nu ar trebui limitați de reguli mediocre.", 100)
            ]
        ),
        (
            "Ai tendința de a monopoliza conversațiile și de a aduce vorba mereu despre tine?",
            "Conversation, Self-Centered, Empathy", 
            2, 
            [
                ("A) Nu, îmi place să ascult.", 0), 
                ("B) Încerc să păstrez un echilibru.", 30), 
                ("C) Uneori, dacă subiectul mă pasionează.", 70), 
                ("D) Da, poveștile mele sunt cele mai interesante.", 100)
            ]
        ),
        (
            "Cum te simți când cineva te critică?",
            "Criticism, Fragility, Defense", 
            2, 
            [
                ("A) Analizez dacă are dreptate.", 0), 
                ("B) Mă supără puțin, dar accept.", 30), 
                ("C) Mă pun în defensivă imediat.", 70), 
                ("D) Mă simt atacat și umilit. Cine e el să mă critice?", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Uncoachable / Leadership Toxic) ---
        (
            "Crezi că majoritatea oamenilor te invidiază pentru calitățile sau succesul tău?",
            "Envy, Paranoia, Projection", 
            3, 
            [
                ("A) Nu, de ce m-ar invidia?", 0), 
                ("B) Poate câțiva, e normal.", 30), 
                ("C) Deseori simt invidia celorlalți.", 70), 
                ("D) Da, e greu să fii în vârf. Toți vor să mă doboare.", 100)
            ]
        ),
        (
            "Ai folosi pe cineva pentru a-ți atinge scopurile, chiar dacă știi că acea persoană va avea de suferit?",
            "Exploitation, Lack of Empathy", 
            3, 
            [
                ("A) Niciodată. Oamenii nu sunt unelte.", 0), 
                ("B) Aș evita, dar uneori în afaceri e dur.", 30), 
                ("C) Dacă scopul e important, sacrificiile sunt necesare.", 70), 
                ("D) Da. Fiecare e responsabil pentru el însuși.", 100)
            ]
        ),
        (
            "Preferi să te asociezi doar cu oameni de statut înalt, faimoși sau 'speciali'?",
            "Status Seeking, Elitism", 
            3, 
            [
                ("A) Nu, am prieteni din toate mediile.", 0), 
                ("B) Nu contează statutul, ci caracterul.", 20), 
                ("C) Prefer oameni care au realizat ceva în viață.", 60), 
                ("D) Da. Nu îmi pierd timpul cu oameni mediocri.", 100)
            ]
        ),
        (
            "Simți că ai o misiune specială sau un destin grandios care te așteaptă?",
            "Grandiosity, Destiny", 
            3, 
            [
                ("A) Nu, vreau doar o viață fericită.", 0), 
                ("B) Sper să realizez ceva util.", 30), 
                ("C) Simt că pot face mai mult decât media.", 60), 
                ("D) Da, sunt predestinat pentru mărire și istorie.", 100)
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