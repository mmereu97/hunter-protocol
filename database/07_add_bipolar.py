import sqlite3
import os
import sys

# Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def install_bipolar():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error("Baza de date lipsește.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", "INSTALARE AXA 108: TULBURARE BIPOLARĂ...")

    try:
        # 1. INSERARE AXĂ
        # ID 108
        # Medie 15, Deviație 10 (Foarte rară statistic)
        c.execute("""
            INSERT OR REPLACE INTO axes 
            (id, name, left_pole, right_pole, category, source_system, norm_mean, norm_std_dev)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (108, "Tulburare Bipolară (Manie)", "Stabil / Eutimic", "Ciclic / Maniacal", "Monster", "MDQ / DSM-5", 15, 10))
        
        # 2. INSERARE REGULI SINERGIE
        # Trigger: Dacă ești foarte Energic (Vivacitate > 80) ȘI foarte Impulsiv (> 80),
        # există riscul de comportament maniacal.
        
        # Curățăm reguli vechi pt 108
        c.execute("DELETE FROM synergy_rules WHERE monster_axis_id = 108")
        
        rules = [
            (108, 16, '>', 80), # Vivacitate / Energie
            (108, 11, '>', 80), # Impulsivitate
            (108, 17, '>', 75)  # Căutarea Senzațiilor
        ]

        for r in rules:
            c.execute("""
                INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold, group_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (r[0], r[1], r[2], r[3], 108))
        
        conn.commit()
        log("db_conn", "Axa 108 și regulile activate.")

    except Exception as e:
        log_error("Eroare instalare Bipolar", e)
    finally:
        conn.close()

if __name__ == "__main__":
    install_bipolar()