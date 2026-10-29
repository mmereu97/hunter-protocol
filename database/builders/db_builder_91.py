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
AXIS_ID = 91
AXIS_NAME = "Hărțuire (Boundaries)"
# Pol 0: Respectuos / Profesional
# Pol 100: Prădător / Invaziv / Fără Limite

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

    # Punctaj: 100 = HĂRȚUITOR (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Umor / Atmosferă) ---
        (
            "Ce părere ai despre glumele deocheate sau cu tentă sexuală spuse la locul de muncă?",
            "Humor, Workplace, Appropriateness", 
            1, 
            [
                ("A) Sunt nepotrivite și neprofesionale.", 0), 
                ("B) Depinde de cine e de față.", 30), 
                ("C) Sunt ok, mai destind atmosfera.", 60), 
                ("D) Sunt esențiale. Cine se supără nu are simțul umorului.", 100)
            ]
        ),
        (
            "Cât de aproape fizic stai de o persoană când îi vorbești?",
            "Personal Space, Body Language", 
            1, 
            [
                ("A) Păstrez o distanță respectuoasă (un braț).", 0), 
                ("B) Normal.", 30), 
                ("C) Destul de aproape, îmi place contactul.", 70), 
                ("D) Foarte aproape, uneori îi ating brațul sau umărul des.", 100)
            ]
        ),
        (
            "Dacă faci un compliment cuiva despre aspectul fizic și persoana pare stânjenită, ce faci?",
            "Empathy, Social Cues, Reaction", 
            1, 
            [
                ("A) Îmi cer scuze imediat și mă retrag.", 0), 
                ("B) Schimb subiectul.", 30), 
                ("C) Îi spun să nu fie timidă/timid.", 70), 
                ("D) Insist. Ar trebui să știe să primească un compliment.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Persistență / Refuz) ---
        (
            "Dacă inviți un coleg/o colegă în oraș și te refuză, ce faci?",
            "Rejection, Persistence, Boundaries", 
            2, 
            [
                ("A) Accept refuzul și nu mai întreb.", 0), 
                ("B) Poate mai încerc peste câteva luni.", 30), 
                ("C) Îl/o întreb de ce, poate o conving.", 70), 
                ("D) Insist. 'Nu' înseamnă doar 'convinge-mă'.", 100)
            ]
        ),
        (
            "Crezi că la birou ar trebui să fie permise relațiile romantice între șefi și subalterni?",
            "Power Dynamics, Ethics, Workplace", 
            2, 
            [
                ("A) Nu, creează conflicte de interese majore.", 0), 
                ("B) Doar dacă sunt declarate la HR.", 30), 
                ("C) Da, dragostea nu ține cont de funcție.", 60), 
                ("D) Da, puterea este atractivă și e normal să fie folosită.", 100)
            ]
        ),
        (
            "Ai comentat vreodată aspectul fizic al unui coleg într-un mod pe care alții l-au considerat 'prea direct'?",
            "Feedback, Reputation, Harassment", 
            2, 
            [
                ("A) Niciodată.", 0), 
                ("B) Nu cred, sunt atent.", 20), 
                ("C) Poate, dar lumea e prea sensibilă azi.", 70), 
                ("D) Da. Sunt onest, dacă arată bine (sau rău), o zic.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Predatory / Abuz de Putere) ---
        (
            "Ai atins vreodată pe cineva într-un mod nedorit (masaj nesolicitat, îmbrățișare forțată) crezând că e un gest prietenesc?",
            "Physical Contact, Consent, Boundaries", 
            3, 
            [
                ("A) Nu, respect spațiul personal cu strictețe.", 0), 
                ("B) Verific mereu dacă e ok.", 20), 
                ("C) S-a întâmplat, dar nu am vrut să supăr.", 60), 
                ("D) Da. Oamenii au nevoie de afecțiune chiar dacă se fac că nu vor.", 100)
            ]
        ),
        (
            "Ce părere ai despre mișcarea #MeToo și regulile stricte de hărțuire?",
            "Social Values, Attitude towards Victims", 
            3, 
            [
                ("A) Sunt necesare pentru protecție.", 0), 
                ("B) Au adus schimbări bune, dar și excese.", 30), 
                ("C) Au stricat atmosfera, bărbații nu mai pot face nimic.", 70), 
                ("D) O vânătoare de vrăjitoare. Victimele adesea exagerează.", 100)
            ]
        ),
        (
            "Dacă ai avea putere absolută asupra carierei cuiva de care ești atras, ai folosi acea putere pentru a te apropia de persoana respectivă?",
            "Power Abuse, Quid Pro Quo, Ethics", 
            3, 
            [
                ("A) Niciodată. Este abuz de putere.", 0), 
                ("B) Aș încerca să separ lucrurile.", 30), 
                ("C) Aș fi mai drăguț cu acea persoană.", 70), 
                ("D) Da. Este un avantaj pe care îl am și îl folosesc.", 100)
            ]
        ),
        (
            "Te enervezi dacă cineva te respinge sexual sau romantic și simți nevoia să te răzbuni (ex: să îi vorbești urât)?",
            "Retaliation, Narcissistic Injury, Danger", 
            3, 
            [
                ("A) Nu, e dreptul lor.", 0), 
                ("B) Sunt trist, dar nu mă răzbun.", 20), 
                ("C) Mă simt jignit.", 60), 
                ("D) Da. Cine mă refuză, plătește. Nu știe ce pierde.", 100)
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