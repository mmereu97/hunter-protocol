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
AXIS_ID = 73
AXIS_NAME = "Recunoștință"
# Pol Stânga (0): Nemulțumit / Îndreptățit (Entitled) / Critic
# Pol Dreapta (100): Recunoscător / Apreciativ / Mulțumit

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
    # Punctaj: 0 = Nemulțumit, 100 = Recunoscător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Atitudinea Zilnică) ---
        (
            "Cât de des te oprești în timpul zilei doar pentru a aprecia un moment plăcut (o cafea bună, vremea, un gest)?",
            "Savoring, Mindfulness, Daily Life", 
            1, 
            [
                ("A) Niciodată. Sunt prea ocupat sau stresat.", 0), 
                ("B) Rar, dacă e ceva ieșit din comun.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Zilnic. Caut activ motive de bucurie.", 100)
            ]
        ),
        (
            "Când te uiți la viața ta în general, pe ce te concentrezi mai mult?",
            "Focus, Lack vs Abundance, Outlook", 
            1, 
            [
                ("A) Pe ce îmi lipsește și ce nu merge bine.", 0), 
                ("B) Pe problemele pe care trebuie să le rezolv.", 30), 
                ("C) Pe realizările mele.", 60), 
                ("D) Pe cât de norocos sunt pentru ceea ce am.", 100)
            ]
        ),
        (
            "Cât de des spui 'Mulțumesc' sincer oamenilor din jur (colegi, familie, prestatori de servicii)?",
            "Expression, Manners, Social", 
            1, 
            [
                ("A) Doar dacă e absolut necesar. Își fac doar treaba.", 0), 
                ("B) Când îmi amintesc.", 30), 
                ("C) Destul de des, e politicos.", 70), 
                ("D) Foarte des. Îmi place să îmi arăt aprecierea.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Mentalitate/Relații) ---
        (
            "Consideri că lumea sau societatea îți este datoare cu un trai mai bun?",
            "Entitlement, Victimhood, Responsibility", 
            2, 
            [
                ("A) Da, absolut. Nu am primit ce meritam.", 0), 
                ("B) Într-o oarecare măsură.", 30), 
                ("C) Nu neapărat. Trebuie să muncesc pentru asta.", 70), 
                ("D) Nu. Tot ce primesc bun este un bonus.", 100)
            ]
        ),
        (
            "Când ți se întâmplă ceva rău, reușești să găsești o lecție sau o parte bună ('silver lining')?",
            "Resilience, Reframing, Positivity", 
            2, 
            [
                ("A) Nu. Răul e rău și atât.", 0), 
                ("B) Greu, îmi ia mult timp.", 30), 
                ("C) De obicei da, după ce trece șocul.", 70), 
                ("D) Da, mereu există ceva de învățat sau de apreciat.", 100)
            ]
        ),
        (
            "Te compari des cu alții care au mai mult decât tine și te simți invidios?",
            "Envy, Comparison, Satisfaction", 
            2, 
            [
                ("A) Da, mă roade invidia constant.", 0), 
                ("B) Uneori mă simt frustrat.", 30), 
                ("C) Rar. Mă concentrez pe drumul meu.", 70), 
                ("D) Nu. Mă bucur pentru succesul lor și pentru ce am eu.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Narcisism / Depresie / Victimizare) ---
        (
            "Când ai un succes, cui atribui meritul?",
            "Modesty, Acknowledgment, Teamwork", 
            3, 
            [
                ("A) Mie. Eu am muncit, eu am reușit ('Self-made').", 0), 
                ("B) În mare parte mie.", 30), 
                ("C) Mie și echipei/familiei.", 70), 
                ("D) Recunosc ajutorul primit de la alții și norocul avut.", 100)
            ]
        ),
        (
            "Ai simțit vreodată o nevoie profundă de a scrie un mesaj sau o scrisoare cuiva doar pentru a-i mulțumi că există în viața ta?",
            "Deep Gratitude, Connection", 
            3, 
            [
                ("A) Nu, mi se pare siropos și inutil.", 0), 
                ("B) M-am gândit, dar nu am făcut-o.", 30), 
                ("C) O dată sau de două ori.", 70), 
                ("D) Da, fac asta periodic pentru oamenii dragi.", 100)
            ]
        ),
        (
            "Dacă ai pierde o parte din confortul actual (ex: bani, statut), crezi că ai mai putea fi fericit?",
            "Adaptability, Values, Materialism", 
            3, 
            [
                ("A) Nu. Fără standardul meu de viață sunt terminat.", 0), 
                ("B) Ar fi foarte greu și deprimant.", 30), 
                ("C) M-aș adapta, deși ar fi neplăcut.", 70), 
                ("D) Da. Fericirea vine din lucruri care nu se pot cumpăra.", 100)
            ]
        ),
        (
            "Simți vreo resentiment față de părinții tăi sau față de trecut pentru că nu ți-au oferit mai mult?",
            "Resentment, Past, Acceptance", 
            3, 
            [
                ("A) Da, le port pică. Au greșit mult.", 0), 
                ("B) Încă am regrete.", 30), 
                ("C) Au făcut ce au putut.", 70), 
                ("D) Le sunt recunoscător pentru viață, indiferent de greșeli.", 100)
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