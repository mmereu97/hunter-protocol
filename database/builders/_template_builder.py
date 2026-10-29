import sqlite3
import hashlib
import json
import os
import sys

# ==============================================================================
# 1. ZONA DE CONFIGURARE (MODIFICĂ DOAR AICI)
# ==============================================================================

# ID-ul Axei din baza de date (ex: 51 pentru Machiavelism)
AXIS_ID = 1  
AXIS_NAME = "Sinceritate" 

# LISTA DE ÎNTREBĂRI
# Format: (Textul Întrebării, Tag-uri AI, Valul (1/2/3), [Lista Opțiuni])
# Opțiuni: [("A) Text", Scor), ("B) Text", Scor)...]
# Scoruri uzuale: 0 (Stânga), 30, 70, 100 (Dreapta)

questions_data = [
    # --- VALUL 1 (SCREENING - 3 Întrebări) ---
    (
        "Întrebarea 1 aici...", 
        "Tag1, Tag2", 
        1, 
        [("A) Răspuns Stânga", 0), ("B) Răspuns Mediu-Stg", 30), ("C) Răspuns Mediu-Dr", 70), ("D) Răspuns Dreapta", 100)]
    ),
    (
        "Întrebarea 2 aici...", 
        "Tag1, Tag2", 
        1, 
        [("A) ...", 0), ("B) ...", 30), ("C) ...", 70), ("D) ...", 100)]
    ),
    (
        "Întrebarea 3 aici...", 
        "Tag1, Tag2", 
        1, 
        [("A) ...", 0), ("B) ...", 30), ("C) ...", 70), ("D) ...", 100)]
    ),

    # --- VALUL 2 (CONFIRMARE - 3 Întrebări) ---
    (
        "Întrebarea 4 (Mai directă)...", 
        "Context Specific", 
        2, 
        [("A) ...", 0), ("B) ...", 30), ("C) ...", 70), ("D) ...", 100)]
    ),
    # ... adaugă restul până la 10
]

# ==============================================================================
# 2. MOTORUL DE INSERARE (NU MODIFICA NIMIC MAI JOS)
# ==============================================================================

# Setup Căi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def generate_hash(text, options_list):
    """Generează amprenta unică pentru Time Machine."""
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def run_script():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există la: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", f"🚀 Populăm Axa {AXIS_ID}: {AXIS_NAME}...")

    try:
        # 1. Curățăm întrebările vechi ale acestei axe (doar versiunile curente)
        # Identificăm hash-urile existente pentru a șterge opțiunile orfane
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"Curățat date vechi pentru Axa {AXIS_ID}.")

        # 2. Inserăm noile întrebări
        count = 0
        for q_text, tags, wave, opts in questions_data:
            v_hash = generate_hash(q_text, opts)
            
            # Header
            c.execute("""
                INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (AXIS_ID, v_hash, q_text, tags, wave))
            
            # Options
            labels = ['A', 'B', 'C', 'D']
            for idx, (opt_text, score) in enumerate(opts):
                c.execute("""
                    INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                    VALUES (?, ?, ?, ?)
                """, (v_hash, labels[idx], opt_text, score))
            count += 1

        conn.commit()
        log("db_conn", f"✅ SUCCES: {count} întrebări inserate pentru {AXIS_NAME}.")

    except Exception as e:
        log_error(f"❌ Eroare la popularea Axei {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    run_script()