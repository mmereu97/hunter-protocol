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
AXIS_ID = 26
AXIS_NAME = "Competență / Perfecționism"
# Pol Stânga (0): Pragmatic / Aproximativ / "Merge și așa"
# Pol Dreapta (100): Meticulos / Detaliist / Expert

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
    # Punctaj: 0 = Pragmatic (Neglijent), 100 = Perfecționist
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Detalii Mici) ---
        (
            "Când trimiți un email sau un mesaj text rapid, cât de mult contează corectitudinea gramaticală sau typos?",
            "Details, Grammar, Communication", 
            1, 
            [
                ("A) Deloc. Important e să se înțeleagă mesajul.", 0), 
                ("B) Nu verific, dar încerc să scriu corect.", 30), 
                ("C) Recitesc o dată înainte de a trimite.", 70), 
                ("D) Mă deranjează enorm orice greșeală, editez și virgulele.", 100)
            ]
        ),
        (
            "Cum te raportezi la principiul 'Mai bine făcut decât perfect' (Done is better than perfect)?",
            "Philosophy, Efficiency vs Quality", 
            1, 
            [
                ("A) Total de acord. Viteza contează.", 0), 
                ("B) De acord în majoritatea cazurilor.", 30), 
                ("C) Depinde, calitatea nu trebuie sacrificată.", 70), 
                ("D) Nu sunt de acord. Dacă nu e perfect, mai bine nu-l fac.", 100)
            ]
        ),
        (
            "Când faci o sarcină (curățenie, un document, o reparație), când te oprești?",
            "Standards, Work Ethic", 
            1, 
            [
                ("A) Când arată acceptabil ('merge și așa').", 0), 
                ("B) Când e funcțional.", 30), 
                ("C) Când arată bine și nu sunt erori vizibile.", 70), 
                ("D) Când e impecabil, verificat la microscop.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Standarde) ---
        (
            "Te deranjează vizibil dacă vezi un tablou strâmb pe perete sau o greșeală de aliniere într-un document?",
            "Symmetry, Order, Obsessive", 
            2, 
            [
                ("A) Nu observ astfel de detalii.", 0), 
                ("B) Observ, dar nu-mi pasă.", 30), 
                ("C) Mă deranjează puțin, poate îl îndrept.", 70), 
                ("D) Da, nu mă pot concentra la altceva până nu îl repar.", 100)
            ]
        ),
        (
            "Preferi să livrezi un proiect la timp cu mici erori sau să întârzii pentru a le corecta pe toate?",
            "Deadlines vs Quality, Priorities", 
            2, 
            [
                ("A) Livrez la timp, erorile se repară din mers.", 0), 
                ("B) Prioritizez termenul limită.", 30), 
                ("C) Prefer o mică întârziere pentru calitate.", 70), 
                ("D) Nu livrez nimic sub standardul meu, indiferent de întârziere.", 100)
            ]
        ),
        (
            "Cât de des verifici munca (double-check) înainte de a o considera finalizată?",
            "Verification, Diligence", 
            2, 
            [
                ("A) Niciodată. Am încredere că e ok.", 0), 
                ("B) O privire rapidă la final.", 30), 
                ("C) Verific punctele cheie.", 70), 
                ("D) Verific de 2-3 ori fiecare detaliu.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Micromanagement / OCPD / Sindrom Impostor) ---
        (
            "Ai tendința să refaci munca altora pentru că nu se ridică la standardele tale?",
            "Delegation, Control, Trust", 
            3, 
            [
                ("A) Nu, nu-mi pasă cum au făcut, e treaba lor.", 0), 
                ("B) Doar dacă e complet greșit.", 30), 
                ("C) Uneori mai retușez pe ici pe colo.", 70), 
                ("D) Da, des. Nimeni nu face lucrurile la fel de bine ca mine.", 100)
            ]
        ),
        (
            "Te blochezi adesea în detalii minore și pierzi din vedere imaginea de ansamblu (Analysis Paralysis)?",
            "Focus, Efficiency, Anxiety", 
            3, 
            [
                ("A) Nu, sunt omul de 'big picture'.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori insist prea mult pe detalii.", 60), 
                ("D) Da, mă consumă dorința de a face totul perfect.", 100)
            ]
        ),
        (
            "Cât de aspru te judeci pentru o greșeală minoră pe care nimeni altcineva nu a observat-o?",
            "Self-Criticism, Standards", 
            3, 
            [
                ("A) Deloc. Dacă nu s-a văzut, nu există.", 0), 
                ("B) Mă amuz și trec peste.", 30), 
                ("C) Mă enervează, dar îmi trece.", 70), 
                ("D) Mă obsedează. Știu că am greșit și nu-mi pot ierta neglijența.", 100)
            ]
        ),
        (
            "Crezi că există 'prea multă atenție la detalii'?",
            "Worldview, Philosophy", 
            3, 
            [
                ("A) Da, e pierdere de timp.", 0), 
                ("B) Da, când devine ineficient.", 30), 
                ("C) Rareori.", 70), 
                ("D) Nu. Detaliile fac diferența între mediocru și excelent.", 100)
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