import sqlite3
from config import Config

def migrate_to_dual_filter_logic():
    conn = sqlite3.connect(Config.DB_NAME)
    c = conn.cursor()
    # Adăugăm coloanele pentru pragurile de abatere de la medie
    try:
        c.execute("ALTER TABLE exam_strategies ADD COLUMN dev_threshold_minor REAL DEFAULT 20.0")
        c.execute("ALTER TABLE exam_strategies ADD COLUMN dev_threshold_major REAL DEFAULT 30.0")
    except: pass # Coloanele există deja
    conn.commit()
    conn.close()

migrate_to_dual_filter_logic()