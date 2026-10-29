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
AXIS_ID = 60
AXIS_NAME = "Comportament Antisocial"
# Pol Stânga (0): Legal / Moral / Cetățean Model
# Pol Dreapta (100): Antisocial / Criminal / Rebel

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
    # Punctaj: 0 = Legal, 100 = Antisocial (Risc Maxim)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Istoric/Autoritate) ---
        (
            "În timpul școlii sau liceului, ai avut probleme disciplinare majore (suspendări, exmatriculare, vizite dese la director)?",
            "School History, Discipline, Authority", 
            1, 
            [
                ("A) Niciodată. Eram un elev model.", 0), 
                ("B) Mici năzbâtii, nimic serios.", 30), 
                ("C) Da, am fost suspendat sau certat des.", 70), 
                ("D) Da, am fost exmatriculat sau am avut probleme grave de comportament.", 100)
            ]
        ),
        (
            "Ce părere ai despre poliție și organele de lege?",
            "Authority, Law, Attitude", 
            1, 
            [
                ("A) Îi respect și mă simt în siguranță.", 0), 
                ("B) Își fac treaba, unii sunt ok.", 30), 
                ("C) Nu îi suport, sunt abuzivi.", 70), 
                ("D) Sunt dușmanii mei. Sistemul trebuie fentat.", 100)
            ]
        ),
        (
            "Ai făcut vreodată ceva ilegal doar pentru adrenalina de a încălca regula (vandalism, furt mărunt, condus imprudent)?",
            "Thrill, Rule Breaking, Risk", 
            1, 
            [
                ("A) Nu, îmi e frică de consecințe.", 0), 
                ("B) Poate în copilărie.", 20), 
                ("C) Uneori e distractiv să riști.", 70), 
                ("D) Da, regulile sunt făcute să fie încălcate.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Familie/Conflicte) ---
        (
            "Cum a fost relația ta cu părinții sau profesorii în adolescență?",
            "Family Conflict, Rebellion", 
            2, 
            [
                ("A) Armonioasă, i-am respectat.", 0), 
                ("B) Conflicte normale de generații.", 30), 
                ("C) Tensionată, am plecat de acasă devreme.", 60), 
                ("D) Război total. Nu suportam să mi se spună ce să fac.", 100)
            ]
        ),
        (
            "Ai fost vreodată implicat în altercații fizice (bătăi) care au rezultat în răniri?",
            "Violence, Aggression, History", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) O dată, m-am apărat.", 30), 
                ("C) De câteva ori în tinerețe.", 70), 
                ("D) Da, am avut multe bătăi. Nu mă dau înapoi.", 100)
            ]
        ),
        (
            "Ai distrus vreodată proprietatea publică sau a altcuiva (graffiti, spart geamuri, zgâriat mașini)?",
            "Vandalism, Destruction, Anger", 
            2, 
            [
                ("A) Nu, respect munca altora.", 0), 
                ("B) Nu intenționat.", 20), 
                ("C) Poate când eram beat sau nervos.", 70), 
                ("D) Da, am făcut-o din răzbunare sau distracție.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Criminalitate / Psihopatie) ---
        (
            "Ai avut vreodată probleme legale serioase (amenzi penale, procese, reținere de către poliție)?",
            "Legal Issues, Criminal Record", 
            3, 
            [
                ("A) Niciodată, nici măcar o amendă de viteză.", 0), 
                ("B) Doar amenzi de circulație.", 20), 
                ("C) Am fost la secție pentru declarații.", 60), 
                ("D) Da, am cazier sau am fost arestat.", 100)
            ]
        ),
        (
            "Consideri că legile sunt făcute doar pentru a proteja bogații și a ține oamenii obișnuiți sub control?",
            "Worldview, Justification, Antisocial", 
            3, 
            [
                ("A) Nu, legile mențin ordinea necesară.", 0), 
                ("B) Sistemul nu e perfect, dar e necesar.", 30), 
                ("C) Da, sistemul e corupt.", 60), 
                ("D) Absolut. Singura lege reală e legea junglei.", 100)
            ]
        ),
        (
            "Ai condus vreodată sub influența alcoolului sau a substanțelor, considerând că poți controla situația?",
            "DUI, Risk, Responsibility", 
            3, 
            [
                ("A) Niciodată. Este iresponsabil.", 0), 
                ("B) Poate după o bere mică.", 30), 
                ("C) Da, dar pe distanțe scurte.", 70), 
                ("D) Da. Conduc mai bine când sunt 'vesel'.", 100)
            ]
        ),
        (
            "Dacă ai găsi un portofel plin cu bani și acte într-un loc izolat, care sunt șansele să îl predai la poliție intact?",
            "Integrity, Theft, Opportunity", 
            3, 
            [
                ("A) 100%. Mă pun în locul păgubitului.", 0), 
                ("B) Îl predau, dar poate sunt tentat.", 30), 
                ("C) Iau banii și arunc actele la cutia poștală.", 80), 
                ("D) Păstrez tot. Ghinionul lui, norocul meu.", 100)
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