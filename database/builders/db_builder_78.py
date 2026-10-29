import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# DEFINIȚII
AXIS_ID = 78
AXIS_NAME = "Depersonalizare"
# Pol 0: Prezent / Conectat
# Pol 100: Detașat / Ireal / Robot

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm Clinicul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = DEPERSONALIZARE (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Pilot Automat / Răceală) ---
        (
            "Cât de des ai senzația că funcționezi pe 'pilot automat', făcând lucrurile mecanic fără să fii prezent mental?",
            "Autopilot, Routine, Presence", 
            1, 
            [
                ("A) Rar. Sunt atent la ce fac.", 0), 
                ("B) Uneori, la sarcini repetitive.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Aproape tot timpul. Nu știu cum trece ziua.", 100)
            ]
        ),
        (
            "Când interacționezi cu oamenii (clienți, colegi), îi vezi ca pe persoane sau ca pe niște probleme/numere de rezolvat?",
            "Dehumanization, Cynicism, Work", 
            1, 
            [
                ("A) Ca pe persoane, empatizez cu ei.", 0), 
                ("B) Încerc să fiu profesionist.", 30), 
                ("C) Uneori devin doar niște task-uri enervante.", 70), 
                ("D) Sunt doar obiecte care mă deranjează. Nu simt nimic pentru ei.", 100)
            ]
        ),
        (
            "Te simți vreodată detașat de propriile emoții, ca și cum ai fi amorțit?",
            "Numbness, Emotion", 
            1, 
            [
                ("A) Nu, simt totul.", 0), 
                ("B) Doar când sunt foarte obosit.", 30), 
                ("C) Da, am perioade de 'ceață'.", 70), 
                ("D) Da. Nu mai simt nici bucurie, nici furie. Sunt gol.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Senzație de Irealitate) ---
        (
            "Ți se întâmplă să te uiți în oglindă și să ți se pară că persoana pe care o vezi e un străin?",
            "Mirror Sign, Dissociation", 
            2, 
            [
                ("A) Nu, mă recunosc.", 0), 
                ("B) Poate pentru o secundă, rar.", 20), 
                ("C) Uneori mi se pare ciudat.", 70), 
                ("D) Da, am des senzația că nu sunt eu.", 100)
            ]
        ),
        (
            "Ai momente în care ai impresia că ești un observator în afara corpului tău, privind ce faci?",
            "Out of Body, Observer Perspective", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Doar în vise.", 20), 
                ("C) Am avut senzația asta la stres mare.", 70), 
                ("D) Da, mă simt ca un spectator la propria viață.", 100)
            ]
        ),
        (
            "Vocea ta ți se pare vreodată străină sau distantă când vorbești?",
            "Auditory Dissociation", 
            2, 
            [
                ("A) Nu.", 0), 
                ("B) Doar dacă sunt răcit/obosit.", 20), 
                ("C) Uneori parcă vorbește altcineva prin mine.", 70), 
                ("D) Da, aud cuvintele dar nu simt că eu le spun.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Derealizare / Ruptură de Realitate) ---
        (
            "Lumea din jurul tău pare uneori falsă, plată, ca într-un decor de film sau un vis?",
            "Derealization, Reality Testing", 
            3, 
            [
                ("A) Nu, lumea e foarte reală.", 0), 
                ("B) Poate când sunt epuizat.", 20), 
                ("C) Uneori culorile sau formele par ciudate.", 70), 
                ("D) Da. Am senzația că trăiesc într-o simulare sau un vis.", 100)
            ]
        ),
        (
            "Simți că amintirile tale nu îți aparțin, ci sunt doar niște informații stocate?",
            "Memory, Ownership", 
            3, 
            [
                ("A) Nu, sunt amintirile mele vii.", 0), 
                ("B) Unele sunt mai șterse.", 30), 
                ("C) Parcă s-au întâmplat altcuiva.", 70), 
                ("D) Da, nu am nicio conexiune emoțională cu trecutul meu.", 100)
            ]
        ),
        (
            "Te simți ca un robot mecanic care execută mișcări fără voință proprie?",
            "Automatism, Loss of Agency", 
            3, 
            [
                ("A) Nu, eu decid ce fac.", 0), 
                ("B) Uneori intru în rutină.", 20), 
                ("C) Mă simt blocat.", 60), 
                ("D) Da. Mă mișc, vorbesc, dar nu e nimeni 'acasă'.", 100)
            ]
        ),
        (
            "Cât de mult te sperie aceste stări de detașare?",
            "Fear of Going Crazy, Insight", 
            3, 
            [
                ("A) Nu am astfel de stări.", 0), 
                ("B) Puțin, dacă apar.", 30), 
                ("C) Mă îngrijorează.", 60), 
                ("D) Mă terifiază. Simt că înnebunesc sau că dispar.", 100)
            ]
        )
    ]

    try:
        # CLEANUP & INSERT
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))

        for q_text, tags, wave, opts in questions_data:
            v_hash = generate_hash(q_text, opts)
            c.execute("""
                INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (AXIS_ID, v_hash, q_text, tags, wave))
            labels = ['A', 'B', 'C', 'D']
            for idx, (opt_text, score) in enumerate(opts):
                c.execute("""
                    INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                    VALUES (?, ?, ?, ?)
                """, (v_hash, labels[idx], opt_text, score))
        
        conn.commit()
        log("db_conn", f"SUCCES: {len(questions_data)} întrebări inserate pentru {AXIS_NAME}.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()