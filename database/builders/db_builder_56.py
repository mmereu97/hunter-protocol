import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 56
AXIS_NAME = "Management Emoțional (Reglare EQ)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 0 = Reactiv/Exploziv, 100 = Controlat/Stoic
    questions_data = [
        # --- VALUL 1: SCREENING (Reacție la Stres) ---
        (
            "Când ești foarte furios sau supărat, cât de repede reușești să te calmezi singur?",
            "Anger Management, Self-Soothing", 1, 
            [
                ("A) Foarte greu. Îmi strică toată ziua.", 0), 
                ("B) Îmi ia câteva ore.", 30), 
                ("C) Destul de repede, respir adânc.", 70), 
                ("D) Imediat. Pot să trec peste emoție instantaneu.", 100)
            ]
        ),
        (
            "Ți se întâmplă des să spui sau să faci lucruri 'la nervi' pe care apoi le regreți?",
            "Impulse Control, Regret", 1, 
            [
                ("A) Da, foarte des.", 0), 
                ("B) Uneori.", 30), 
                ("C) Rar.", 70), 
                ("D) Niciodată. Gândesc înainte să reacționez, oricât de nervos aș fi.", 100)
            ]
        ),
        (
            "Când primești o veste proastă, te simți copleșit și incapabil să acționezi?",
            "Resilience, Coping, Panic", 1, 
            [
                ("A) Da, mă blochez sau plâng.", 0), 
                ("B) Mă afectează, dar îmi revin.", 30), 
                ("C) Mă îngrijorez, dar caut soluții.", 70), 
                ("D) Nu. Rămân calm și analizez situația la rece.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Mască Socială / Profesionalism) ---
        (
            "Cât de ușor îți este să îți ascunzi sentimentele (tristețe, furie) într-un context profesional, dacă e necesar?",
            "Poker Face, Professionalism, Masking", 2, 
            [
                ("A) Imposibil. Se vede totul pe fața mea.", 0), 
                ("B) E greu, vocea mă trădează.", 30), 
                ("C) Pot să par calm.", 70), 
                ("D) Foarte ușor. Am control total asupra expresiei mele.", 100)
            ]
        ),
        (
            "Dacă cineva țipă la tine, ai tendința să țipi și tu înapoi (escaladare) sau să rămâi calm (de-escaladare)?",
            "Conflict, Emotional Contagion", 2, 
            [
                ("A) Țip și eu. Nu mă las călcat în picioare.", 0), 
                ("B) Mă enervez vizibil.", 30), 
                ("C) Încerc să nu ridic tonul.", 70), 
                ("D) Rămân perfect calm. Furia lui nu mă atinge.", 100)
            ]
        ),
        (
            "Dispoziția ta se schimbă frecvent pe parcursul unei zile în funcție de evenimentele externe?",
            "Mood Stability, Reactivity", 2, 
            [
                ("A) Da, sunt ca un carusel emoțional.", 0), 
                ("B) Sunt destul de sensibil la mediu.", 30), 
                ("C) Sunt destul de constant.", 70), 
                ("D) Nu. Starea mea interioară e stabilă, indiferent ce se întâmplă afară.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Stoicism vs Instabilitate) ---
        (
            "În situații de criză majoră, alții te văd ca pe o persoană panicată sau ca pe o 'stâncă'?",
            "Leadership in Crisis, Stoicism", 3, 
            [
                ("A) Panicat. Am nevoie de cineva să mă calmeze.", 0), 
                ("B) Agitat.", 30), 
                ("C) Destul de stăpân pe mine.", 60), 
                ("D) O stâncă. Devin hiper-focalizat și rațional în criză.", 100)
            ]
        ),
        (
            "Poți să îți schimbi starea de spirit voluntar (ex: să te motivezi când ești trist)?",
            "Self-Motivation, Regulation Strategy", 3, 
            [
                ("A) Nu, trebuie să aștept să treacă.", 0), 
                ("B) E greu.", 30), 
                ("C) Uneori reușesc.", 60), 
                ("D) Da, am tehnici mentale să mă resetez.", 100)
            ]
        ),
        (
            "Simți că emoțiile tale sunt mai puternice decât tine și te 'inundă'?",
            "Overwhelmed, Lack of Control", 3, 
            [
                ("A) Da, des. Mă simt neputincios în fața lor.", 0), 
                ("B) Uneori.", 30), 
                ("C) Rar.", 70), 
                ("D) Nu. Eu îmi conduc emoțiile, nu ele pe mine.", 100)
            ]
        ),
        (
            "Ai recurs vreodată la mâncare, alcool sau substanțe pentru a te calma, pentru că nu puteai gestiona emoția altfel?",
            "Coping Mechanisms, Risk", 3, 
            [
                ("A) Da, des.", 0), 
                ("B) Uneori.", 30), 
                ("C) Foarte rar.", 70), 
                ("D) Nu. Folosesc metode sănătoase (sport, meditație, gândire).", 100)
            ]
        )
    ]

    try:
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
        log("db_conn", f"SUCCES: Întrebări Management Emoțional inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()