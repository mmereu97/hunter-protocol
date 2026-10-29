import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 108
AXIS_NAME = "Tulburare Bipolară"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME}...")

    # Punctaj: 100 = MANIE / BIPOLAR ACTIV
    questions_data = [
        # --- VALUL 1: SCREENING (Energie Ciclică / Somn) ---
        (
            "Ai perioade în care te simți extrem de energic, nu ai nevoie de somn și simți că poți face orice, urmate de prăbușiri?",
            "Cyclothymia, Mood Cycles, Energy", 1, 
            [
                ("A) Nu, am un nivel de energie constant.", 0), 
                ("B) Am variații normale.", 20), 
                ("C) Da, am zile când sunt hiperactiv.", 60), 
                ("D) Da, am episoade clare de 'super-om' urmate de depresie.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să dormi doar 2-3 ore pe noapte timp de câteva zile și totuși să nu te simți obosit?",
            "Decreased Need for Sleep, Mania", 1, 
            [
                ("A) Niciodată. Am nevoie de 8 ore.", 0), 
                ("B) Doar dacă beau multă cafea.", 20), 
                ("C) Rar, când sunt stresat.", 50), 
                ("D) Da, în perioadele mele 'bune' nu am nevoie de somn.", 100)
            ]
        ),
        (
            "Simți uneori că gândurile tale merg atât de repede încât nu poți să le ții pasul sau să le exprimi?",
            "Racing Thoughts, Flight of Ideas", 1, 
            [
                ("A) Nu, gândesc clar și structurat.", 0), 
                ("B) Doar când sunt foarte aglomerat.", 30), 
                ("C) Uneori mintea mea e ca un carusel.", 60), 
                ("D) Da, am o avalanșă de idei care nu se oprește.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Impulsivitate Maniacală / Grandoare) ---
        (
            "În perioadele de energie maximă, ai cheltuit sume mari de bani pe lucruri inutile sau ai făcut investiții riscante?",
            "Spending Spree, Impulsivity", 2, 
            [
                ("A) Nu, sunt chibzuit mereu.", 0), 
                ("B) Poate mi-am luat un moft.", 20), 
                ("C) Da, am regretat apoi.", 70), 
                ("D) Da, am golit contul crezând că am ideea secolului.", 100)
            ]
        ),
        (
            "Ai simțit vreodată că ai puteri speciale, talente unice sau o misiune divină, mult peste realitate?",
            "Grandiosity, Delusion", 2, 
            [
                ("A) Nu, sunt realist.", 0), 
                ("B) Am încredere în mine, atâta tot.", 20), 
                ("C) Uneori mă simt invincibil.", 60), 
                ("D) Da. În acele momente simt că sunt un geniu sau un ales.", 100)
            ]
        ),
        (
            "Prietenii ți-au spus vreodată că vorbești prea mult, prea repede și că nu te pot întrerupe?",
            "Pressured Speech, Social Behavior", 2, 
            [
                ("A) Nu, sunt un ascultător bun.", 0), 
                ("B) Vorbesc normal.", 20), 
                ("C) Când sunt entuziasmat, vorbesc mult.", 60), 
                ("D) Da, mi se spune des să 'iau o pauză de respirație'.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Risc Major / Diagnostic) ---
        (
            "Ai început vreodată mai multe proiecte grandioase simultan, lucrând frenetic la ele, doar pentru a le abandona complet când starea s-a schimbat?",
            "Goal-Directed Activity, Abandonment", 3, 
            [
                ("A) Nu, sunt consecvent.", 0), 
                ("B) Am câteva proiecte neterminate.", 30), 
                ("C) Da, am explozii de creativitate.", 70), 
                ("D) Da, viața mea e plină de șantiere abandonate din perioadele de manie.", 100)
            ]
        ),
        (
            "În perioadele 'înalte', ai devenit mult mai activ sexual sau ai avut comportamente riscante pe care nu le-ai avea în mod normal?",
            "Hypersexuality, Risk Behavior", 3, 
            [
                ("A) Nu, comportamentul meu e constant.", 0), 
                ("B) Nu cred.", 20), 
                ("C) Devin mai dezinhibat.", 60), 
                ("D) Da, fac lucruri de care îmi e rușine ulterior.", 100)
            ]
        ),
        (
            "Devii extrem de iritabil sau chiar agresiv dacă cineva încearcă să te încetinească în perioadele tale de energie?",
            "Manic Irritability, Rage", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Mă enervez puțin.", 30), 
                ("C) Da, nu suport să fiu oprit.", 70), 
                ("D) Da, explodez. Nimeni nu înțelege viziunea mea.", 100)
            ]
        ),
        (
            "Ai fost vreodată diagnosticat sau suspectat de tulburare bipolară de către un specialist?",
            "Medical History, Insight", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Mi s-a spus că am ciclotimie (forme ușoare).", 50), 
                ("C) Am avut suspiciuni.", 70), 
                ("D) Da, am istoric medical.", 100)
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
        log("db_conn", f"SUCCES: Întrebări Bipolar inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()