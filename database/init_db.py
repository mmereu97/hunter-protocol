import sqlite3
import os
import sys

# Hack pentru importuri
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from logger import log, log_error

def init_database():
    db_path = Config.DB_NAME
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            log("sys", f"♻️  Baza de date veche ștearsă: {db_path}")
        except PermissionError:
            log_error("Nu pot șterge baza. Închide PyCharm/DB Browser!")
            return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("db_conn", "Se construiește structura tabelelor (V3 Final)...")

    # 1. AXE (Cu toate coloanele necesare, inclusiv source_system)
    c.execute("""CREATE TABLE axes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        left_pole TEXT DEFAULT 'Low',
        right_pole TEXT DEFAULT 'High',
        category TEXT,
        description TEXT,
        source_system TEXT,          -- <--- COLOANA NOUĂ ADĂUGATĂ NATIV
        norm_mean INTEGER DEFAULT 50,    -- <--- COLOANA NORME
        norm_std_dev INTEGER DEFAULT 15, -- <--- COLOANA NORME
        is_custom BOOLEAN DEFAULT 0
    )""")

    # 2. BANCA DE ÎNTREBĂRI
    c.execute("""CREATE TABLE questions_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        axis_id INTEGER,
        version_hash TEXT UNIQUE NOT NULL,
        text_content TEXT,
        ai_tags TEXT,
        wave_target INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(axis_id) REFERENCES axes(id)
    )""")

    c.execute("""CREATE TABLE question_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_hash TEXT,
        option_index TEXT,
        text_content TEXT,
        score_value INTEGER,
        FOREIGN KEY(question_hash) REFERENCES questions_bank(version_hash)
    )""")

    # 3. REGULI SINERGIE
    c.execute("""CREATE TABLE synergy_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monster_axis_id INTEGER,
        trigger_axis_id INTEGER,
        operator TEXT,
        threshold INTEGER,
        group_id INTEGER, 
        FOREIGN KEY(monster_axis_id) REFERENCES axes(id)
    )""")

    # 4. TEMPLATE-URI TESTE
    c.execute("""CREATE TABLE test_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        config_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # 5. PACIENȚI
    c.execute("""CREATE TABLE patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cnp_hash TEXT UNIQUE,
        full_name TEXT,
        age INTEGER,
        gender TEXT,
        occupation TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE holistic_knowledge (
        patient_id INTEGER,
        axis_id INTEGER,
        latest_score INTEGER,
        confidence INTEGER,
        last_updated_at DATETIME,
        source_session_id INTEGER,
        PRIMARY KEY (patient_id, axis_id)
    )""")

    # 6. SESIUNI & RĂSPUNSURI
    c.execute("""CREATE TABLE sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        template_id INTEGER,
        date_taken DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT
    )""")

    c.execute("""CREATE TABLE session_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        question_hash TEXT,
        axis_id INTEGER,
        answer_chosen TEXT,
        score_snapshot INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )""")

    c.execute("""CREATE TABLE session_results (
        session_id INTEGER,
        axis_id INTEGER,
        final_score INTEGER,
        confidence INTEGER,
        is_monster_triggered BOOLEAN DEFAULT 0,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )""")

    conn.commit()
    conn.close()
    log("sys", "DATABASE INITIALIZED SUCCESSFULLY (WITH ALL COLUMNS).")

if __name__ == "__main__":
    init_database()