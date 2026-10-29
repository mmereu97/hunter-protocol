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
AXIS_ID = 19
AXIS_NAME = "Iertare"
# Pol Stânga (0): Răzbunător / Ranchiunos / Resentimentar
# Pol Dreapta (100): Iertător / Împăciuitor / Tolerant

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
    # Punctaj: 0 = Ranchiunos, 100 = Iertător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Conflicte Minore) ---
        (
            "După o ceartă aprinsă cu un prieten sau coleg, cât timp îți ia să îți treacă supărarea?",
            "Conflict, Anger Duration, Mood", 
            1, 
            [
                ("A) Zile sau săptămâni. Îmi revin greu.", 0), 
                ("B) O zi sau două, depinde de gravitate.", 30), 
                ("C) Câteva ore, nu îmi place să stau supărat.", 70), 
                ("D) Aproape imediat. Viața e prea scurtă pentru certuri.", 100)
            ]
        ),
        (
            "Dacă cineva îți cere scuze sincer pentru o greșeală, care e reacția ta obișnuită?",
            "Apology, Trust, Reconciliation", 
            1, 
            [
                ("A) Le accept verbal, dar nu uit ce a făcut.", 0), 
                ("B) Sunt sceptic, aștept să văd dacă se repetă.", 30), 
                ("C) Accept și încerc să trec peste.", 70), 
                ("D) Iert complet și relația revine la normal.", 100)
            ]
        ),
        (
            "Cât de des te gândești la nedreptăți sau ofense din trecut?",
            "Rumination, Past, Grudges", 
            1, 
            [
                ("A) Foarte des. Retrăiesc momentele și mă înfurii din nou.", 0), 
                ("B) Uneori, când sunt melancolic.", 30), 
                ("C) Rar, trecutul e trecut.", 70), 
                ("D) Niciodată. Ce a fost, a fost.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Încredere/Trădare) ---
        (
            "Dacă un coleg te-a dezamăgit într-un proiect, ai mai lucra cu el a doua oară?",
            "Work, Trust, Second Chances", 
            2, 
            [
                ("A) Nu. M-aș asigura că nu mai depind de el.", 0), 
                ("B) Doar dacă sunt obligat de șef.", 30), 
                ("C) Da, dar aș fi mai precaut.", 70), 
                ("D) Da, oricine poate avea o zi proastă.", 100)
            ]
        ),
        (
            "Crezi în zicala 'Iert, dar nu uit'?",
            "Philosophy, Trust, Grudges", 
            2, 
            [
                ("A) Da, este motto-ul meu. Țin minte tot.", 0), 
                ("B) În mare parte da. Iertarea nu înseamnă amnezie.", 30), 
                ("C) Nu neapărat. Dacă ierți, trebuie să mergi mai departe.", 70), 
                ("D) Nu. Dacă ții minte răul, nu ai iertat cu adevărat.", 100)
            ]
        ),
        (
            "Când cineva te jignește, simți nevoia să îi răspunzi cu aceeași monedă?",
            "Retaliation, Impulse, Conflict", 
            2, 
            [
                ("A) Da, trebuie să simtă și el ce am simțit eu.", 0), 
                ("B) Uneori, îmi scapă o replică acidă.", 30), 
                ("C) Mă abțin, deși mă deranjează.", 70), 
                ("D) Nu. Răzbunarea nu rezolvă nimic.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Malicious / Răzbunător) ---
        (
            "Ai păstrat vreodată o supărare pe cineva ani de zile?",
            "Long-term Grudge, Bitterness", 
            3, 
            [
                ("A) Da, sunt oameni cu care nu voi mai vorbi niciodată.", 0), 
                ("B) Am câteva resentimente vechi, dar nu active.", 30), 
                ("C) Nu ani de zile, maxim câteva luni.", 70), 
                ("D) Nu. Nu pot să țin supărare atât de mult.", 100)
            ]
        ),
        (
            "Dacă cineva ți-ar face un rău intenționat, ai căuta o ocazie să te răzbuni subtil?",
            "Revenge, Malice, Machiavellianism", 
            3, 
            [
                ("A) Da, karma trebuie ajutată.", 0), 
                ("B) M-aș bucura dacă ar păți ceva rău, dar nu aș acționa.", 30), 
                ("C) Probabil nu, aș rupe doar legătura.", 70), 
                ("D) Nu. Cea mai bună răzbunare e să fii fericit.", 100)
            ]
        ),
        (
            "Ți se întâmplă să 'ții scorul' într-o relație (ex: 'eu am făcut asta de 3 ori, tu doar o dată')?",
            "Transactional, Keeping Score", 
            3, 
            [
                ("A) Da, corectitudinea e importantă. Nu vreau să fiu prostul.", 0), 
                ("B) Uneori, când mă simt nedreptățit.", 30), 
                ("C) Rar, încerc să nu fiu meschin.", 70), 
                ("D) Nu. Într-o relație nu există contabilitate.", 100)
            ]
        ),
        (
            "Cât de greu îți este să recâștigi încrederea în cineva care te-a mințit o dată?",
            "Trust, Betrayal, Rigidity", 
            3, 
            [
                ("A) Imposibil. Odată ruptă, încrederea nu se mai lipește.", 0), 
                ("B) Foarte greu, durează mult timp.", 20), 
                ("C) Destul de greu, dar se poate.", 60), 
                ("D) Relativ ușor, dacă văd că îi pare rău.", 100)
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