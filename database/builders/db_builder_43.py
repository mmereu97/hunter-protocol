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
AXIS_ID = 43
AXIS_NAME = "Respectare Reguli"
# Pol Stânga (0): Anarhist / Flexibil / Nonconformist
# Pol Dreapta (100): Procedural / Conformist / Strict

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
    # Punctaj: 0 = Rebel, 100 = Conformist
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Trafic/Cotidian) ---
        (
            "Cum te raportezi la limitele de viteză și semnele de circulație când ești grăbit?",
            "Traffic, Laws, Compliance", 
            1, 
            [
                ("A) Sunt doar sugestii. Conduc cum permite drumul.", 0), 
                ("B) Le depășesc frecvent dacă nu e poliție.", 30), 
                ("C) Încerc să le respect, cu mici excepții.", 70), 
                ("D) Le respect cu strictețe. Siguranța și legea primează.", 100)
            ]
        ),
        (
            "Dacă cumperi un aparat nou, citești manualul de instrucțiuni înainte de a-l folosi?",
            "Instructions, Patience, Procedure", 
            1, 
            [
                ("A) Niciodată. Butonez până merge.", 0), 
                ("B) Doar dacă mă blochez.", 30), 
                ("C) Citesc părțile importante.", 70), 
                ("D) Da, citesc tot, pas cu pas, ca să nu greșesc.", 100)
            ]
        ),
        (
            "Ce părere ai despre birocrație și procedurile administrative?",
            "Bureaucracy, Order vs Chaos", 
            1, 
            [
                ("A) O pierdere de timp inutilă care trebuie ocolită.", 0), 
                ("B) Sunt enervante, dar le fac.", 30), 
                ("C) Sunt necesare pentru organizare.", 70), 
                ("D) Sunt esențiale. Fără ele ar fi haos.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Autoritate) ---
        (
            "La locul de muncă, dacă o procedură ți se pare ineficientă sau învechită, ce faci?",
            "Work, Innovation vs Compliance", 
            2, 
            [
                ("A) O ignor și fac cum știu eu că e mai bine.", 0), 
                ("B) O adaptez 'din mers' fără să anunț.", 30), 
                ("C) O respect, dar propun oficial schimbarea ei.", 70), 
                ("D) O urmez întocmai. Nu e treaba mea să schimb regulile.", 100)
            ]
        ),
        (
            "Cum reacționezi când vezi pe cineva încălcând o regulă minoră (ex: aruncă gunoi pe jos, parchează ilegal)?",
            "Civic Duty, Judgment", 
            2, 
            [
                ("A) Nu-mi pasă, și eu mai fac.", 0), 
                ("B) Mă deranjează puțin.", 30), 
                ("C) Dezaprob comportamentul.", 70), 
                ("D) Mă enervez foarte tare sau îi atrag atenția. Regulile sunt pentru toți.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să faci lucrurile 'ca la carte' (by the book)?",
            "Standards, Perfectionism, Rigidty", 
            2, 
            [
                ("A) Deloc. Rezultatul contează, nu metoda.", 0), 
                ("B) Destul de puțin. Prefer scurtăturile.", 30), 
                ("C) Important, evită erorile.", 70), 
                ("D) Foarte important. Există un singur mod corect de a face lucrurile.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: OCPD vs Antisocial) ---
        (
            "Crezi că există situații în care este moral să încalci legea pentru un bine mai mare?",
            "Ethics, Morality, Rigidty", 
            3, 
            [
                ("A) Da, legile sunt adesea nedrepte.", 0), 
                ("B) În situații de urgență, da.", 30), 
                ("C) Foarte rar, e o pantă alunecoasă.", 70), 
                ("D) Nu. Legea este absolută, indiferent de context.", 100)
            ]
        ),
        (
            "Te simți vinovat dacă încalci o regulă, chiar dacă știi că nu te-a văzut nimeni și nu a avut consecințe?",
            "Conscience, Guilt, Superego", 
            3, 
            [
                ("A) Nu. Dacă nu m-au prins, nu s-a întâmplat.", 0), 
                ("B) Nu prea.", 30), 
                ("C) Puțin inconfortabil.", 60), 
                ("D) Da, mă simt vinovat. Integritatea e ce faci când nu te vede nimeni.", 100)
            ]
        ),
        (
            "Ai tendința de a fi 'polițistul' grupului, amintindu-le celorlalți ce au voie și ce nu au voie să facă?",
            "Control, Monitoring, Policing", 
            3, 
            [
                ("A) Nu, urăsc oamenii care fac asta.", 0), 
                ("B) Doar dacă mă afectează direct.", 30), 
                ("C) Uneori, pentru siguranță.", 60), 
                ("D) Da. Cineva trebuie să mențină ordinea.", 100)
            ]
        ),
        (
            "Ce te definește mai bine: spiritul liber sau disciplina?",
            "Self-Image, Identity", 
            3, 
            [
                ("A) Spirit liber, rebel.", 0), 
                ("B) Independent.", 30), 
                ("C) Organizat.", 70), 
                ("D) Disciplinat și conformist.", 100)
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