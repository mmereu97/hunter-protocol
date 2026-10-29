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
AXIS_ID = 102
AXIS_NAME = "Yes-Man (Submisiv)"
# Pol 0: Asertiv / Critic
# Pol 100: Supus / Pleaser / Fără coloană

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

    # Punctaj: 100 = YES-MAN (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Relația cu Autoritatea) ---
        (
            "Dacă șeful tău propune o idee care știi sigur că va eșua, ce faci?",
            "Assertiveness, Authority, Courage", 
            1, 
            [
                ("A) Îi spun direct și argumentat că greșește.", 0), 
                ("B) Îi pun întrebări care să îl facă să realizeze singur.", 30), 
                ("C) Nu zic nimic, e decizia lui.", 70), 
                ("D) Îl laud pentru idee și execut, chiar dacă știu că e prost.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine să fii plăcut de toată lumea la birou?",
            "Social Approval, People Pleasing", 
            1, 
            [
                ("A) Deloc. Vreau să fiu respectat, nu plăcut.", 0), 
                ("B) E bine să fie armonie.", 30), 
                ("C) Destul de important, evit conflictele.", 70), 
                ("D) Crucial. Mă consum enorm dacă simt că cineva e supărat pe mine.", 100)
            ]
        ),
        (
            "Dacă ți se cere să faci ore suplimentare neplătite pentru a 5-a oară luna asta, ce zici?",
            "Boundaries, Refusal", 
            1, 
            [
                ("A) Refuz categoric.", 0), 
                ("B) Negociez sau cer recuperare.", 30), 
                ("C) Accept cu greu.", 70), 
                ("D) Accept imediat cu zâmbetul pe buze, ca să arăt că sunt dedicat.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Cameleonsim Social) ---
        (
            "Îți schimbi des opiniile (politice, profesionale) în funcție de persoana cu care vorbești?",
            "Social Chameleon, Lack of Identity", 
            2, 
            [
                ("A) Niciodată. Am principiile mele.", 0), 
                ("B) Uneori evit subiectele sensibile.", 30), 
                ("C) Da, ca să nu creez discuții.", 70), 
                ("D) Da, sunt de acord cu oricine vorbește ultimul cu mine.", 100)
            ]
        ),
        (
            "Cât de des îți ceri scuze pentru lucruri care nu sunt vina ta?",
            "Apology, Guilt, Submissiveness", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Rar, din politețe.", 30), 
                ("C) Destul de des, ca să calmez spiritele.", 70), 
                ("D) Constant. 'Îmi pare rău' e tic verbal.", 100)
            ]
        ),
        (
            "Te simți vinovat dacă refuzi o cerere, chiar dacă nu ai timp?",
            "Guilt, Overcommitment", 
            2, 
            [
                ("A) Nu. Prioritățile mele contează.", 0), 
                ("B) Puțin, dar refuz oricum.", 30), 
                ("C) Da, mă simt prost.", 70), 
                ("D) Da, așa că accept tot și mă îngrop în muncă.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Lipsă totală de coloană vertebrală) ---
        (
            "Dacă majoritatea grupului decide să facă ceva ce ție ți se pare greșit etic, te opui?",
            "Ethics, Peer Pressure, Conformity", 
            3, 
            [
                ("A) Da, mă opun vehement.", 0), 
                ("B) Mă retrag din grup.", 30), 
                ("C) Tac și merg cu valul.", 70), 
                ("D) Mă alătur lor entuziast ca să nu fiu exclus.", 100)
            ]
        ),
        (
            "Crezi că rolul unui subaltern este să execute orbește, fără să gândească?",
            "Hierarchy, Mindset, Obedience", 
            3, 
            [
                ("A) Nu, rolul meu e să aduc valoare și idei.", 0), 
                ("B) Execut, dar dau feedback.", 30), 
                ("C) În general, șeful are dreptate.", 70), 
                ("D) Da. Șeful e șef, eu doar fac ce zice el.", 100)
            ]
        ),
        (
            "Ai minți pentru șeful tău dacă el ți-ar cere-o, chiar dacă știi că e ilegal?",
            "Loyalty vs Integrity, Blind Obedience", 
            3, 
            [
                ("A) Niciodată. Îl denunț.", 0), 
                ("B) Aș refuza politicos.", 20), 
                ("C) M-aș simți presat și poate aș ceda.", 70), 
                ("D) Da. Loialitatea față de șef e supremă.", 100)
            ]
        ),
        (
            "Te simți anxios sau panicat dacă trebuie să iei o decizie singur, fără aprobarea cuiva?",
            "Autonomy, Dependency, Fear", 
            3, 
            [
                ("A) Nu, îmi place autonomia.", 0), 
                ("B) Prefer să mă consult, dar decid.", 30), 
                ("C) Da, prefer să decidă alții.", 70), 
                ("D) Da. Nu fac nicio mișcare fără aprobare.", 100)
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