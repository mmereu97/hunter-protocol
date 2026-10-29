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
AXIS_ID = 94
AXIS_NAME = "Sabotor (Toxic)"
# Pol 0: Colegial / Transparent
# Pol 100: Toxic / Subminator / Bârfitor

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

    # Punctaj: 100 = SABOTOR (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Politici de Birou / Bârfă) ---
        (
            "Ce părere ai despre 'politicile de birou' (alianțe, discuții de culise)?",
            "Office Politics, Strategy, Ethics", 
            1, 
            [
                ("A) Le urăsc, îmi fac doar treaba.", 0), 
                ("B) Le ignor pe cât posibil.", 30), 
                ("C) Sunt necesare pentru a supraviețui.", 70), 
                ("D) Sunt esențiale. Cine nu le joacă, pierde.", 100)
            ]
        ),
        (
            "Cât de interesat ești de viața privată sau greșelile colegilor tăi?",
            "Gossip, Information, Leverage", 
            1, 
            [
                ("A) Deloc. Nu e treaba mea.", 0), 
                ("B) Ascult dacă se vorbește, dar nu dau mai departe.", 30), 
                ("C) Sunt curios, informația e putere.", 70), 
                ("D) Foarte interesat. Niciodată nu știi când îți folosește un secret.", 100)
            ]
        ),
        (
            "Dacă un coleg pe care nu îl placi primește o laudă nemeritată, ce faci?",
            "Envy, Justice, Reaction", 
            1, 
            [
                ("A) Tac și îmi văd de treabă.", 0), 
                ("B) Mă frustrează, dar asta e.", 30), 
                ("C) Fac o remarcă subtilă despre incompetența lui.", 70), 
                ("D) Mă asigur că șeful află despre greșelile lui trecute.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Reținere Info / Subminare) ---
        (
            "Ai 'uitat' vreodată intenționat să transmiți o informație unui coleg pentru a-l pune într-o lumină proastă?",
            "Withholding Info, Sabotage", 
            2, 
            [
                ("A) Niciodată. Succesul echipei contează.", 0), 
                ("B) Poate am uitat, dar nu intenționat.", 20), 
                ("C) S-a întâmplat, dacă era un rival.", 70), 
                ("D) Da. În carieră e fiecare pentru el.", 100)
            ]
        ),
        (
            "Dacă lucrezi în echipă și proiectul eșuează, încerci să te asiguri că vina cade pe altcineva?",
            "Blame Shifting, Teamwork", 
            2, 
            [
                ("A) Nu, ne asumăm eșecul împreună.", 0), 
                ("B) Îmi apăr partea mea de muncă.", 30), 
                ("C) Subliniez subtil cine a greșit.", 70), 
                ("D) Da, mă protejez cu orice preț, chiar dacă sacrific pe cineva.", 100)
            ]
        ),
        (
            "Îți asumi meritele pentru o idee care a fost a grupului sau a unui subaltern, dacă știi că nu te va contrazice nimeni?",
            "Credit Stealing, Integrity", 
            2, 
            [
                ("A) Nu, dau credit cui merită.", 0), 
                ("B) Spun 'noi am făcut'.", 30), 
                ("C) Dacă eu am prezentat-o, e ideea mea.", 70), 
                ("D) Da. Important e cine vinde ideea, nu cine a avut-o.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Răzbunare Activă / Distrugere) ---
        (
            "Ai răspândit vreodată un zvon fals sau exagerat despre cineva pentru a-i scădea reputația?",
            "Rumors, Slander, Reputation Attack", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Am participat la bârfe, dar nu am inițiat.", 30), 
                ("C) Doar dacă persoana merita o lecție.", 70), 
                ("D) Da, reputația e o armă și o folosesc.", 100)
            ]
        ),
        (
            "Te bucuri în sinea ta când un proiect condus de un rival eșuează?",
            "Schadenfreude, Rivalry, Toxicity", 
            3, 
            [
                ("A) Nu, e rău pentru firmă.", 0), 
                ("B) Nu mă afectează.", 20), 
                ("C) Puțin, recunosc.", 60), 
                ("D) Da, e o satisfacție imensă. Îmi confirmă valoarea.", 100)
            ]
        ),
        (
            "Ai șters vreodată munca cuiva sau ai modificat fișiere pentru a-l încurca?",
            "Active Sabotage, Malice", 
            3, 
            [
                ("A) Doamne ferește, nu!", 0), 
                ("B) Nu.", 0), 
                ("C) M-am gândit la asta la nervi.", 40), 
                ("D) Da, sau am ascuns resurse necesare.", 100)
            ]
        ),
        (
            "Consideri că într-o ierarhie, singurul mod de a urca este să dai pe alții la o parte?",
            "Worldview, Zero-Sum Game", 
            3, 
            [
                ("A) Nu, putem crește împreună.", 0), 
                ("B) Competiția e bună, dar fair-play.", 30), 
                ("C) Locurile la vârf sunt limitate, trebuie să fii dur.", 70), 
                ("D) Da. Ori mănânci, ori ești mâncat.", 100)
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