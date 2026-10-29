import sqlite3
import os
import sys

# Setup căi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def populate_synergies():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", "Injectăm Sinergiile Complete (Reguli de Activare Monștri)...")

    # Format: (Monster_ID, Trigger_Axis_ID, Operator, Threshold, Group_ID)
    # Group_ID leagă condițiile între ele (AND logic).
    
    rules_data = [
        # --- 51. MACHIAVELISM (Manipulare) ---
        (51, 1, '<', 30, 51),   # Sinceritate foarte mică
        (51, 13, '<', 30, 51),  # Empatie redusă
        
        # --- 52. NARCISISM (Grandiozitate) ---
        (52, 4, '<', 20, 52),   # Modestie foarte mică (Aroganță)
        (52, 14, '>', 75, 52),  # Asertivitate/Dominanță mare
        
        # --- 53. PSIHOPATIE (Răceală/Impulsivitate) ---
        (53, 20, '<', 20, 53),  # Blândețe foarte mică (Duritate)
        (53, 11, '>', 70, 53),  # Impulsivitate mare
        
        # --- 58. SOMATIZARE (Ipohondrie) ---
        (58, 6, '>', 70, 58),   # Anxietate mare
        (58, 36, '>', 70, 58),  # Vulnerabilitate la stres mare
        
        # --- 59. GÂNDIRE BIZARĂ (Schizotipie) ---
        (59, 32, '>', 80, 59),  # Fantezie foarte mare
        (59, 40, '<', 40, 59),  # Raționament/Gândire concretă (posibilă confuzie)
        
        # --- 60. COMPORTAMENT ANTISOCIAL ---
        (60, 43, '<', 25, 60),  # Respectare Reguli foarte mică
        (60, 2, '<', 25, 60),   # Corectitudine foarte mică
        
        # --- 68. DEMORALIZARE (Disperare) ---
        (68, 9, '>', 75, 68),   # Depresie mare
        (68, 35, '<', 25, 68),  # Optimism foarte mic
        
        # --- 69. CINISM (Mizantropie) ---
        (69, 23, '<', 25, 69),  # Încredere în oameni foarte mică
        (69, 45, '>', 70, 69),  # Vigilență/Suspiciune mare
        
        # --- 74. ANHEDONIE (Lipsă plăcere) ---
        (74, 16, '<', 20, 74),  # Vivacitate/Energie foarte mică
        (74, 17, '<', 20, 74),  # Căutarea senzațiilor foarte mică
        
        # --- 75. ALEXITIMIE (Orbire Emoțională) ---
        (75, 38, '<', 20, 75),  # Receptivitate Emoțională foarte mică
        (75, 54, '<', 30, 75),  # Percepție Emoțională mică
        
        # --- 76. DEZINHIBIȚIE (Lipsă de frână) ---
        (76, 11, '>', 80, 76),  # Impulsivitate extremă
        (76, 27, '<', 20, 76),  # Prudență foarte mică
        
        # --- 77. BURNOUT (Epuizare) ---
        (77, 16, '<', 25, 77),  # Vivacitate/Energie mică
        (77, 36, '>', 75, 77),  # Vulnerabilitate la stres mare
        
        # --- 78. DEPERSONALIZARE (Detașare) ---
        (78, 8, '<', 20, 78),   # Sentimentalism foarte mic (Răceală)
        (78, 85, '>', 60, 78),  # Disociere (dacă există în screening, altfel Fantezie mare)
        
        # --- 84. SADISM COTIDIAN ---
        (84, 13, '<', 15, 84),  # Empatie extrem de mică
        (84, 37, '>', 70, 84),  # Ostilitate mare
        
        # --- 85. DISOCIERE ---
        (85, 32, '>', 85, 85),  # Fantezie extremă
        (85, 16, '<', 30, 85),  # Focus/Atenție mică
        
        # --- 89. AGRESIVITATE ---
        (89, 37, '>', 75, 89),  # Ostilitate foarte mare
        (89, 12, '<', 25, 89),  # Răbdare foarte mică
        
        # --- 90. INTEGRITATE (Risc Fraudă) ---
        (90, 2, '<', 30, 90),   # Corectitudine mică
        (90, 3, '<', 30, 90),   # Evitarea Lăcomiei mică (adică e Lacom)
        
        # --- 91. HĂRȚUIRE (Boundaries) ---
        # Notă: Fără Libido în screening, folosim Impulsivitate + Dominanță
        (91, 11, '>', 75, 91),  # Impulsivitate mare
        (91, 14, '>', 70, 91),  # Dominanță mare (Abuz de putere)
        (91, 20, '<', 30, 91),  # Blândețe mică (Insensibil)
        
        # --- 92. NEGLIJENȚĂ (Safety Risk) ---
        (92, 24, '<', 25, 92),  # Organizare mică
        (92, 29, '<', 30, 92),  # Simțul Datoriei mic
        
        # --- 93. UNCOACHABLE (Refractar) ---
        (93, 14, '>', 75, 93),  # Dominanță mare
        (93, 50, '<', 25, 93),  # Deschidere la Schimbare mică
        
        # --- 94. SABOTOR (Politică de birou) ---
        (94, 1, '<', 30, 94),   # Sinceritate mică
        (94, 41, '>', 70, 94),  # Diplomație/Secretomanie mare
        
        # --- 95. LOAFING (Chiul) ---
        (95, 25, '<', 30, 95),  # Hărnicie mică
        (95, 7, '>', 70, 95),   # Dependență mare (se ascunde după grup)
        
        # --- 96. MALICIOUS (Răzbunător) ---
        (96, 19, '<', 20, 96),  # Iertare foarte mică (Ranchiunos)
        (96, 37, '>', 60, 96),  # Ostilitate
        
        # --- 97. FLIGHT RISK (Mercenar) ---
        (97, 86, '>', 80, 97),  # Motivație Financiară mare
        (97, 29, '<', 35, 97),  # Loialitate/Datorie mică
        
        # --- 98. VICTIMIZARE ---
        (98, 65, '<', 30, 98),  # Locus of Control Extern (Soarta e de vină)
        (98, 9, '>', 60, 98),   # Depresie/Tristețe
        
        # --- 99. DEZIRABILITATE (Minciună) ---
        # Trigger dacă e "Prea bun ca să fie adevărat"
        (99, 1, '>', 90, 99),   # Sinceritate declarată extremă
        (99, 2, '>', 90, 99),   # Corectitudine declarată extremă
        
        # --- 100. MICROMANAGEMENT ---
        (100, 26, '>', 80, 100), # Perfecționism mare
        (100, 23, '<', 30, 100), # Încredere în oameni mică
        
        # --- 101. SINDROM IMPOSTOR ---
        (101, 26, '>', 75, 101), # Perfecționism mare
        (101, 6, '>', 75, 101),  # Anxietate mare
        
        # --- 102. YES-MAN (Submisiv) ---
        (102, 39, '>', 80, 102), # Conciliere/Supunere mare
        (102, 14, '<', 20, 102)  # Asertivitate mică
    ]

    try:
        # Ștergem regulile vechi pentru a evita duplicatele
        c.execute("DELETE FROM synergy_rules")
        
        # Inserăm regulile noi
        c.executemany("""
            INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold, group_id)
            VALUES (?, ?, ?, ?, ?)
        """, rules_data)
        
        conn.commit()
        log("db_conn", f"SUCCES: {len(rules_data)} reguli de sinergie injectate pentru 29 monștri.")
        
    except Exception as e:
        log_error("Eroare la popularea regulilor", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_synergies()