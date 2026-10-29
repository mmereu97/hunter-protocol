import sqlite3
import os
import sys

# Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def install_clinical_pack():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error("Baza de date lipsește.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", "INSTALARE PACHET CLINIC (ID 103-107)...")

    # 1. INSERARE AXE NOI
    # ID, Nume, Stânga, Dreapta, Categorie, Sursă, Medie, Deviație
    new_axes = [
        (103, "ADHD (Disfuncție Executivă)", "Focusat / Executiv", "Dispersat / Hiperactiv", "Monster", "ASRS-v1.1", 25, 15),
        (104, "Autism (Spectru ASD)", "Empatic / Social", "Sistematic / Rigid", "Monster", "AQ Test", 20, 15),
        (105, "OCPD (Obsesiv-Compulsiv)", "Flexibil / Relaxat", "Rigid / Control Freak", "Monster", "DSM-5", 25, 15),
        (106, "BPD (Borderline)", "Stabil / Securizant", "Instabil / Intens", "Monster", "MSI-BPD", 15, 10),
        (107, "Anxietate Socială (Fobie)", "Dezinvolt / Relaxat", "Evitant / Terifiat", "Monster", "LSAS", 25, 15)
    ]

    try:
        c.executemany("""
            INSERT OR REPLACE INTO axes 
            (id, name, left_pole, right_pole, category, source_system, norm_mean, norm_std_dev)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, new_axes)
        log("db_conn", "Axele 103-107 adăugate.")

        # 2. INSERARE REGULI SINERGIE (Triggere Automate)
        # Format: (Monster, Trigger, Op, Val)
        new_rules = [
            # ADHD -> Focus Mic (16) + Organizare Mică (24)
            (103, 16, '<', 30),
            (103, 24, '<', 30),
            
            # ASD -> Sociabilitate Mică (15) + Sensibilitate Senzorială Mare (80)
            (104, 15, '<', 30),
            (104, 80, '>', 70),

            # OCPD -> Perfecționism Mare (26) + Flexibilitate Mică (21)
            (105, 26, '>', 80),
            (105, 21, '<', 25),

            # BPD -> Vulnerabilitate Mare (36) + Ostilitate Mare (37) + Depresie (9)
            (106, 36, '>', 75),
            (106, 37, '>', 70),

            # ANXIETATE SOCIALĂ -> Timiditate Mare (10) + Stimă Socială Mică (13)
            (107, 10, '>', 80),
            (107, 13, '<', 25)
        ]

        # Ștergem regulile vechi pt acești monștri (safety check)
        placeholders = ','.join(['?']*len(new_axes))
        ids = [x[0] for x in new_axes]
        c.execute(f"DELETE FROM synergy_rules WHERE monster_axis_id IN ({placeholders})", ids)

        # Inserăm regulile noi (Group ID = Monster ID pentru simplificare AND)
        for r in new_rules:
            # (monster, trigger, op, val, group_id)
            c.execute("INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold, group_id) VALUES (?, ?, ?, ?, ?)", 
                      (r[0], r[1], r[2], r[3], r[0]))
        
        conn.commit()
        log("db_conn", "Regulile de sinergie pentru 103-107 instalate.")

    except Exception as e:
        log_error("Eroare instalare pachet clinic", e)
    finally:
        conn.close()

if __name__ == "__main__":
    install_clinical_pack()