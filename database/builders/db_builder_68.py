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
AXIS_ID = 68
AXIS_NAME = "Demoralizare (Disperare)"
# Pol 0: Speranță / Reziliență
# Pol 100: Disperare / Renunțare

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

    # Punctaj: 100 = DEMORALIZAT (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Sentimentul de Copleșire) ---
        (
            "Cât de des simți că problemele tale s-au adunat atât de mult încât nu le mai poți face față?",
            "Overwhelmed, Coping", 
            1, 
            [
                ("A) Niciodată. Iau problemele pe rând.", 0), 
                ("B) Uneori e greu, dar mă descurc.", 30), 
                ("C) Deseori mă simt depășit.", 70), 
                ("D) Constant. Simt că mă înec și nu mai am putere.", 100)
            ]
        ),
        (
            "Când te gândești la viitor, crezi că lucrurile se vor îmbunătăți?",
            "Hope, Optimism", 
            1, 
            [
                ("A) Da, sigur.", 0), 
                ("B) Sper că da, muncesc pentru asta.", 30), 
                ("C) Mă îndoiesc, pare că bat pasul pe loc.", 70), 
                ("D) Nu. Nu văd nicio luminiță la capătul tunelului.", 100)
            ]
        ),
        (
            "Simți că ai control asupra direcției în care merge viața ta?",
            "Agency, Locus of Control", 
            1, 
            [
                ("A) Da, eu sunt căpitanul.", 0), 
                ("B) În mare parte da.", 30), 
                ("C) Simt că sunt purtat de val.", 70), 
                ("D) Nu. Sunt prins într-o capcană fără ieșire.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Eșec / Stima de sine) ---
        (
            "Cum te evaluezi comparativ cu alții?",
            "Self-Esteem, Comparison", 
            2, 
            [
                ("A) Sunt mulțumit de mine.", 0), 
                ("B) Am calități și defecte, ca toți.", 30), 
                ("C) Mă simt adesea inferior.", 70), 
                ("D) Sunt un eșec total. Alții se descurcă, eu nu.", 100)
            ]
        ),
        (
            "Cât de des plângi sau îți vine să plângi din cauza neputinței?",
            "Crying, Helplessness, Emotion", 
            2, 
            [
                ("A) Foarte rar.", 0), 
                ("B) Doar la evenimente triste majore.", 30), 
                ("C) Destul de des în ultima vreme.", 70), 
                ("D) Zilnic. Am o tristețe care nu trece.", 100)
            ]
        ),
        (
            "Ai renunțat la activități care înainte îți plăceau pentru că simți că 'nu mai are rost'?",
            "Apathy, Pointlessness", 
            2, 
            [
                ("A) Nu, hobby-urile mă relaxează.", 0), 
                ("B) Doar din lipsă de timp.", 20), 
                ("C) Da, nu mai am energie pentru ele.", 70), 
                ("D) Da. Nimic nu mai are rost oricum.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Disperare Clinică / Idei Suicidare Pasive) ---
        (
            "Te trezești dimineața dezamăgit că a început o nouă zi?",
            "Morning Dread, Depression", 
            3, 
            [
                ("A) Nu, mă trezesc ok.", 0), 
                ("B) Doar lunea sau când sunt obosit.", 30), 
                ("C) Da, aș vrea să dorm mai mult să uit.", 70), 
                ("D) Da. Viața e o povară pe care trebuie să o car.", 100)
            ]
        ),
        (
            "Simți că ești o povară pentru familia sau prietenii tăi?",
            "Burden, Guilt, Isolation", 
            3, 
            [
                ("A) Nu, ne ajutăm reciproc.", 0), 
                ("B) Uneori cer prea mult ajutor.", 30), 
                ("C) Mă tem să nu îi plictisesc cu problemele mele.", 70), 
                ("D) Da. Le-ar fi mai bine fără mine.", 100)
            ]
        ),
        (
            "Mai ai energie să lupți pentru a-ți rezolva problemele?",
            "Willpower, Resilience", 
            3, 
            [
                ("A) Da, sunt un luptător.", 0), 
                ("B) Sunt obosit, dar continui.", 30), 
                ("C) M-am săturat să lupt.", 70), 
                ("D) Nu. Am renunțat. Ce-o fi, o fi.", 100)
            ]
        ),
        (
            "Te simți singur și neînțeles, chiar și când ești înconjurat de oameni?",
            "Loneliness, Alienation", 
            3, 
            [
                ("A) Nu, am conexiuni bune.", 0), 
                ("B) Uneori, e normal.", 30), 
                ("C) Da, mă simt izolat emoțional.", 70), 
                ("D) Da. Nimeni nu poate înțelege prin ce trec.", 100)
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