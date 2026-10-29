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
AXIS_ID = 47
AXIS_NAME = "Îngrijorare (Apprehension)"
# Pol Stânga (0): Încrezător / Sigur pe sine
# Pol Dreapta (100): Temător / Vinovat / Îngrijorat

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
    # Punctaj: 0 = Încrezător, 100 = Îngrijorat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Dubii/Decizii) ---
        (
            "După ce ai luat o decizie, cât de des te gândești dacă ai procedat corect (second-guessing)?",
            "Self-Doubt, Decision Making", 
            1, 
            [
                ("A) Niciodată. Am încredere în judecata mea.", 0), 
                ("B) Rar, doar la decizii majore.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Mereu. Mă macină gândul că am greșit.", 100)
            ]
        ),
        (
            "Cum te simți în general în legătură cu capacitățile tale de a face față vieții?",
            "Confidence, Self-Efficacy", 
            1, 
            [
                ("A) Sunt foarte capabil și sigur pe mine.", 0), 
                ("B) Mă descurc bine.", 30), 
                ("C) Uneori mă simt depășit.", 70), 
                ("D) Mă simt inadecvat și nepregătit.", 100)
            ]
        ),
        (
            "Dacă cineva râde în preajma ta, te gândești automat că râde de tine?",
            "Paranoia, Insecurity, Social", 
            1, 
            [
                ("A) Nu, nici nu-mi trece prin cap.", 0), 
                ("B) Doar dacă am un motiv să cred asta.", 30), 
                ("C) Uneori mă verific.", 70), 
                ("D) Da, am mereu impresia că sunt ridicol.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Vinovăție/Grijă) ---
        (
            "Cât de mult te îngrijorezi că ai fi putut jigni sau supăra pe cineva fără să vrei?",
            "Social Guilt, People Pleasing", 
            2, 
            [
                ("A) Deloc. Dacă se supără, e problema lor.", 0), 
                ("B) Dacă nu mi-au zis nimic, presupun că e ok.", 30), 
                ("C) Mă gândesc la asta uneori.", 70), 
                ("D) Analizez fiecare conversație și mă simt vinovat pentru orice.", 100)
            ]
        ),
        (
            "Ai tendința să îți asumi responsabilitatea (și vina) pentru lucruri care nu depind de tine?",
            "Responsibility, Guilt Complex", 
            2, 
            [
                ("A) Nu. Îmi asum doar ce fac eu.", 0), 
                ("B) Sunt realist.", 30), 
                ("C) Uneori mă simt responsabil pentru atmosfera din grup.", 70), 
                ("D) Da, mă simt vinovat pentru tot ce merge prost în jur.", 100)
            ]
        ),
        (
            "Te simți adesea tensionat sau 'pe ace', chiar dacă nu există un motiv concret?",
            "Anxiety, Tension, Mood", 
            2, 
            [
                ("A) Nu, sunt foarte relaxat.", 0), 
                ("B) Doar când sunt foarte obosit.", 30), 
                ("C) Am perioade de neliniște.", 70), 
                ("D) Da, am o stare de aprehensiune continuă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Sindrom Impostor / Anxietate Generalizată / Depresie) ---
        (
            "Simți o vinovăție difuză, ca și cum ai fi făcut ceva rău, dar nu știi exact ce?",
            "Free-floating Guilt, Neuroticism", 
            3, 
            [
                ("A) Niciodată. Conștiința mea e curată.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori am acest sentiment apăsător.", 70), 
                ("D) Da, mă simt ca un 'păcătos' sau un om rău fără motiv.", 100)
            ]
        ),
        (
            "Te aștepți ca lucrurile să meargă prost, chiar și atunci când totul pare să fie bine?",
            "Pessimism, Dread, Anxiety", 
            3, 
            [
                ("A) Nu, sunt optimist.", 0), 
                ("B) Sunt precaut, dar nu fatalist.", 30), 
                ("C) Mă tem că norocul se va termina.", 70), 
                ("D) Da. Aștept mereu 'să cadă celălalt pantof' (dezastrul).", 100)
            ]
        ),
        (
            "Ești genul de persoană care își cere scuze des, chiar și când nu e cazul (ex: dacă cineva te calcă pe tine pe picior)?",
            "Apologizing, Submissiveness", 
            3, 
            [
                ("A) Nu. Cer scuze doar când greșesc.", 0), 
                ("B) Sunt politicos, dar nu exagerat.", 30), 
                ("C) Uneori, din reflex.", 60), 
                ("D) Da, îmi cer scuze pentru simpla mea existență.", 100)
            ]
        ),
        (
            "Te simți vreodată copleșit de un sentiment de 'iminență a pericolului' sau de groază inexplicabilă?",
            "Panic, Doom, Fear", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Poate după un vis urât.", 20), 
                ("C) Rareori.", 60), 
                ("D) Da, am senzația că urmează ceva groaznic.", 100)
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