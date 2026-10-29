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
AXIS_ID = 34
AXIS_NAME = "Deschidere la Acțiuni"
# Pol Stânga (0): Rutină / Obicei / Familiar
# Pol Dreapta (100): Nou / Experimentare / Varietate

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
    # Punctaj: 0 = Rutină, 100 = Noutate
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Generale) ---
        (
            "Când mergi la restaurantul tău preferat, ce comanzi?",
            "Food, Habits, Comfort Zone", 
            1, 
            [
                ("A) Același lucru, de fiecare dată. Știu că îmi place.", 0), 
                ("B) Rareori schimb, dacă îmi recomandă cineva.", 30), 
                ("C) Încerc des ceva nou din meniu.", 70), 
                ("D) Niciodată același lucru. Vreau să gust tot.", 100)
            ]
        ),
        (
            "Cum îți alegi destinațiile de vacanță?",
            "Travel, Novelty, Safety", 
            1, 
            [
                ("A) Merg în același loc (ex: la aceeași mare/pensiune) de ani de zile.", 0), 
                ("B) Prefer locuri similare cu ce știu.", 30), 
                ("C) Îmi place să văd o țară nouă la câțiva ani.", 70), 
                ("D) Caut locuri exotice, ciudate și complet diferite cultural.", 100)
            ]
        ),
        (
            "Ce părere ai despre rutină (program fix, aceleași activități)?",
            "Routine, Lifestyle, Boredom", 
            1, 
            [
                ("A) O ador. Îmi oferă siguranță și confort.", 0), 
                ("B) E necesară pentru eficiență.", 30), 
                ("C) Mă plictisește dacă durează prea mult.", 70), 
                ("D) O urăsc. Mă simt ca într-o închisoare.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Flexibilitate/Schimbare) ---
        (
            "Dacă trebuie să ajungi undeva, folosești mereu același drum?",
            "Commute, Exploration, Efficiency", 
            2, 
            [
                ("A) Da, cel mai scurt și cunoscut.", 0), 
                ("B) Schimb doar dacă e trafic.", 30), 
                ("C) Mai schimb peisajul din când în când.", 60), 
                ("D) Da, o iau pe străduțe noi doar ca să văd ce mai e pe acolo.", 100)
            ]
        ),
        (
            "Cât de des îți rearanjezi mobila în casă sau schimbi decorul?",
            "Home, Environment, Change", 
            2, 
            [
                ("A) Niciodată. Mobila stă așa de când m-am mutat.", 0), 
                ("B) Doar când renovez forțat.", 30), 
                ("C) O dată la câțiva ani, pentru un aer proaspăt.", 70), 
                ("D) Des. Mă plictisesc să văd aceeași cameră.", 100)
            ]
        ),
        (
            "Dacă ți se propune să înveți un hobby complet nou și neobișnuit (ex: olărit, scrimă, origami), ce zici?",
            "Hobbies, Learning, Curiosity", 
            2, 
            [
                ("A) Nu, am deja hobby-urile mele.", 0), 
                ("B) Probabil nu, pare pierdere de timp.", 30), 
                ("C) Sună interesant, aș încerca o lecție.", 70), 
                ("D) Da! Îmi place să încerc orice activitate nouă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Flight Risk / Rigiditate / OCPD) ---
        (
            "Te-ai muta într-o țară cu o cultură complet diferită (ex: Japonia, India) pentru un an?",
            "Relocation, Adaptability, Adventure", 
            3, 
            [
                ("A) Exclus. Nu m-aș putea adapta.", 0), 
                ("B) Doar dacă condițiile sunt excelente și sigure.", 30), 
                ("C) Ar fi o provocare interesantă.", 70), 
                ("D) Mi-aș face bagajele mâine. Abia aștept șocul cultural.", 100)
            ]
        ),
        (
            "Dacă magazinul tău preferat se închide și trebuie să cumperi altă marcă de produse, cât de tare te deranjează?",
            "Brand Loyalty, Rigidity, Anxiety", 
            3, 
            [
                ("A) Foarte tare. Sunt fidel brandurilor mele.", 0), 
                ("B) E neplăcut, trebuie să testez altele.", 30), 
                ("C) Nu prea mult.", 70), 
                ("D) Deloc. Oricum îmi place să testez produse noi.", 100)
            ]
        ),
        (
            "Cum reacționezi când șeful sau partenerul propune o schimbare radicală de plan în ultimul moment?",
            "Spontaneity, Control, Anxiety", 
            3, 
            [
                ("A) Mă panichez sau mă enervez. Nu-mi plac surprizele.", 0), 
                ("B) Rezist inițial, am nevoie de timp să procesez.", 30), 
                ("C) Mă adaptez.", 70), 
                ("D) Super! Planurile neprevăzute sunt cele mai tari.", 100)
            ]
        ),
        (
            "Ai încerca o activitate care contravine normelor tale obișnuite (ex: să mergi la o operă dacă ești rocker, sau la un meci de box dacă ești pacifist)?",
            "Openness, Prejudice, Experience", 
            3, 
            [
                ("A) Nu, știu ce-mi place și ce nu.", 0), 
                ("B) Probabil m-aș plictisi.", 30), 
                ("C) Aș merge de curiozitate.", 70), 
                ("D) Da, vreau să înțeleg ce văd alții în asta.", 100)
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