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
AXIS_ID = 30
AXIS_NAME = "Apreciere Estetică"
# Pol Stânga (0): Utilitar / Pratic / Insensibil la artă
# Pol Dreapta (100): Artistic / Sensibil / Estet

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
    # Punctaj: 0 = Utilitar, 100 = Estet
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Generale) ---
        (
            "Când cumperi un obiect (telefon, mașină, mobilă), cât de mult contează aspectul vs. specificațiile tehnice?",
            "Shopping, Design vs Function, Preferences", 
            1, 
            [
                ("A) Deloc. Mă interesează doar să funcționeze bine.", 0), 
                ("B) Mă uit la specificații, aspectul e bonus.", 30), 
                ("C) Aspectul e foarte important, trebuie să îmi placă.", 70), 
                ("D) Designul e decisiv. Nu cumpăr ceva urât, oricât de bun ar fi.", 100)
            ]
        ),
        (
            "Cât de des te oprești să admiri un peisaj, un apus de soare sau o clădire frumoasă?",
            "Nature, Awareness, Beauty", 
            1, 
            [
                ("A) Niciodată. Nu am timp de romantisme.", 0), 
                ("B) Rar, dacă e ceva spectaculos.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Zilnic. Găsesc frumusețe peste tot.", 100)
            ]
        ),
        (
            "Îți place să mergi la muzee de artă, galerii sau concerte de muzică clasică/simfonică?",
            "Culture, Art, Hobbies", 
            1, 
            [
                ("A) Nu, mă plictisesc de mor.", 0), 
                ("B) Merg doar dacă sunt invitat sau e un eveniment mare.", 30), 
                ("C) Da, îmi face plăcere.", 70), 
                ("D) Da, sunt locurile mele preferate, mă hrănesc sufletește.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Reacție Emoțională/Mediu) ---
        (
            "Ți s-a întâmplat vreodată ca o melodie, o poezie sau un tablou să te emoționeze până la lacrimi sau să îți dea fiori?",
            "Chills, Emotion, Art Sensitivity", 
            2, 
            [
                ("A) Nu. E doar sunet sau vopsea.", 0), 
                ("B) Nu îmi amintesc.", 20), 
                ("C) Da, câteva piese muzicale speciale.", 70), 
                ("D) Da, frecvent. Arta mă atinge profund.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine ca spațiul în care locuiești să fie decorat armonios și estetic?",
            "Home, Decoration, Harmony", 
            2, 
            [
                ("A) Deloc. E doar un loc unde dorm.", 0), 
                ("B) Vreau să fie curat, nu neapărat decorat.", 30), 
                ("C) Îmi place să am câteva tablouri sau plante.", 70), 
                ("D) Esențial. Investesc mult timp și bani în design interior.", 100)
            ]
        ),
        (
            "Ce părere ai despre poezie?",
            "Poetry, Literature, Abstract", 
            2, 
            [
                ("A) O pierdere de vreme. Prefer textele clare, informative.", 0), 
                ("B) Nu o înțeleg prea bine.", 30), 
                ("C) Îmi plac anumite poezii.", 70), 
                ("D) O ador. Exprimă lucruri pe care proza nu le poate atinge.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Sensibilitate Artistică vs Pragmatism Extrem) ---
        (
            "Ai fi dispus să cheltui o sumă semnificativă de bani pe un obiect decorativ care nu are nicio utilitate practică, doar pentru că e frumos?",
            "Money, Art Value, Utility", 
            3, 
            [
                ("A) Niciodată. Ar fi o risipă.", 0), 
                ("B) Probabil nu.", 30), 
                ("C) Da, dacă îmi place mult.", 70), 
                ("D) Da, frumusețea are o valoare intrinsecă imensă.", 100)
            ]
        ),
        (
            "Te simți fizic inconfortabil sau lipsit de energie dacă ești nevoit să lucrezi într-un mediu urât, gri și deprimant?",
            "Environment Sensitivity, Mood", 
            3, 
            [
                ("A) Nu, pot lucra oriunde.", 0), 
                ("B) Nu îmi place, dar mă adaptez.", 30), 
                ("C) Mă afectează negativ.", 70), 
                ("D) Da, am nevoie de frumos în jur ca să funcționez.", 100)
            ]
        ),
        (
            "Ce părere ai despre arta abstractă sau modernă care nu reprezintă nimic clar?",
            "Abstract Art, Openness", 
            3, 
            [
                ("A) 'Asta poate să facă și copilul meu'. E o prostie.", 0), 
                ("B) Nu îmi spune nimic.", 30), 
                ("C) Unele lucrări sunt interesante.", 70), 
                ("D) Îmi place să descifrez sensurile și emoțiile din spatele ei.", 100)
            ]
        ),
        (
            "Simți nevoia să te exprimi artistic (prin scris, pictură, dans, muzică), chiar dacă nu ești profesionist?",
            "Creativity, Expression, Hobby", 
            3, 
            [
                ("A) Nu. Nu am înclinații artistice.", 0), 
                ("B) Rareori.", 30), 
                ("C) Da, am un hobby creativ.", 70), 
                ("D) Da, este modul meu principal de relaxare și exprimare.", 100)
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