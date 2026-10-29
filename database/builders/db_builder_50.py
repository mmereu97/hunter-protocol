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
AXIS_ID = 50
AXIS_NAME = "Deschidere la Schimbare"
# Pol Stânga (0): Conservator / Tradiționalist
# Pol Dreapta (100): Radical / Inovator / Experimental

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
    # Punctaj: 0 = Conservator, 100 = Radical
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Tehnologie/Noutate) ---
        (
            "Când apare o actualizare majoră de software sau o tehnologie nouă la muncă, cum reacționezi?",
            "Technology, Adaptability, Change", 
            1, 
            [
                ("A) Mă enervez. De ce schimbă ceva care mergea bine?", 0), 
                ("B) Aștept să văd dacă are bug-uri înainte să o folosesc.", 30), 
                ("C) O instalez și învăț să o folosesc.", 70), 
                ("D) Abia aștept! Îmi place să testez funcții noi.", 100)
            ]
        ),
        (
            "În general, preferi metodele tradiționale, verificate în timp, sau ideile moderne și experimentale?",
            "Tradition vs Innovation, Methods", 
            1, 
            [
                ("A) Tradiționale. Riscul e mai mic.", 0), 
                ("B) Prefer o bază solidă cu mici îmbunătățiri.", 30), 
                ("C) Sunt deschis la modernizare.", 70), 
                ("D) Experimentale. Trebuie să evoluăm constant.", 100)
            ]
        ),
        (
            "Dacă șeful tău propune o reorganizare completă a departamentului, ce simți?",
            "Work, Restructuring, Security", 
            1, 
            [
                ("A) Frică și rezistență. Stabilitatea e crucială.", 0), 
                ("B) Scepticism.", 30), 
                ("C) Curiozitate.", 70), 
                ("D) Entuziasm. Lucrurile deveniseră plictisitoare.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Rezolvare Probleme/Obiceiuri) ---
        (
            "Când trebuie să rezolvi o problemă, cauți în manual/istoric cum s-a mai făcut sau încerci o abordare proprie?",
            "Problem Solving, Creativity, Protocol", 
            2, 
            [
                ("A) Fac exact cum scrie la carte.", 0), 
                ("B) Mă inspir din trecut.", 30), 
                ("C) Combin metode vechi cu idei noi.", 70), 
                ("D) Inventez o soluție nouă. 'Vechi' înseamnă 'depășit'.", 100)
            ]
        ),
        (
            "Ce părere ai despre zicala: 'Dacă nu e stricat, nu-l repara'?",
            "Philosophy, Maintenance vs Innovation", 
            2, 
            [
                ("A) Este regula mea de aur.", 0), 
                ("B) E un sfat bun de cele mai multe ori.", 30), 
                ("C) E limitativă. Putem îmbunătăți orice.", 70), 
                ("D) Falsă. Trebuie să inovăm înainte să se strice.", 100)
            ]
        ),
        (
            "Cât de des îți schimbi rutina zilnică, traseul spre muncă sau dieta?",
            "Routine, Flexibility, Habit", 
            2, 
            [
                ("A) Niciodată. Am tabieturile mele sfinte.", 0), 
                ("B) Rar.", 30), 
                ("C) Destul de des, ca să nu mă plictisesc.", 70), 
                ("D) Constant. Urăsc să fac două zile la fel.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Uncoachable / Rigiditate / Haos) ---
        (
            "Ai tendința să contești autoritatea sau tradițiile doar pentru că ți se par învechite?",
            "Rebellion, Authority, Tradition", 
            3, 
            [
                ("A) Nu, respect ierarhia și tradiția.", 0), 
                ("B) Doar dacă sunt absurde.", 30), 
                ("C) Da, pun multe întrebări incomode.", 70), 
                ("D) Da, vreau să dărâm sistemul vechi și să construiesc altul.", 100)
            ]
        ),
        (
            "Te simți confortabil în situații de incertitudine și haos, unde regulile se schimbă din mers?",
            "Chaos Tolerance, Uncertainty", 
            3, 
            [
                ("A) Nu, mă panichez. Vreau claritate.", 0), 
                ("B) Mă stresez, dar fac față.", 30), 
                ("C) Mă adaptez rapid.", 70), 
                ("D) Da, în haos găsesc oportunități. Mă plictisesc când e liniște.", 100)
            ]
        ),
        (
            "Ești dispus să îți asumi riscul de a strica ceva ce funcționează, doar pentru șansa de a-l face mult mai bun?",
            "Risk, Innovation, Optimization", 
            3, 
            [
                ("A) Nu. Siguranța primează.", 0), 
                ("B) Doar dacă riscul e mic.", 30), 
                ("C) Da, progresul cere sacrificii.", 70), 
                ("D) Absolut. Fără risc nu există inovație.", 100)
            ]
        ),
        (
            "Cum privești trecutul și 'vremurile bune de altădată'?",
            "Nostalgia vs Future", 
            3, 
            [
                ("A) Cu nostalgie. Era mai bine înainte.", 0), 
                ("B) Aveau farmecul lor.", 30), 
                ("C) Trecutul e o lecție, viitorul e scopul.", 70), 
                ("D) Nu mă uit înapoi. Viitorul e singurul care contează.", 100)
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