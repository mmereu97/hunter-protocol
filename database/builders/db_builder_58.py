import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# DEFINIȚII
AXIS_ID = 58
AXIS_NAME = "Somatizare"
# Pol 0: Sănătos / Rezilient
# Pol 100: Ipohondru / Somatizare / Dureri

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm Clinicul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = SOMATIZARE (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Simptome Generale) ---
        (
            "Cât de des ai dureri de cap, de stomac sau stări de rău fără o cauză medicală clară?",
            "Physical Symptoms, Frequency", 
            1, 
            [
                ("A) Foarte rar sau niciodată.", 0), 
                ("B) Ocazional, la oboseală.", 30), 
                ("C) Destul de des (săptămânal).", 70), 
                ("D) Aproape zilnic. Mereu mă doare ceva.", 100)
            ]
        ),
        (
            "Când treci printr-o perioadă stresantă, cum reacționează corpul tău?",
            "Stress Response, Body", 
            1, 
            [
                ("A) Rezist bine, nu am simptome fizice.", 0), 
                ("B) Dorm puțin mai prost.", 30), 
                ("C) Îmi scade imunitatea sau am tensiune musculară.", 60), 
                ("D) Mă îmbolnăvesc imediat (migrene, greață, dureri).", 100)
            ]
        ),
        (
            "Cât de des te îngrijorezi că ai putea avea o boală gravă, chiar dacă medicii spun că ești ok?",
            "Hypochondria, Health Anxiety", 
            1, 
            [
                ("A) Niciodată. Am încredere în medici.", 0), 
                ("B) Rar, doar dacă am simptome ciudate.", 30), 
                ("C) Uneori caut simptome pe Google și mă sperii.", 70), 
                ("D) Foarte des. Sunt convins că am ceva ce ei nu găsesc.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Impact Funcțional) ---
        (
            "Ți se întâmplă să îți anulezi planurile sau să nu mergi la muncă din cauza unor stări de rău vagi?",
            "Functional Impairment, Avoidance", 
            2, 
            [
                ("A) Nu, merg și bolnav dacă trebuie.", 0), 
                ("B) Doar dacă am febră sau ceva contagios.", 20), 
                ("C) Uneori, când nu mă simt în apele mele.", 60), 
                ("D) Da, des. Nu pot funcționa când mă simt rău.", 100)
            ]
        ),
        (
            "Simți des o senzație de 'nod în gât', presiune în piept sau dificultăți de respirație când ești emoționat?",
            "Panic Symptoms, Psychosomatic", 
            2, 
            [
                ("A) Nu.", 0), 
                ("B) Rar, la emoții extreme.", 30), 
                ("C) Da, mi se întâmplă în situații tensionate.", 70), 
                ("D) Da, e o senzație constantă care mă sufocă.", 100)
            ]
        ),
        (
            "Cât de mult timp petreci discutând despre sănătatea ta sau simptomele tale cu alții?",
            "Health Focus, Conversations", 
            2, 
            [
                ("A) Deloc. Urăsc să mă plâng.", 0), 
                ("B) Doar dacă e ceva serios.", 30), 
                ("C) Menționez dacă mă întreabă.", 60), 
                ("D) Mult. Este subiectul meu principal de discuție.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Conversie / Obsesie) ---
        (
            "Ai avut vreodată o pierdere bruscă a unei funcții fizice (ex: voce, vedere, mișcare mână) după un șoc emoțional?",
            "Conversion Disorder, Trauma", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Nu.", 0), 
                ("C) Am avut amețeli puternice.", 60), 
                ("D) Da, am pățit să nu mai pot vorbi sau merge temporar.", 100)
            ]
        ),
        (
            "Ești sensibil la schimbările de vreme, mirosuri sau zgomote până la punctul în care ți se face rău fizic?",
            "HSP, Physical Sensitivity", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Mă deranjează, dar nu mă îmbolnăvesc.", 30), 
                ("C) Da, am migrene de la vreme/mirosuri.", 70), 
                ("D) Da, sunt extrem de fragil fizic la orice stimul.", 100)
            ]
        ),
        (
            "Consideri că ești o persoană 'bolnăvicioasă' sau cu o constituție slabă?",
            "Self-Image, Health Identity", 
            3, 
            [
                ("A) Nu, sunt sănătos tun.", 0), 
                ("B) Sunt mediu.", 30), 
                ("C) Sunt mai sensibil decât alții.", 70), 
                ("D) Da, am avut probleme de sănătate toată viața.", 100)
            ]
        ),
        (
            "Dacă ai o durere, iei medicamente imediat sau aștepți să treacă?",
            "Medication, Pain Tolerance", 
            3, 
            [
                ("A) Aștept să treacă, evit pastilele.", 0), 
                ("B) Iau doar dacă e insuportabil.", 30), 
                ("C) Iau ceva ca să nu mă chinui.", 60), 
                ("D) Iau preventiv sau la primul semn. Nu suport durerea.", 100)
            ]
        )
    ]

    try:
        # CLEANUP & INSERT
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
        log("db_conn", f"SUCCES: {len(questions_data)} întrebări inserate pentru {AXIS_NAME}.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()