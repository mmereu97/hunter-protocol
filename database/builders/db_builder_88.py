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
AXIS_ID = 88
AXIS_NAME = "Romantism"
# Pol Stânga (0): Pragmatic / Cinic / Realist
# Pol Dreapta (100): Idealist / Romantic / Visător

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
    # Punctaj: 0 = Pragmatic, 100 = Romantic Incurabil
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Credințe de Bază) ---
        (
            "Ce părere ai despre conceptul de 'Suflet Pereche' (o singură persoană predestinată pentru tine)?",
            "Soulmate, Destiny, Beliefs", 
            1, 
            [
                ("A) Este un mit naiv. Există doar compatibilitate.", 0), 
                ("B) E o idee frumoasă, dar puțin probabilă.", 30), 
                ("C) Cred că există oameni cu care rezonăm special.", 70), 
                ("D) Absolut. Există cineva creat special pentru mine.", 100)
            ]
        ),
        (
            "Crezi în dragoste la prima vedere?",
            "Love at first sight, Attraction", 
            1, 
            [
                ("A) Nu, aia e doar atracție sexuală sau iluzie.", 0), 
                ("B) E posibil să îți placă cineva repede.", 30), 
                ("C) Da, se poate întâmpla.", 70), 
                ("D) Da, poți ști într-o secundă că el/ea este 'Alesul'.", 100)
            ]
        ),
        (
            "Cum vezi o relație ideală pe termen lung?",
            "Relationship Goals, Partnership vs Passion", 
            1, 
            [
                ("A) Un parteneriat solid, bazat pe respect și interese comune.", 0), 
                ("B) O prietenie bună.", 30), 
                ("C) O poveste de dragoste care evoluează.", 60), 
                ("D) O pasiune continuă, surprize și fluturi în stomac mereu.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Gesturi/Sărbători) ---
        (
            "Cât de importante sunt pentru tine gesturile romantice grandioase (cine la lumina lumânării, declarații publice, cadouri surpriză)?",
            "Gestures, Romance, Love Language", 
            2, 
            [
                ("A) Inutile și siropoase. Prefer ajutorul practic.", 0), 
                ("B) Drăguțe ocazional.", 30), 
                ("C) Importante pentru a menține scânteia.", 70), 
                ("D) Esențiale. Fără ele relația e moartă.", 100)
            ]
        ),
        (
            "Ce părere ai despre Ziua Îndrăgostiților (Valentine's Day)?",
            "Holidays, Commercialism vs Romance", 
            2, 
            [
                ("A) O sărbătoare comercială stupidă.", 0), 
                ("B) O zi ca oricare alta.", 20), 
                ("C) O ocazie bună să ieșim în oraș.", 70), 
                ("D) O zi magică ce trebuie sărbătorită corespunzător.", 100)
            ]
        ),
        (
            "Dacă partenerul tău trece printr-o perioadă financiară grea pe termen lung, cum vezi viitorul relației?",
            "Money vs Love, Pragmatism", 
            2, 
            [
                ("A) Iubirea nu ține de foame. Ar fi o problemă gravă.", 0), 
                ("B) Ne calculăm bugetul și vedem.", 30), 
                ("C) Îl susțin, dar e stresant.", 60), 
                ("D) Nu contează banii, important e că suntem împreună.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Limerență / Așteptări Nerealiste / Dependență) ---
        (
            "Ești de acord cu afirmația 'Dragostea învinge totul'?",
            "Philosophy, Idealism, Reality Check", 
            3, 
            [
                ("A) Nu. Banii, valorile și logistica contează mai mult.", 0), 
                ("B) Sună bine în filme, dar viața e altfel.", 30), 
                ("C) Învinge multe obstacole, dar nu chiar totul.", 70), 
                ("D) Da, dacă există iubire adevărată, nimic nu ne poate sta în cale.", 100)
            ]
        ),
        (
            "Dacă pasiunea ('scânteia') dispare după câțiva ani și rămâne doar o afecțiune caldă, ce faci?",
            "Long Term, Passion, Reality", 
            3, 
            [
                ("A) E normal, relația s-a maturizat.", 0), 
                ("B) E ok, atâta timp cât ne înțelegem.", 30), 
                ("C) Încerc să reaprind focul.", 60), 
                ("D) Mă simt nefericit. O relație fără pasiune intensă nu merită trăită.", 100)
            ]
        ),
        (
            "Ai fi dispus să renunți la cariera ta, la prieteni sau să te muți la capătul lumii pentru 'marea iubire'?",
            "Sacrifice, Priorities, Values", 
            3, 
            [
                ("A) Nu. Nu renunț la mine pentru altcineva.", 0), 
                ("B) Depinde de circumstanțe, dar e riscant.", 30), 
                ("C) Aș face compromisuri mari.", 70), 
                ("D) Da, fără să clipesc. Iubirea e tot ce contează.", 100)
            ]
        ),
        (
            "Te-ai îndrăgostit vreodată de ideea unei persoane (potențialul ei) mai mult decât de realitatea ei?",
            "Projection, Fantasy vs Reality", 
            3, 
            [
                ("A) Nu, văd oamenii așa cum sunt.", 0), 
                ("B) Rar.", 20), 
                ("C) Uneori am tendința să idealizez.", 60), 
                ("D) Da, mi se întâmplă des să mă îndrăgostesc de o fantezie.", 100)
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