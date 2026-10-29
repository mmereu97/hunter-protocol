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
AXIS_ID = 3
AXIS_NAME = "Evitarea Lăcomiei"
# Pol Stânga (0): Materialist / Lux / Arogant financiar
# Pol Dreapta (100): Modest / Neinteresat / Simplu

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
    # Punctaj: 0 = Materialist (Risc), 100 = Modest (Sigur)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Corporate/General) ---
        (
            "Ce te motivează cel mai mult să accepți o promovare?",
            "Career, Money, Motivation", 
            1, 
            [
                ("A) Creșterea salarială și bonusurile. Banii contează.", 0), 
                ("B) Statutul și titlul mai important.", 30), 
                ("C) Provocarea profesională.", 70), 
                ("D) Posibilitatea de a avea un impact pozitiv.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să ai un birou luxos sau o mașină de serviciu scumpă?",
            "Status, Image, Corporate", 
            1, 
            [
                ("A) Foarte important. Arată valoarea mea.", 0), 
                ("B) Este un bonus plăcut, prefer să le am.", 30), 
                ("C) Nu contează prea mult, e doar logistică.", 70), 
                ("D) Deloc. Pot lucra de oriunde, rezultatele contează.", 100)
            ]
        ),
        (
            "Dacă ai câștiga o sumă uriașă la loterie, ai mai veni la muncă?",
            "Hypothetical, Money vs Meaning", 
            1, 
            [
                ("A) Nici o secundă. Aș trăi în lux toată viața.", 0), 
                ("B) Aș veni doar să îmi dau demisia spectaculos.", 20), 
                ("C) Probabil aș continua să lucrez ceva, dar part-time.", 70), 
                ("D) Da, munca îmi oferă sens, nu doar bani.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Lifestyle/Social) ---
        (
            "Când îți cumperi haine sau accesorii (ceas, telefon), cât de mult contează brandul?",
            "Lifestyle, Brands, Image", 
            2, 
            [
                ("A) Totul. Trebuie să se vadă că e scump.", 0), 
                ("B) Destul de mult, prefer lucrurile de firmă.", 30), 
                ("C) Mă uit la calitate, nu neapărat la etichetă.", 70), 
                ("D) Deloc. Cumpăr ce e funcțional și comod.", 100)
            ]
        ),
        (
            "Te deranjează dacă un coleg cu aceleași responsabilități câștigă mai mult decât tine?",
            "Envy, Money, Comparison", 
            2, 
            [
                ("A) Enorm. Mă simt jignit și furios.", 0), 
                ("B) Da, aș cere imediat o mărire.", 30), 
                ("C) Puțin, dar aș încerca să înțeleg de ce.", 70), 
                ("D) Nu, dacă își face treaba bine, merită. Eu mă focusez pe mine.", 100)
            ]
        ),
        (
            "Cum îți place să îți petreci vacanțele?",
            "Lifestyle, Spending", 
            2, 
            [
                ("A) Hoteluri de 5 stele, locații exclusiviste, VIP.", 0), 
                ("B) Locuri populare, confort ridicat.", 30), 
                ("C) Explorând locuri noi, confort mediu.", 70), 
                ("D) Camping, natură sau locuri simple și autentice.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Risc de Fraudă/Integritate) ---
        (
            "Consideri că oamenii bogați sunt superiori celor săraci?",
            "Values, Prejudice, Narcissism", 
            3, 
            [
                ("A) Da, bogăția arată inteligență și succes.", 0), 
                ("B) În general da, au demonstrat ceva.", 30), 
                ("C) Nu neapărat, depinde de caracter.", 70), 
                ("D) Nu. Valoarea unui om nu stă în portofel.", 100)
            ]
        ),
        (
            "Ai fi dispus să te căsătorești (sau să intri într-o relație) strict pentru bani?",
            "Relationships, Transactional, Values", 
            3, 
            [
                ("A) Da, dragostea trece, banii rămân.", 0), 
                ("B) Banii ajută mult la 'iubire'.", 30), 
                ("C) E greu, dar stabilitatea financiară e un factor.", 60), 
                ("D) Niciodată. Relațiile sunt despre sentimente.", 100)
            ]
        ),
        (
            "Dacă ai putea primi un bonus ilegal de 50.000 EUR pentru a aproba un contract dezavantajos firmei, ai face-o?",
            "Corruption, Fraud, Integrity Risk", 
            3, 
            [
                ("A) Da, e o sumă care îmi schimbă viața.", 0), 
                ("B) M-aș gândi foarte serios dacă pot scăpa neprins.", 20), 
                ("C) Probabil nu, e prea riscant.", 80), 
                ("D) Nu. Nu pot fi cumpărat.", 100)
            ]
        ),
        (
            "Ce părere ai despre afirmația: 'Lăcomia este bună' (Greed is good)?",
            "Worldview, Philosophy, Ambition", 
            3, 
            [
                ("A) Este adevărat. Lăcomia progresează lumea.", 0), 
                ("B) Este un motor necesar pentru afaceri.", 30), 
                ("C) Poate fi utilă în doze mici, dar periculoasă.", 70), 
                ("D) Fals. Lăcomia distruge societatea și caracterul.", 100)
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