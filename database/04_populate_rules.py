import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def populate_synergies():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error("Baza de date lipsește.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", "Injectăm 'Rețetele Monștrilor' CORECTATE (New IDs)...")

    # Format: (Monster_ID, Trigger_Axis_ID, Operator, Threshold)
    
    rules_data = [
        # --- 1. AGRESIVITATE (ID 89) ---
        (89, 37, '>', 70),  # Ostilitate (37) > 70
        (89, 12, '<', 30),  # Răbdare (12) < 30
        
        # --- 2. INTEGRITATE / FRAUDĂ (ID 90) ---
        (90, 2,  '<', 30),  # Corectitudine (2) < 30
        (90, 3,  '<', 30),  # Evitarea Lăcomiei (3) < 30 (Lacom)
        (90, 51, '>', 60),  # Machiavelism (51) > 60
        
        # --- 3. HĂRȚUIRE (ID 91) ---
        (91, 11, '>', 70),  # Impulsivitate (11) > 70
        (91, 4,  '<', 20),  # Modestie (4) < 20
        (91, 20, '<', 30),  # Blândețe (20) < 30
        
        # --- 4. NEGLIJENȚĂ (ID 92) ---
        (92, 24, '<', 25),  # Organizare (24) < 25
        (92, 29, '<', 30),  # Simțul Datoriei (29) < 30
        (92, 5,  '<', 30),  # Frică Fizică (5) < 30
        
        # --- 5. UNCOACHABLE (ID 93) ---
        (93, 52, '>', 65),  # Narcisism (52) > 65
        (93, 50, '<', 30),  # Deschidere la Schimbare (50) < 30
        (93, 4,  '<', 30),  # Modestie (4) < 30
        
        # --- 6. SABOTOR (ID 94) ---
        (94, 51, '>', 65),  # Machiavelism (51) > 65
        (94, 18, '>', 60),  # Căldură Umană (18) > 60 (Farmec superficial)
        (94, 1,  '<', 30),  # Sinceritate (1) < 30
        
        # --- 7. LOAFING / CHIUL (ID 95) ---
        (95, 25, '<', 30),  # Auto-disciplină/Hărnicie (25) < 30
        (95, 7,  '>', 70),  # Dependență (7) > 70
        (95, 16, '<', 30),  # Vivacitate (16) < 30
        
        # --- 8. MALICIOUS (ID 96) ---
        (96, 84, '>', 50),  # Sadism (84) > 50
        (96, 19, '<', 20),  # Iertare (19) < 20
        (96, 13, '<', 20),  # Empatie (13) < 20
        
        # --- 9. FLIGHT RISK (ID 97) ---
        (97, 86, '>', 80),  # Motivație Financiară (86) > 80
        (97, 29, '<', 30),  # Simțul Datoriei (29) < 30
        (97, 34, '>', 70),  # Deschidere la Acțiuni (34) > 70 (Plictiseală)
        
        # --- 10. VICTIMIZARE (ID 98) ---
        (98, 65, '<', 25),  # Locus of Control (65) < 25 (Extern)
        (98, 28, '>', 70),  # Nevrotism General (28) > 70
        
        # --- 11. MICROMANAGEMENT (ID 100) ---
        (100, 26, '>', 80), # Competență/Perfecționism (26) > 80
        (100, 23, '<', 30), # Încredere în oameni (23) < 30
        
        # --- 12. SINDROM IMPOSTOR (ID 101) ---
        (101, 26, '>', 70), # Competență/Perfecționism (26) > 70
        (101, 6,  '>', 70), # Anxietate (6) > 70
        
        # --- 13. YES-MAN (ID 102) ---
        (102, 12, '>', 80), # Răbdare (12) > 80
        (102, 14, '<', 20)  # Asertivitate (14) < 20
    ]

    try:
        c.execute("DELETE FROM synergy_rules") # Curățare
        
        c.executemany("""
            INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold)
            VALUES (?, ?, ?, ?)
        """, rules_data)
        
        conn.commit()
        log("db_conn", f"Succes: {len(rules_data)} reguli de sinergie actualizate pe noile ID-uri.")
        
    except Exception as e:
        log_error("Eroare populate rules", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_synergies()