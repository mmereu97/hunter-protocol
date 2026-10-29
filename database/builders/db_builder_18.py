import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINITIONS
AXIS_ID = 18
AXIS_NAME = "Căldură Umană"

# 3. HASHING (Time Machine)
def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", f"Populating Axis {AXIS_ID}: {AXIS_NAME}...")

    # 4. DATASET (GENERATE THIS CONTENT IN ROMANIAN)
    # Options format: [("A) Text (Left Pole)", 0), ("B) Text", 30), ("C) Text", 70), ("D) Text (Right Pole)", 100)]
    
    questions_data = [
        # --- VALUL 1 (SCREENING) ---
        (
            "Cum te percep, în general, oamenii când te întâlnesc pentru prima dată?", 
            "prima impresie, percepție, socializare", 
            1, 
            [("A) Ca o persoană rece și distantă", 0), ("B) Ca o persoană rezervată, dar politicoasă", 30), ("C) Ca o persoană prietenoasă, dar nu foarte deschisă", 70), ("D) Ca o persoană caldă și primitoare", 100)]
        ),
        (
            "Ce reacție ai cel mai des în contexte sociale informale?", 
            "comportament social, interacțiune, expresivitate", 
            1, 
            [("A) Rămân în fundal și observ, rareori inițiez conversații", 0), ("B) Particip doar dacă sunt abordat direct", 30), ("C) Particip activ, dar nu sunt cel mai extrovertit", 70), ("D) Zâmbesc des, conversez cu ușurință și încerc să includ pe toată lumea", 100)]
        ),
        (
            "Cât de des zâmbești în mod natural în interacțiunile de zi cu zi?", 
            "expresie facială, comunicare non-verbală, emoții", 
            1, 
            [("A) Rareori zâmbesc, chiar și în situații prietenoase", 0), ("B) Zâmbesc doar când este social adecvat", 30), ("C) Zâmbesc destul de des, mai ales cu oamenii pe care îi cunosc", 70), ("D) Zâmbesc frecvent și natural în majoritatea interacțiunilor", 100)]
        ),

        # --- VALUL 2 (CONFIRMARE) ---
        (
            "Cum reacționezi când un prieten apropiat te îmbrățișează?", 
            "contact fizic, relații apropiate, confort emoțional", 
            2, 
            [("A) Mă simt inconfortabil și încerc să evit contactul", 0), ("B) Accept gestul, dar rămân rigid și nu răspund la fel", 30), ("C) Reciproc gestul, dar nu inițiez eu contactul fizic", 70), ("D) Îmbrățișez cu căldură și apreciez gestul de afecțiune", 100)]
        ),
        (
            "Ce părere ai despre exprimarea emoțiilor în public?", 
            "exprimare emoțională, vulnerabilitate, norme sociale", 
            2, 
            [("A) Cred că emoțiile ar trebui păstrate private", 0), ("B) Emoțiile pot fi exprimate, dar cu moderație", 30), ("C) Nu am probleme cu exprimarea emoțiilor, dar o fac selectiv", 70), ("D) Sunt complet confortabil exprimându-mi emoțiile, inclusiv în public", 100)]
        ),
        (
            "Cum îți menții relațiile cu prietenii apropiați?", 
            "relații personale, investiție emoțională, comunicare", 
            2, 
            [("A) Prefer contacte rare și mai formale", 0), ("B) Mențin relațiile, dar rareori inițiez întâlniri", 30), ("C) Încerc să mă văd regulat și să fiu prezent pentru ei", 70), ("D) Investesc mult timp și energie în a menține legături strânse și calde", 100)]
        ),

        # --- VALUL 3 (DEEP DIVE) ---
        (
            "Când un prieten trece printr-o perioadă dificilă emoțional, care este reacția ta ta imediată?", 
            "empathie, sprijin emoțional, inteligență emoțională", 
            3, 
            [("A) Mă simt nepregătit și prefer să păstrez distanța", 0), ("B) Ofer sfaturi practice, dar evit discuțiile emoționale profunde", 30), ("C) Ascult și încerc să înțeleg, dar mă simt stânjenit să exprim compasiune", 70), ("D) Sunt prezent emoțional, ascult fără a judeca și ofer sprijin necondiționat", 100)]
        ),
        (
            "Cum te simți despre vulnerabilitatea în relațiile apropiate?", 
            "intimitate emoțională, bariere personale, încredere", 
            3, 
            [("A) O consider un semn de slăbiciune și o evit", 0), ("B) Îmi este greu să fiu vulnerabil, chiar și cu persoanele apropiate", 30), ("C) Pot fi vulnerabil, dar doar cu un cerc foarte restrâns de oameni", 70), ("D) Consider că vulnerabilitatea este esențială pentru conexiuni autentice și nu am probleme să o arăt", 100)]
        ),
        (
            "Ce descrie cel mai bine relația ta cu propriile emoții?", 
            "conștientizare emoțională, alexitimie, inteligență emoțională", 
            3, 
            [("A) Rareori îmi dau seama ce simt și am dificultăți în a numi emoțiile", 0), ("B) Îmi recunosc emoțiile, dar prefer să nu le analizez prea mult", 30), ("C) Îmi înțeleg emoțiile și le pot exprima, dar nu întotdeauna cu ușurință", 70), ("D) Sunt foarte conectat cu emoțiile mele și le pot exprima natural", 100)]
        ),
        (
            "Ce înseamnă pentru tine o relație profundă cu altcineva?", 
            "intimitate, conexiune emoțională, relații semnificative", 
            3, 
            [("A) Prefer relațiile superficiale și nu caut conexiuni profunde", 0), ("B) Apreciez relațiile, dar păstrez o anumită distanță emoțională", 30), ("C) Caut conexiuni profunde, dar am nevoie de timp pentru a dezvolta încrederea", 70), ("D) Caut activ relații profunde bazate pe încredere reciprocă, vulnerabilitate și sprijin emoțional", 100)]
        )
    ]

    try:
        # 5. CLEANUP
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"Cleared old questions for Axis {AXIS_ID}.")

        # 6. INSERT
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
        log("db_conn", f"SUCCESS: {count} questions inserted for {AXIS_NAME}.")

    except Exception as e:
        log_error(f"Error populating Axis {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()