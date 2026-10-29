import sqlite3
import os
import sys

# Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def install_missing_axes():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error("Baza de date lipsește.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", "INSTALARE AXE LIPSA (MOBILITATE & FOCUS)...")

    try:
        # 1. DEFINIRE AXE NOI
        new_axes = [
            # ID 109: MOBILITATE
            (109, "Mobilitate (Stil de Viață)", "Sedentar / Stabil / Casnic", "Nomad / Dinamic / Călător", "Career", "Hunter V1", 40, 20),
            
            # ID 110: FOCUS (DEEP WORK)
            (110, "Stil de Atenție (Focus)", "Multitasking / Distributiv", "Deep Work / Focusat / Monahal", "Core", "Newport", 45, 15)
        ]

        c.executemany("""
            INSERT OR REPLACE INTO axes 
            (id, name, left_pole, right_pole, category, source_system, norm_mean, norm_std_dev)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, new_axes)
        
        # 2. ACTUALIZARE REGULI SINERGIE (OPȚIONAL)
        # Putem folosi noile axe pentru a rafina monștrii existenți.
        
        # A. Actualizăm FLIGHT RISK (ID 97)
        # Adăugăm: Dacă Mobilitate (109) > 80 => Risc de Plecare
        c.execute("""
            INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold, group_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (97, 109, '>', 80, 97))

        # B. Actualizăm ADHD (ID 103)
        # Adăugăm: Dacă Focus (110) < 20 => Risc ADHD
        c.execute("""
            INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold, group_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (103, 110, '<', 20, 103))

        conn.commit()
        log("db_conn", "Axele 109 și 110 au fost instalate și conectate la Sinergii.")

    except Exception as e:
        log_error("Eroare instalare axe lipsă", e)
    finally:
        conn.close()

if __name__ == "__main__":
    install_missing_axes()