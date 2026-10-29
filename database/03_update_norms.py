import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def update_norms():
    db_path = Config.DB_NAME
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", "Actualizăm Normele Psihometrice (Final 102)...")

    # HARTA FINALĂ A NORMELOR (Mean, StdDev)
    # Valorile reflectă populația generală.
    # Monștrii au medii mici. Trăsăturile dezirabile au medii mari.
    
    ALL_NORMS = {
        # --- HEXACO CORE (1-8) ---
        1:  (65, 15), # Sinceritate
        2:  (60, 15), # Corectitudine
        3:  (55, 15), # Evitare Lăcomie
        4:  (50, 15), # Modestie
        5:  (45, 18), # Frică Fizică
        6:  (45, 18), # Anxietate
        7:  (50, 15), # Dependență
        8:  (55, 15), # Sentimentalism

        # --- NEVROTISM & EXTRAVERSIE (9-18) ---
        9:  (30, 15), # Depresie (Normal e să NU fii deprimat)
        10: (40, 15), # Timiditate
        11: (45, 18), # Impulsivitate
        12: (50, 15), # Răbdare
        13: (55, 15), # Stimă Sine
        14: (50, 15), # Asertivitate
        15: (50, 18), # Sociabilitate
        16: (55, 20), # Vivacitate
        17: (40, 18), # Căutare Senzații
        18: (55, 15), # Căldură

        # --- AGREABILITATE (19-23) ---
        19: (50, 15), # Iertare
        20: (55, 15), # Blândețe
        21: (50, 15), # Flexibilitate
        22: (60, 15), # Altruism
        23: (50, 15), # Încredere

        # --- CONȘTIINCIOZITATE (24-29) ---
        24: (55, 15), # Organizare
        25: (50, 20), # Disciplină
        26: (55, 15), # Competență
        27: (50, 15), # Prudență
        28: (55, 18), # Realizare
        29: (60, 15), # Datorie

        # --- DESCHIDERE & MIX (30-50) ---
        30: (50, 20), # Estetică
        31: (55, 15), # Curiozitate
        32: (45, 20), # Fantezie
        33: (40, 15), # Valori
        34: (45, 15), # Acțiuni
        35: (60, 15), # Optimism
        36: (40, 18), # Stres
        37: (35, 18), # Ostilitate
        38: (50, 15), # Receptivitate Emo
        39: (50, 15), # Conciliere
        40: (50, 15), # IQ
        41: (45, 15), # Diplomație
        42: (45, 15), # Dominanță Agresivă
        43: (55, 15), # Reguli
        44: (50, 20), # Artistic
        45: (45, 15), # Vigilență
        46: (40, 20), # Visare
        47: (40, 18), # Îngrijorare
        48: (50, 15), # Auto-suficiență
        49: (40, 18), # Tensiune
        50: (45, 15), # Schimbare

        # --- MONȘTRI & RISCURI (Medii Mici!) ---
        51: (25, 15), # Machiavelism
        52: (30, 15), # Narcisism
        53: (15, 10), # Psihopatie
        58: (20, 15), # Somatizare
        59: (10, 10), # Gândire Bizară
        60: (15, 15), # Antisocial
        68: (20, 15), # Demoralizare
        69: (30, 15), # Cinism
        74: (15, 10), # Anhedonie
        75: (20, 15), # Alexitimie
        76: (30, 15), # Dezinhibiție
        77: (35, 20), # Burnout
        78: (15, 10), # Depersonalizare
        84: (10, 10), # Sadism
        85: (20, 15), # Disociere
        
        # --- MONȘTRI COMPORTAMENTALI ---
        89: (20, 15), # Agresivitate
        90: (20, 15), # Fraudă
        91: (15, 10), # Hărțuire
        92: (25, 15), # Neglijență
        93: (30, 15), # Uncoachable
        94: (20, 15), # Sabotor
        95: (25, 15), # Loafing
        96: (15, 10), # Malicious
        97: (30, 20), # Flight Risk
        98: (30, 15), # Victimizare
        99: (35, 15), # Minciună (Dezirabilitate)
        100:(30, 15), # Micromanagement
        101:(45, 20), # Impostor
        102:(40, 18), # Yes-Man

        # --- CARIERĂ & EQ & BIO (54-57, 61-67, 70-88) ---
        54: (50, 15), 55: (45, 15), 56: (50, 15), 57: (50, 15),
        61: (50, 20), 62: (50, 20), 63: (50, 20), 64: (50, 20),
        65: (50, 15), # Locus
        66: (50, 15), 67: (50, 18),
        70: (35, 15), 71: (30, 15), # Dating
        72: (50, 15), 73: (60, 15),
        79: (45, 20), 80: (20, 15), 81: (60, 20), 82: (50, 20), 83: (40, 18),
        86: (55, 20), 87: (50, 20), 88: (50, 20)
    }

    try:
        count = 0
        for axis_id, (mean, sd) in ALL_NORMS.items():
            c.execute("UPDATE axes SET norm_mean=?, norm_std_dev=? WHERE id=?", (mean, sd, axis_id))
            count += 1
        
        conn.commit()
        log("db_conn", f"Norme actualizate pentru {count} axe.")
        
    except Exception as e:
        log_error("Eroare update norme", e)
    finally:
        conn.close()

if __name__ == "__main__":
    update_norms()