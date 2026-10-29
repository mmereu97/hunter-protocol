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
AXIS_ID = 4
AXIS_NAME = "Modestie"
# Pol Stânga (0): Arogant / Superior / Narcisist
# Pol Dreapta (100): Umil / Egal / Modest

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
    # Punctaj: 0 = Arogant (Risc), 100 = Modest (Safe)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Social) ---
        (
            "Dacă ești sincer cu tine, consideri că posezi calități care te fac superior majorității oamenilor?",
            "Self-Image, Ego, Narcissism", 
            1, 
            [
                ("A) Da, categoric. Sunt peste medie.", 0), 
                ("B) În multe privințe, da.", 30), 
                ("C) Nu neapărat, fiecare are atuurile lui.", 70), 
                ("D) Nu. Sunt un om obișnuit, ca toți ceilalți.", 100)
            ]
        ),
        (
            "Cum te simți când trebuie să stai la o coadă lungă sau să respecți o procedură birocratică greoaie?",
            "Entitlement, Patience, Rules", 
            1, 
            [
                ("A) Furios. Timpul meu e prea valoros pentru asta.", 0), 
                ("B) Frustrat, încerc să găsesc o scurtătură.", 30), 
                ("C) E neplăcut, dar aștept ca toată lumea.", 70), 
                ("D) E normal, regulile sunt pentru toți.", 100)
            ]
        ),
        (
            "Când obții un succes major, cât de important este pentru tine ca ceilalți să afle și să te felicite?",
            "Recognition, Social, Validation", 
            1, 
            [
                ("A) Foarte important. Succesul neștiut nu are valoare.", 0), 
                ("B) Îmi place să fiu recunoscut pentru merite.", 30), 
                ("C) E plăcut, dar nu e scopul principal.", 70), 
                ("D) Nu contează. Satisfacția mea e interioară.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Interacțiune/Status) ---
        (
            "Dacă un chelner sau un subaltern greșește ceva simplu, cum reacționezi de obicei?",
            "Power Dynamics, Empathy, Arrogance", 
            2, 
            [
                ("A) Îi atrag atenția ferm sau ironic. Trebuie să învețe.", 0), 
                ("B) Sunt vizibil iritat.", 30), 
                ("C) Îl corectez politicos.", 70), 
                ("D) Sunt înțelegător, oricine poate greși.", 100)
            ]
        ),
        (
            "Îți place să fii centrul atenției la petreceri sau ședințe?",
            "Extraversion, Ego, Attention Seeking", 
            2, 
            [
                ("A) Da, îmi place să domin camera.", 0), 
                ("B) De multe ori, da.", 30), 
                ("C) Doar dacă am ceva important de spus.", 70), 
                ("D) Nu, prefer să ascult sau să stau retras.", 100)
            ]
        ),
        (
            "Crezi că ai merita mai multe privilegii în societate datorită inteligenței sau statutului tău?",
            "Entitlement, Social Justice", 
            2, 
            [
                ("A) Da, elita ar trebui tratată diferit.", 0), 
                ("B) Unele avantaje ar fi justificate.", 30), 
                ("C) Nu cred în privilegii speciale.", 80), 
                ("D) Nu, toți oamenii sunt egali în drepturi.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Narcisism/Uncoachable) ---
        (
            "Dacă cineva îți critică o idee în public, cum interpretezi gestul?",
            "Criticism, Defensive, Ego", 
            3, 
            [
                ("A) Ca pe un atac personal sau invidie.", 0), 
                ("B) Mă enervez și contraatac.", 20), 
                ("C) Analizez dacă are dreptate.", 70), 
                ("D) Apreciez feedback-ul, mă ajută să cresc.", 100)
            ]
        ),
        (
            "Ți se pare natural ca ceilalți să te asculte și să te urmeze fără să pună prea multe întrebări?",
            "Leadership, Control, Authoritarian", 
            3, 
            [
                ("A) Da, de obicei știu cel mai bine.", 0), 
                ("B) În domeniul meu de expertiză, da.", 30), 
                ("C) Prefer să explic și să conving.", 70), 
                ("D) Nu. Autoritatea se câștigă, nu se impune.", 100)
            ]
        ),
        (
            "Ai tendința de a-i întrerupe pe alții când vorbesc pentru că simți că știi deja ce vor să spună?",
            "Communication, Patience, Respect", 
            3, 
            [
                ("A) Da, îi ajut să ajungă la concluzie mai repede.", 0), 
                ("B) Deseori, dacă sunt lenți.", 30), 
                ("C) Încerc să mă abțin, deși e greu.", 60), 
                ("D) Nu, ascult până la capăt din respect.", 100)
            ]
        ),
        (
            "Cât de mult te preocupă să ai haine de brand, mașini scumpe sau accesorii care să îți arate statutul?",
            "Materialism, Status, Image", 
            3, 
            [
                ("A) Este esențial. Haina face omul.", 0), 
                ("B) Este important pentru imaginea mea.", 30), 
                ("C) Apreciez calitatea, nu brandul neapărat.", 70), 
                ("D) Deloc. Sunt lucruri superficiale.", 100)
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