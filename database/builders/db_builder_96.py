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
AXIS_ID = 96
AXIS_NAME = "Malicious (Răutate / Răzbunare)"
# Pol 0: Binevoitor / Constructiv
# Pol 100: Răzbunător / Malign / Pasiv-Agresiv

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
    log("sys", f"Populăm Monstrul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = MALICIOUS (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Schadenfreude / Rigiditate) ---
        (
            "Dacă un coleg care ți-a fost antipatic face o greșeală majoră și este sancționat, ce simți?",
            "Schadenfreude, Empathy, Rivalry", 
            1, 
            [
                ("A) Îmi pare rău pentru el, e o situație grea.", 0), 
                ("B) Indiferență. Fiecare cu treaba lui.", 30), 
                ("C) O mică satisfacție. Karma funcționează.", 70), 
                ("D) Mă bucur enorm. Merita să sufere.", 100)
            ]
        ),
        (
            "Dacă observi o eroare într-un proiect care nu e al tău, dar știi că va cauza probleme mari mai târziu, ce faci?",
            "Helpfulness, Sabotage by Omission", 
            1, 
            [
                ("A) Anunț imediat responsabilul să corecteze.", 0), 
                ("B) Îi dau un indiciu prietenesc.", 30), 
                ("C) Nu zic nimic. Să fie mai atent data viitoare.", 70), 
                ("D) Tac și aștept să văd 'spectacolul' când totul se prăbușește.", 100)
            ]
        ),
        (
            "Ce părere ai despre 'Malicious Compliance' (a respecta ordinul șefului exact cum a fost dat, știind că va duce la dezastru)?",
            "Authority, Passive-Aggressive, Compliance", 
            1, 
            [
                ("A) E contraproductiv. Trebuie să avertizezi șeful.", 0), 
                ("B) O fac doar dacă șeful insistă absurd.", 30), 
                ("C) E o lecție bună pentru șefii aroganți.", 70), 
                ("D) O ador. 'Am făcut exact ce mi-ai cerut, nu e vina mea'.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Răzbunare / "Lecții") ---
        (
            "Dacă cineva îți taie calea în trafic sau se bagă în fața ta, simți nevoia să îi 'dai o lecție' (ex: frână bruscă, blocat)?",
            "Road Rage, Retaliation, Teaching Lesson", 
            2, 
            [
                ("A) Nu, e periculos și inutil.", 0), 
                ("B) Mă enervez, dar nu fac nimic.", 30), 
                ("C) Uneori îl blochez puțin să se învețe minte.", 70), 
                ("D) Da, mă asigur că ține minte să nu mai facă asta.", 100)
            ]
        ),
        (
            "Când ai puterea de a aproba sau respinge cererile altora (birocrație), cum te comporți cu cei care nu îți plac?",
            "Power Abuse, Bureaucracy, Pettiness", 
            2, 
            [
                ("A) Sunt profesionist și imparțial.", 0), 
                ("B) Îi tratez corect, dar rece.", 20), 
                ("C) Le cer documente suplimentare, să muncească puțin.", 70), 
                ("D) Le resping cererile pe motive tehnice sau le amân la infinit.", 100)
            ]
        ),
        (
            "Ai bârfit vreodată pe cineva cu intenția clară de a-i strica reputația?",
            "Gossip, Malice, Reputation", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Doar m-am plâns de comportamentul lui.", 30), 
                ("C) Am exagerat puțin adevărul, da.", 70), 
                ("D) Da, uneori reputația cuiva trebuie distrusă.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Vindictiveness / Cruzime Psihologică) ---
        (
            "Dacă un fost partener sau prieten te trădează, cum te răzbuni?",
            "Revenge, Forgiveness, Moving On", 
            3, 
            [
                ("A) Nu mă răzbun. Cea mai bună răzbunare e să fii fericit.", 0), 
                ("B) Rup orice legătură.", 30), 
                ("C) Mă asigur că prietenii comuni știu ce a făcut.", 60), 
                ("D) Planific o răzbunare rece și dureroasă pe termen lung.", 100)
            ]
        ),
        (
            "Te simți bine când refuzi ajutorul cuiva care are disperată nevoie, pe motiv că 'nu e treaba ta'?",
            "Lack of Empathy, Coldness, Rules", 
            3, 
            [
                ("A) Nu, mă simt vinovat.", 0), 
                ("B) Îl ajut dacă pot.", 20), 
                ("C) Nu e treaba mea să salvez lumea.", 60), 
                ("D) Da. Fiecare trebuie să se descurce singur. Nu sunt asistență socială.", 100)
            ]
        ),
        (
            "Ai păstrat vreodată informații vitale pentru tine doar pentru a te face indispensabil sau pentru a vedea cum se chinuie alții?",
            "Gatekeeping, Information Hoarding", 
            3, 
            [
                ("A) Nu, împărtășesc totul cu echipa.", 0), 
                ("B) Păstrez doar atuurile mele profesionale.", 30), 
                ("C) Uneori 'uit' să dau detalii.", 70), 
                ("D) Da. Informația e putere, nu o dau gratis.", 100)
            ]
        ),
        (
            "Crezi că oamenii care sunt 'prea buni' sunt de fapt proști și merită să fie exploatați?",
            "Worldview, Predatory, Cynicism", 
            3, 
            [
                ("A) Nu, bunătatea e o virtute.", 0), 
                ("B) Sunt naivi, dar nu merită exploatați.", 30), 
                ("C) Uneori își fac rău singuri.", 60), 
                ("D) Da. Dacă te lași călcat în picioare, meriți.", 100)
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