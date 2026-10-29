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
AXIS_ID = 83
AXIS_NAME = "Toleranță la Risc"
# Pol Stânga (0): Aversiune la Risc / Siguranță
# Pol Dreapta (100): Jucător / Riscant / Speculator

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
    # Punctaj: 0 = Aversiune (Safety), 100 = Risc (Gambler)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Bani și Carieră) ---
        (
            "Dacă ai avea 10.000 EUR de investit, ce ai face cu ei?",
            "Investment, Money, Safety", 
            1, 
            [
                ("A) Depozit bancar garantat sau titluri de stat. Siguranța e cheia.", 0), 
                ("B) Fonduri mutuale diversificate (risc mediu).", 30), 
                ("C) Acțiuni la bursă sau imobiliare.", 70), 
                ("D) Crypto, start-up-uri sau trading agresiv. Vreau profit maxim.", 100)
            ]
        ),
        (
            "Preferi un job cu salariu fix mediu, dar foarte stabil, sau unul bazat pe comision unde poți câștiga triplu, dar poți lua și zero?",
            "Career, Salary, Stability vs Gain", 
            1, 
            [
                ("A) Salariu fix. Am nevoie de predictibilitate.", 0), 
                ("B) Fix plus un mic bonus.", 30), 
                ("C) Jumătate fix, jumătate comision.", 60), 
                ("D) 100% comision. Îmi asum riscul pentru câștigul potențial.", 100)
            ]
        ),
        (
            "Când trebuie să iei o decizie cu rezultat incert, cum te simți?",
            "Decision Making, Anxiety vs Excitement", 
            1, 
            [
                ("A) Foarte anxios. Încerc să elimin orice risc.", 0), 
                ("B) Precaut, analizez toate variantele de eșec.", 30), 
                ("C) Calculat, dar optimist.", 70), 
                ("D) Entuziasmat. Riscul face jocul interesant.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Asigurări/Pierderi) ---
        (
            "Când cumperi un electrocasnic scump, plătești extra pentru garanție extinsă?",
            "Insurance, Loss Aversion", 
            2, 
            [
                ("A) Da, întotdeauna. Nu vreau surprize.", 0), 
                ("B) De obicei da.", 30), 
                ("C) Rar, doar la lucruri foarte fragile.", 70), 
                ("D) Nu. E o risipă de bani, îmi asum riscul.", 100)
            ]
        ),
        (
            "Imaginează-ți că ai pierdut o sumă de bani într-o investiție. Care e reacția ta?",
            "Reaction to Loss, Resilience", 
            2, 
            [
                ("A) Mă panichez și retrag tot ce a mai rămas.", 0), 
                ("B) Mă supăr și nu mai investesc o perioadă.", 30), 
                ("C) Analizez unde am greșit și merg mai departe.", 70), 
                ("D) Dublez miza pentru a recupera. Face parte din joc.", 100)
            ]
        ),
        (
            "Ce te sperie mai tare: posibilitatea de a pierde ce ai deja sau posibilitatea de a rata o mare oportunitate (FOMO)?",
            "Loss Aversion vs Opportunity Seeking", 
            2, 
            [
                ("A) Să pierd ce am. 'Mai bine vrabia din mână'.", 0), 
                ("B) Înclin spre siguranță.", 30), 
                ("C) Să ratez oportunitatea.", 70), 
                ("D) Să ratez șansa vieții. Aș risca totul pentru ea.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Flight Risk / Gambling / Iresponsabilitate) ---
        (
            "Ai fi dispus să îți ipotechezi casa pentru a finanța o afacere în care crezi, deși există riscul de faliment?",
            "Entrepreneurship, High Stakes", 
            3, 
            [
                ("A) Niciodată. Casa familiei e sfântă.", 0), 
                ("B) Nu, aș căuta investitori.", 20), 
                ("C) M-aș gândi foarte bine.", 60), 
                ("D) Da. Cine nu riscă, nu câștigă.", 100)
            ]
        ),
        (
            "Ai împrumutat vreodată bani pentru a face o investiție riscantă sau pentru jocuri de noroc?",
            "Debt, Leverage, Recklessness", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Doar sume mici de la prieteni.", 30), 
                ("C) Da, am folosit 'leverage' (banii băncii).", 70), 
                ("D) Da, și aș mai face-o. E singura cale de a crește rapid.", 100)
            ]
        ),
        (
            "Dacă ai primi o ofertă de muncă într-o altă țară, mult mai bine plătită, dar instabilă (proiect pe 6 luni), ai pleca mâine?",
            "Mobility, Stability vs Gain", 
            3, 
            [
                ("A) Nu, stabilitatea e mai importantă.", 0), 
                ("B) Doar dacă am garanții.", 30), 
                ("C) Probabil că da.", 70), 
                ("D) Imediat. Îmi fac bagajele acum.", 100)
            ]
        ),
        (
            "Te-ai descrie ca o persoană care joacă 'la sigur' sau care joacă 'la victorie'?",
            "Defense vs Offense, Strategy", 
            3, 
            [
                ("A) La sigur. Apărarea câștigă campionate.", 0), 
                ("B) Prudent, dar calculat.", 30), 
                ("C) Ofensiv.", 70), 
                ("D) La victorie totală. Ori câștig tot, ori pierd tot.", 100)
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