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
AXIS_ID = 12
AXIS_NAME = "Răbdare"
# Pol Stânga (0): Irascibil / Fitil Scurt / Nervos
# Pol Dreapta (100): Răbdător / Stoic / Tolerant

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
    # Punctaj: 0 = Irascibil, 100 = Răbdător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Zilnic/Social) ---
        (
            "Trebuie să explici cuiva o procedură simplă, dar persoana respectivă nu înțelege din prima și pune aceleași întrebări. Cum reacționezi?",
            "Teaching, Tolerance, Frustration", 
            1, 
            [
                ("A) Mă enervez vizibil sau îi spun că e greu de cap.", 0), 
                ("B) Devin sarcastic sau ridic tonul.", 30), 
                ("C) Respir adânc și explic din nou, mai rar.", 70), 
                ("D) Îmi păstrez calmul total, caut o altă metodă de a explica.", 100)
            ]
        ),
        (
            "Ești la un restaurant și comanda întârzie nejustificat de mult. Ce faci?",
            "Service, Waiting, Anger", 
            1, 
            [
                ("A) Fac scandal și cer să vorbesc cu managerul.", 0), 
                ("B) Sunt iritat și îi bat obrazul chelnerului.", 30), 
                ("C) Aștept, dar nu voi lăsa bacșiș.", 70), 
                ("D) Înțeleg că poate e aglomerat, aștept liniștit.", 100)
            ]
        ),
        (
            "Când un aparat electronic (telefon, PC) se blochează sau merge greu, care e prima reacție?",
            "Technology, Rage, Impulse", 
            1, 
            [
                ("A) Îmi vine să dau cu el de pământ (sau chiar o fac).", 0), 
                ("B) Înjur și lovesc masa.", 30), 
                ("C) Mă enervez, dar încerc să îl restartez.", 70), 
                ("D) Aștept să își revină sau caut o soluție tehnică.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Trafic/Muncă) ---
        (
            "Ești blocat într-un trafic infernal și știi că vei întârzia. Cum te simți în mașină?",
            "Traffic, Control, Stress", 
            2, 
            [
                ("A) Fierb de furie, claxonez, urlu.", 0), 
                ("B) Sunt foarte tensionat și frustrat.", 30), 
                ("C) Sunt nemulțumit, dar sun să anunț.", 70), 
                ("D) Ascult muzică/podcast. Nu pot controla traficul, deci nu mă agit.", 100)
            ]
        ),
        (
            "Cât de repede 'îți sare țandăra' dacă cineva te contrazice pe un ton nepoliticos?",
            "Conflict, Trigger, Temper", 
            2, 
            [
                ("A) Instantaneu. Nu permit lipsa de respect.", 0), 
                ("B) Destul de repede, mă aprind ușor.", 30), 
                ("C) Încerc să mă abțin, dar mă consumă interior.", 70), 
                ("D) Rămân calm și nu iau lucrurile personal.", 100)
            ]
        ),
        (
            "La muncă, un coleg îți întrerupe fluxul de lucru pentru o întrebare banală. Cum reacționezi?",
            "Work, Interruptions, Focus", 
            2, 
            [
                ("A) Îl repezesc: 'Nu vezi că am treabă?!'.", 0), 
                ("B) Îi răspund sec și vizibil deranjat.", 30), 
                ("C) Îl rog să revină mai târziu.", 70), 
                ("D) Îi răspund calm și revin la lucru.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Agresivitate / Yes-Man) ---
        (
            "Când lucrurile nu merg conform planului, ai tendința de a ridica vocea la cei din jur?",
            "Aggression, Verbal Abuse, Stress", 
            3, 
            [
                ("A) Da, țip ca să mă descarc și să se miște lucrurile.", 0), 
                ("B) Uneori ridic tonul fără să vreau.", 30), 
                ("C) Foarte rar, doar în situații extreme.", 70), 
                ("D) Niciodată. Țipatul nu rezolvă nimic.", 100)
            ]
        ),
        (
            "Dacă stai la o coadă și cineva se bagă în față, ce faci?",
            "Assertiveness, Conflict, Justice", 
            3, 
            [
                ("A) Fac scandal imediat, îl pun la punct agresiv.", 0), 
                ("B) Îi fac o observație tăioasă.", 30), 
                ("C) Mă uit urât, dar probabil nu zic nimic.", 70), 
                ("D) Îi atrag atenția politicos sau ignor incidentul.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să strici o relație sau să pierzi un job din cauza unui moment de furie necontrolată?",
            "Consequences, Regret, Impulsivity", 
            3, 
            [
                ("A) Da, de mai multe ori. Sunt vulcanic.", 0), 
                ("B) O dată sau de două ori.", 30), 
                ("C) Am fost aproape, dar m-am oprit la timp.", 70), 
                ("D) Nu, am control asupra reacțiilor mele.", 100)
            ]
        ),
        (
            "Oamenii apropiați ți-au spus vreodată că trebuie să ai mai multă răbdare sau că ești prea irascibil?",
            "Feedback, Reputation, Self-Awareness", 
            3, 
            [
                ("A) Da, îmi spun asta des.", 0), 
                ("B) Uneori, când sunt obosit.", 30), 
                ("C) Rar, de obicei sunt calm.", 70), 
                ("D) Nu, sunt considerat o persoană foarte calmă.", 100)
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