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
AXIS_ID = 90
AXIS_NAME = "Integritate (Risc Fraudă)"
# Pol 0: Integru / Onest
# Pol 100: Risc Fraudă / Coruptibil

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

    # Punctaj: 100 = RISC FRAUDĂ (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Furturi mici / Raționalizare) ---
        (
            "Crezi că este acceptabil să iei acasă mici consumabile de la birou (pixuri, hârtie, capse) dacă firma are buget mare?",
            "Petty Theft, Rationalization, Entitlement", 
            1, 
            [
                ("A) Nu, este tot furt, indiferent de valoare.", 0), 
                ("B) Evit, dar nu condamn pe cine o face.", 20), 
                ("C) Da, sunt lucruri mărunte, nu sărăcește firma.", 70), 
                ("D) Da, la cât muncesc, mi se cuvin.", 100)
            ]
        ),
        (
            "Dacă ai găsi o modalitate de a 'fenta' sistemul de pontaj pentru a fi plătit câteva ore în plus fără să muncești, ai face-o?",
            "Time Theft, Integrity, Work Ethic", 
            1, 
            [
                ("A) Nu, ar fi incorect.", 0), 
                ("B) M-ar tenta, dar mi-ar fi frică să nu fiu prins.", 30), 
                ("C) Probabil că da, dacă riscul e mic.", 70), 
                ("D) Cu siguranță. Dacă sistemul are o gaură, e vina lor.", 100)
            ]
        ),
        (
            "Ce părere ai despre angajații care își decontează cheltuieli personale pe firma angajatorului?",
            "Expense Fraud, Ethics", 
            1, 
            [
                ("A) Este o fraudă și trebuie sancționată.", 0), 
                ("B) Nu e ok, dar mulți o fac.", 30), 
                ("C) Dacă sumele sunt mici, e de înțeles.", 60), 
                ("D) E un beneficiu nescris. Toată lumea o face.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Corupție / Mită / Loialitate) ---
        (
            "Dacă un furnizor îți oferă un cadou scump (ex: un ceas sau o vacanță) pentru a-i prefera contractul, ce faci?",
            "Bribery, Corruption, Professionalism", 
            2, 
            [
                ("A) Refuz categoric și raportez incidentul.", 0), 
                ("B) Refuz politicos.", 20), 
                ("C) Accept dacă nu afectează calitatea contractului.", 80), 
                ("D) Accept bucuros. Așa merg afacerile.", 100)
            ]
        ),
        (
            "Dacă știi că firma face profituri uriașe și te plătește puțin, consideri că e justificat să 'îți completezi veniturile' prin metode neoficiale?",
            "Justification, Revenge, Fraud", 
            2, 
            [
                ("A) Nu. Dacă nu îmi convine salariul, plec.", 0), 
                ("B) E frustrant, dar nu aș fura.", 20), 
                ("C) E o zonă gri morală.", 60), 
                ("D) Da. E o formă de dreptate socială.", 100)
            ]
        ),
        (
            "Ai acoperi un coleg care a comis o fraudă, dacă te-ar ruga și ți-ar promite o parte din câștig?",
            "Complicity, Loyalty vs Integrity", 
            2, 
            [
                ("A) Nu, l-aș denunța imediat.", 0), 
                ("B) Nu m-aș băga, dar nici nu l-aș pârî.", 30), 
                ("C) M-aș gândi, depinde de risc.", 70), 
                ("D) Da, aș intra în combinație.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Risc Penal / Fraudă Majoră) ---
        (
            "Dacă ai lucra la o bancă și ai putea transfera o sumă mare de bani într-un cont secret fără nicio urmă, ai face-o?",
            "Grand Theft, Opportunity, Dark Triad", 
            3, 
            [
                ("A) Nu. Nu aș putea trăi cu mine.", 0), 
                ("B) M-aș gândi, e o tentație mare.", 30), 
                ("C) Probabil da, dacă sunt sigur 100% că scap.", 80), 
                ("D) Imediat. Ăsta e visul oricui.", 100)
            ]
        ),
        (
            "Ai falsificat vreodată documente oficiale (semnături, facturi, diplome) pentru a obține un avantaj?",
            "Forgery, Deception, History", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Poate o scutire medicală în școală.", 20), 
                ("C) Da, dar pentru lucruri minore.", 70), 
                ("D) Da, am făcut ce a trebuit ca să reușesc.", 100)
            ]
        ),
        (
            "Consideri că legile sunt doar niște sugestii pentru oamenii inteligenți care știu să nu fie prinși?",
            "Antisocial Attitudes, Law", 
            3, 
            [
                ("A) Nu, legea e fundamentul societății.", 0), 
                ("B) Legea e rigidă, dar trebuie respectată.", 30), 
                ("C) Unele legi pot fi ocolite.", 70), 
                ("D) Da. Doar proștii se lasă limitați de reguli.", 100)
            ]
        ),
        (
            "Dacă ai vinde o mașină care are un defect ascuns grav, l-ai spune cumpărătorului?",
            "Transaction, Honesty, Safety", 
            3, 
            [
                ("A) Da, obligatoriu. E periculos.", 0), 
                ("B) I-aș da indicii să verifice.", 30), 
                ("C) Nu, e datoria lui să verifice ('Caveat Emptor').", 70), 
                ("D) Nu, l-aș ascunde cât mai bine ca să iau prețul maxim.", 100)
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