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
AXIS_ID = 39
AXIS_NAME = "Conciliere"
# Pol Stânga (0): Combativ / Încăpățânat / Argumentativ
# Pol Dreapta (100): Împăciuitor / Cedează / Cooperant

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
    # Punctaj: 0 = Combativ, 100 = Împăciuitor
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Stil de Conflict) ---
        (
            "Când ești implicat într-o discuție în contradictoriu, care este obiectivul tău principal?",
            "Conflict, Winning vs Harmony", 
            1, 
            [
                ("A) Să câștig. Să demonstrez că am dreptate.", 0), 
                ("B) Să îmi susțin punctul de vedere ferm.", 30), 
                ("C) Să găsim o soluție rapidă.", 70), 
                ("D) Să aplanez conflictul, chiar dacă cedez.", 100)
            ]
        ),
        (
            "Dacă cineva te roagă să faci ceva ce nu îți convine, cât de greu îți este să refuzi?",
            "Refusal, People Pleasing", 
            1, 
            [
                ("A) Deloc. Refuz direct.", 0), 
                ("B) Pot refuza, dar explic de ce.", 30), 
                ("C) E destul de greu, inventez o scuză.", 70), 
                ("D) Foarte greu. De obicei accept ca să nu supăr.", 100)
            ]
        ),
        (
            "Cum reacționezi dacă ești tratat incorect la un magazin sau restaurant?",
            "Assertiveness, Confrontation", 
            1, 
            [
                ("A) Fac scandal până se rezolvă.", 0), 
                ("B) Cer să vorbesc cu managerul.", 30), 
                ("C) Menționez problema politicos.", 70), 
                ("D) Nu zic nimic, plătesc și plec.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Relații/Compromis) ---
        (
            "Într-o relație de cuplu sau prietenie, cine decide de obicei unde mergeți sau ce faceți?",
            "Control, Relationships, Dominance", 
            2, 
            [
                ("A) Eu. Îmi place să decid.", 0), 
                ("B) Discutăm, dar insist pe preferințele mele.", 30), 
                ("C) Facem cu rândul.", 70), 
                ("D) Celălalt. Mie îmi e indiferent, mă adaptez.", 100)
            ]
        ),
        (
            "Dacă știi că ai dreptate 100%, dar celălalt se enervează foarte tare, ce faci?",
            "Argument, De-escalation", 
            2, 
            [
                ("A) Continui până recunoaște. Adevărul contează.", 0), 
                ("B) Îi spun că greșește și închei discuția.", 30), 
                ("C) Îl las în pace momentan.", 70), 
                ("D) Îi dau dreptate doar ca să se calmeze.", 100)
            ]
        ),
        (
            "Ce te deranjează mai mult: să pierzi o dezbatere sau să creezi o situație jenantă/tensionată?",
            "Social Values, Harmony", 
            2, 
            [
                ("A) Să pierd. Nu suport să fiu contrazis.", 0), 
                ("B) Depinde de subiect.", 30), 
                ("C) Tensiunea e neplăcută.", 70), 
                ("D) Tensiunea. Prefer să pierd decât să ne certăm.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Agresivitate vs Victimă/Yes-Man) ---
        (
            "Ai tendința să îți ceri scuze chiar și atunci când nu este vina ta, doar pentru a restabili armonia?",
            "Apology, Guilt, Submissiveness", 
            3, 
            [
                ("A) Niciodată. Cine greșește, plătește.", 0), 
                ("B) Doar dacă am contribuit și eu la problemă.", 30), 
                ("C) Uneori, ca să deblochez situația.", 70), 
                ("D) Da, foarte des. Îmi asum vina ca să fie bine.", 100)
            ]
        ),
        (
            "Te consideri o persoană competitivă?",
            "Competition, Aggression", 
            3, 
            [
                ("A) Foarte. Vreau să câștig în orice.", 0), 
                ("B) Îmi place să câștig, dar joc fair-play.", 30), 
                ("C) Nu prea.", 70), 
                ("D) Deloc. Prefer cooperarea, competiția mă stresează.", 100)
            ]
        ),
        (
            "Dacă cineva te atacă verbal agresiv, te aperi sau te retragi?",
            "Fight or Flight, Conflict", 
            3, 
            [
                ("A) Contraatac imediat, cu dublă intensitate.", 0), 
                ("B) Mă apăr ferm.", 30), 
                ("C) Încerc să calmez spiritele.", 70), 
                ("D) Mă blochez, tac sau plâng.", 100)
            ]
        ),
        (
            "Cât de mult îți ascunzi adevăratele sentimente sau opinii pentru a nu-i deranja pe ceilalți?",
            "Authenticity, Masking, People Pleasing", 
            3, 
            [
                ("A) Deloc. Sunt o carte deschisă și directă.", 0), 
                ("B) Sunt diplomat, dar sincer.", 30), 
                ("C) Deseori, unele lucruri e mai bine să nu fie spuse.", 70), 
                ("D) Mereu. Spun ce vor alții să audă.", 100)
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