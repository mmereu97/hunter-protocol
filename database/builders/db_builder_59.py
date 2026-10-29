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
AXIS_ID = 59
AXIS_NAME = "Gândire Bizară (Psihoticism)"
# Pol 0: Rațional / Ancorat
# Pol 100: Psihotic / Delirant

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

    # Punctaj: 100 = PSIHOTIC (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Gândire Magică / Tipare) ---
        (
            "Ți se întâmplă des să observi coincidențe stranii sau semne care par să îți transmită un mesaj personal?",
            "Magical Thinking, Signs, Patterns", 
            1, 
            [
                ("A) Nu, coincidențele sunt doar statistici.", 0), 
                ("B) Rar, dar uneori e ciudat.", 30), 
                ("C) Da, cred că universul îmi vorbește.", 70), 
                ("D) Zilnic. Totul în jur are o semnificație ascunsă pentru mine.", 100)
            ]
        ),
        (
            "Ai idei sau gânduri pe care ceilalți le consideră ciudate sau greu de înțeles?",
            "Eccentricity, Social Norms", 
            1, 
            [
                ("A) Nu, sunt o persoană obișnuită.", 0), 
                ("B) Am idei originale, dar logice.", 30), 
                ("C) Da, prietenii îmi spun că sunt 'dus'.", 60), 
                ("D) Da, nimeni nu are capacitatea să înțeleagă ce văd eu.", 100)
            ]
        ),
        (
            "Crezi în fenomene paranormale, telepatie sau puteri extrasenzoriale?",
            "Beliefs, Paranormal, Rationality", 
            1, 
            [
                ("A) Nu, sunt sceptic.", 0), 
                ("B) Sunt deschis, dar nu am dovezi.", 30), 
                ("C) Cred că există energii pe care le simțim.", 60), 
                ("D) Da, am experimentat personal astfel de puteri.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Paranoia / Control) ---
        (
            "Ai simțit vreodată că cineva îți poate citi gândurile sau că îți introduce gânduri în minte?",
            "Mind Reading, Thought Insertion, Delusion", 
            2, 
            [
                ("A) Niciodată. Gândurile mele sunt private.", 0), 
                ("B) Doar metaforic, când cineva mă cunoaște bine.", 20), 
                ("C) Uneori am avut senzația stranie că sunt 'scanat'.", 70), 
                ("D) Da, știu sigur că gândurile mele nu sunt în siguranță.", 100)
            ]
        ),
        (
            "Simți că ești urmărit sau că există un complot împotriva ta, chiar dacă nu ai dovezi concrete?",
            "Paranoia, Persecution", 
            2, 
            [
                ("A) Nu.", 0), 
                ("B) Uneori sunt precaut noaptea.", 20), 
                ("C) Da, am multe suspiciuni.", 70), 
                ("D) Da, sunt forțe care lucrează activ să mă distrugă.", 100)
            ]
        ),
        (
            "Ți se întâmplă să simți o prezență invizibilă în cameră, chiar când ești singur?",
            "Sensing Presence, Hallucination risk", 
            2, 
            [
                ("A) Nu, niciodată.", 0), 
                ("B) Poate după un film de groază.", 20), 
                ("C) Uneori simt că nu sunt singur.", 60), 
                ("D) Da, simt adesea entități sau spirite lângă mine.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Halucinații / Disociere Gravă) ---
        (
            "Ai auzit vreodată voci sau sunete pe care alții nu le auzeau?",
            "Auditory Hallucinations, Psychosis", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Doar când adormeam (vis).", 10), 
                ("C) Mi s-a părut că îmi aud numele strigat.", 60), 
                ("D) Da, aud voci care îmi vorbesc sau comentează ce fac.", 100)
            ]
        ),
        (
            "Crezi că ai puteri speciale sau o misiune divină pe care oamenii obișnuiți nu o au?",
            "Grandiosity, Messiah Complex", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Cred că fiecare om e special.", 20), 
                ("C) Simt că am un destin aparte.", 60), 
                ("D) Da, am puteri/cunoștințe unice care vor schimba lumea.", 100)
            ]
        ),
        (
            "Uneori, lucrurile din jurul tău (obiecte, oameni) par ireale, distorsionate sau ca într-un vis?",
            "Derealization, Perception", 
            3, 
            [
                ("A) Nu, realitatea e solidă.", 0), 
                ("B) Doar la oboseală extremă.", 20), 
                ("C) Mi se întâmplă să văd lumea ca printr-un geam.", 70), 
                ("D) Da, des. Lumea își schimbă forma sau culorile.", 100)
            ]
        ),
        (
            "Ai impresia că televizorul, radioul sau internetul îți trimit mesaje codificate special pentru tine?",
            "Ideas of Reference, Delusion", 
            3, 
            [
                ("A) Nu, e absurd.", 0), 
                ("B) Uneori algoritmii par că mă ascultă.", 30), 
                ("C) Am observat coincidențe ciudate în reclame.", 60), 
                ("D) Da, primesc mesaje secrete prin media.", 100)
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