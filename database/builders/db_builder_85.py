import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS & IMPORTS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 85
AXIS_NAME = "Disociere"
# Pol Stânga (0): Ancorat / Prezent
# Pol Dreapta (100): Disociat / Absent / Derealizat

# 3. FUNCȚIA DE HASHING
def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu a fost găsită la: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    log("sys", f"Populăm Axa {AXIS_ID}: {AXIS_NAME}...")

    # 4. DATASET-UL
    # Punctaj: 0 = Ancorat, 100 = Disociat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Pilot Automat) ---
        (
            "Ți se întâmplă să conduci mașina (sau să mergi pe jos) pe o distanță lungă și să ajungi la destinație fără să îți amintești nimic din drumul parcurs?",
            "Autopilot, Highway Hypnosis, Focus", 
            1, 
            [
                ("A) Nu, sunt mereu atent la drum.", 0), 
                ("B) Rar, doar dacă sunt foarte obosit.", 30), 
                ("C) Uneori, pe rute cunoscute.", 70), 
                ("D) Da, foarte des. Mintea mea e complet altundeva.", 100)
            ]
        ),
        (
            "Cât de des ți se întâmplă să 'te pierzi' într-o conversație și să nu auzi ce spune celălalt, deși te uiți la el?",
            "Zoning Out, Attention", 
            1, 
            [
                ("A) Niciodată. Ascult activ.", 0), 
                ("B) Doar dacă subiectul e plictisitor.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Constant. Trebuie să întreb des 'ce ai zis?'.", 100)
            ]
        ),
        (
            "Ai momente în care te simți ca un observator în propria viață, ca și cum ai privi un film?",
            "Detachment, Perspective", 
            1, 
            [
                ("A) Nu, mă simt prezent și implicat.", 0), 
                ("B) Rar, în momente de stres.", 30), 
                ("C) Uneori am această senzație de distanțare.", 70), 
                ("D) Da, des. Parcă nu eu trăiesc evenimentele.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Reacție la Stres/Memorie) ---
        (
            "În situații de stres extrem sau conflict, ai tendința să te 'închizi' emoțional și să nu mai simți nimic (numbness)?",
            "Emotional Numbness, Defense Mechanism", 
            2, 
            [
                ("A) Nu, simt emoțiile intens.", 0), 
                ("B) Îmi păstrez calmul, dar simt.", 30), 
                ("C) Da, devin puțin robot.", 70), 
                ("D) Da, mă deconectez complet. Nu mai simt nici durere, nici frică.", 100)
            ]
        ),
        (
            "Ți se întâmplă să găsești obiecte mutate prin casă și să nu îți amintești când le-ai mutat?",
            "Memory, Awareness", 
            2, 
            [
                ("A) Nu, am memorie bună.", 0), 
                ("B) Poate dacă sunt foarte distrat.", 30), 
                ("C) Uneori.", 70), 
                ("D) Da, mă sperie uneori cât de multe uit că am făcut.", 100)
            ]
        ),
        (
            "Cât de ușor te poți lăsa absorbit de un film, o carte sau un joc video, uitând complet de lumea din jur și de trecerea timpului?",
            "Hyperfocus, Immersion, Escapism", 
            2, 
            [
                ("A) Greu. Sunt atent la mediu.", 0), 
                ("B) Mă prinde, dar rămân conștient.", 30), 
                ("C) Pierd noțiunea timpului ușor.", 70), 
                ("D) Total. Dispar din realitate ore întregi.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Gândire Bizară / Depersonalizare / PTSD) ---
        (
            "Ai avut vreodată senzația că mâinile tale sau fața ta din oglindă nu îți aparțin (Depersonalizare)?",
            "Depersonalization, Clinical", 
            3, 
            [
                ("A) Nu, niciodată.", 0), 
                ("B) Poate o senzație ciudată de oboseală.", 20), 
                ("C) De câteva ori, a fost straniu.", 70), 
                ("D) Da, mi se întâmplă să nu mă recunosc.", 100)
            ]
        ),
        (
            "Lumea din jurul tău pare uneori falsă, plată, bidimensională sau ca de plastic (Derealizare)?",
            "Derealization, Reality Testing", 
            3, 
            [
                ("A) Nu, lumea e vie și reală.", 0), 
                ("B) Doar în lumina artificială uneori.", 20), 
                ("C) Am avut senzația asta.", 70), 
                ("D) Da. Uneori simt că trăiesc într-o simulare.", 100)
            ]
        ),
        (
            "Ți se întâmplă să nu recunoști locuri familiare sau oameni pe care îi știi?",
            "Jamais Vu, Confusion", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Foarte rar, o confuzie de moment.", 30), 
                ("C) Uneori locurile par străine.", 70), 
                ("D) Da, am momente de 'jamais vu' (straniu în familiar).", 100)
            ]
        ),
        (
            "Ai simțit vreodată că ai mai multe 'părți' ale personalității tale care nu comunică între ele?",
            "Identity Integration, Fragmentation", 
            3, 
            [
                ("A) Nu, sunt o singură persoană coerentă.", 0), 
                ("B) Am toane diferite, dar sunt eu.", 30), 
                ("C) Uneori mă comport atât de diferit încât mă mir.", 70), 
                ("D) Da, simt că sunt fragmentat intern.", 100)
            ]
        )
    ]

    try:
        # 5. CURĂȚARE
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"Curățat întrebări vechi pentru Axa {AXIS_ID}.")

        # 6. INSERARE
        count = 0
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
            count += 1

        conn.commit()
        log("db_conn", f"SUCCES: {count} întrebări inserate pentru {AXIS_NAME}.")

    except Exception as e:
        log_error(f"Eroare Axa {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()