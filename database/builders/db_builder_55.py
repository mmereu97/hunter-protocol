import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 55
AXIS_NAME = "Interes Întreprinzător (RIASEC E)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = ÎNTREPRINZĂTOR (SALES/LEADER)
    questions_data = [
        # --- VALUL 1: SCREENING (Persuasiune / Influență) ---
        (
            "Cât de confortabil te simți să încerci să convingi pe cineva să îți adopte punctul de vedere sau să cumpere ceva?",
            "Persuasion, Sales, Influence", 1, 
            [
                ("A) Foarte inconfortabil. Nu îmi place să insist.", 0), 
                ("B) Prefer să prezint faptele și să îi las să decidă.", 30), 
                ("C) Mă descurc bine dacă cred în idee.", 70), 
                ("D) Ador asta! Vânzarea este un joc pe care îl câștig.", 100)
            ]
        ),
        (
            "Te vezi mai degrabă într-un rol de execuție tehnică sau într-un rol de coordonare și management?",
            "Career, Role Preference", 1, 
            [
                ("A) Execuție. Vreau să îmi fac treaba liniștit.", 0), 
                ("B) Execuție, dar cu autonomie.", 30), 
                ("C) Coordonare de echipă mică.", 60), 
                ("D) Management și strategie. Vreau să conduc 'the big picture'.", 100)
            ]
        ),
        (
            "Ce te motivează mai mult la un proiect: procesul de lucru sau rezultatul final (câștigul/succesul)?",
            "Motivation, Results Oriented", 1, 
            [
                ("A) Procesul. Îmi place să lucrez corect.", 0), 
                ("B) Echilibrat.", 30), 
                ("C) Rezultatul e important.", 70), 
                ("D) Câștigul și succesul. Restul sunt detalii.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Business / Risc / Inițiativă) ---
        (
            "Ai fi dispus să îți pornești propria afacere, asumându-ți riscul financiar?",
            "Entrepreneurship, Risk", 2, 
            [
                ("A) Nu, am nevoie de siguranța unui salariu.", 0), 
                ("B) Poate ceva mic, pe lângă job.", 30), 
                ("C) Da, este un obiectiv de-al meu.", 70), 
                ("D) Da, deja am încercat sau o voi face. Nu pot fi angajat toată viața.", 100)
            ]
        ),
        (
            "Cum reacționezi într-o negociere (salariu, contract, preț)?",
            "Negotiation, Conflict", 2, 
            [
                ("A) Accept prima ofertă rezonabilă, evit tensiunea.", 0), 
                ("B) Negociez puțin, timid.", 30), 
                ("C) Mă pregătesc și cer ce merit.", 70), 
                ("D) Sunt dur și strategic. Vreau cel mai bun deal posibil.", 100)
            ]
        ),
        (
            "Îți place să vorbești în public sau să ții prezentări pentru a 'vinde' o idee?",
            "Public Speaking, Charisma", 2, 
            [
                ("A) Groaznic. Am trac.", 0), 
                ("B) O fac dacă trebuie.", 30), 
                ("C) Îmi place moderat.", 70), 
                ("D) Da, scena e a mea. Mă simt energizat.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Ambiție Extremă / Machiavelism) ---
        (
            "Cât de importantă este puterea și influența socială pentru tine?",
            "Power, Status, Ambition", 3, 
            [
                ("A) Deloc. Vreau doar o viață simplă.", 0), 
                ("B) Puțin importantă.", 20), 
                ("C) E un indicator al succesului.", 60), 
                ("D) Esențială. Vreau să fiu cineva care contează și decide.", 100)
            ]
        ),
        (
            "Crezi că ești capabil să vinzi 'gheață eschimoșilor' (să convingi pe oricine de orice)?",
            "Manipulation, Sales Skill, Confidence", 3, 
            [
                ("A) Nu, și nici nu aș vrea să păcălesc lumea.", 0), 
                ("B) Nu cred.", 20), 
                ("C) Pot fi foarte convingător.", 70), 
                ("D) Da. Totul ține de cum prezinți povestea.", 100)
            ]
        ),
        (
            "Te deranjează să fii într-o poziție subalternă unde trebuie să execuți ordine fără să le discuți?",
            "Insubordination, Independence", 3, 
            [
                ("A) Nu, e relaxant să nu am responsabilitatea deciziei.", 0), 
                ("B) Dacă șeful e bun, e ok.", 30), 
                ("C) Mă frustrează uneori.", 70), 
                ("D) Da, urăsc să am șef. Vreau să fiu propriul meu stăpân.", 100)
            ]
        ),
        (
            "Ești o persoană competitivă care vede viața ca pe o scară ce trebuie urcată?",
            "Competition, Career Ladder", 3, 
            [
                ("A) Nu, colaborarea e mai bună.", 0), 
                ("B) Sunt competitiv doar cu mine însumi.", 30), 
                ("C) Îmi place să avansez.", 70), 
                ("D) Da. Nu mă opresc până nu ajung în vârf.", 100)
            ]
        )
    ]

    try:
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))

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
        
        conn.commit()
        log("db_conn", f"SUCCES: Întrebări {AXIS_NAME} inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()