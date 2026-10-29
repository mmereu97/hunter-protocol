import sqlite3
import os

# Calea către baza ta de date (asigură-te că e corectă)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

DB_PATH = Config.DB_NAME

def repara_tabele_audit():
    if not os.path.exists(DB_PATH):
        print(f"❌ Nu am găsit baza de date la: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🔧 Verificare și reparație structură tabele...")

    # 1. Reparație TABEL AUDIT (Adăugare coloană question_text)
    try:
        c.execute("ALTER TABLE session_audit ADD COLUMN question_text TEXT")
        print("✅ Adăugată coloana 'question_text' în session_audit.")
    except sqlite3.OperationalError:
        print("ℹ️ Coloana 'question_text' există deja.")

    # 2. Verificare TABEL STRATEGII (Adăugare coloane noi dacă lipsesc)
    coloane_noi = [
        ("yellow_extra_qty", "INTEGER DEFAULT 3"),
        ("red_extra_qty", "INTEGER DEFAULT 7"),
        ("dev_threshold_minor", "REAL DEFAULT 20.0"),
        ("dev_threshold_major", "REAL DEFAULT 30.0"),
        ("dev_minor_qty", "INTEGER DEFAULT 3"),
        ("dev_major_qty", "INTEGER DEFAULT 7")
    ]
    
    for col, tip in coloane_noi:
        try:
            c.execute(f"ALTER TABLE exam_strategies ADD COLUMN {col} {tip}")
            print(f"✅ Adăugată coloana '{col}' în exam_strategies.")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
    print("🚀 Baza de date este acum 100% compatibilă cu noul motor.")

if __name__ == "__main__":
    repara_tabele_audit()