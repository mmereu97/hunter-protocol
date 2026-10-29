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
AXIS_ID = 87
AXIS_NAME = "Tradiționalism"
# Pol Stânga (0): Liberal / Modern / Progresist
# Pol Dreapta (100): Tradiționalist / Conservator / Familist

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
    # Punctaj: 0 = Modern (Liberal), 100 = Tradițional (Conservator)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Valori Generale) ---
        (
            "Cât de important este pentru tine să respecți obiceiurile și tradițiile (sărbători, ritualuri de familie, etichetă)?",
            "Customs, Family, Heritage", 
            1, 
            [
                ("A) Deloc. Sunt demodate și inutile.", 0), 
                ("B) Le respect dacă sunt distractive.", 30), 
                ("C) Sunt importante, ne definesc.", 70), 
                ("D) Sfinte. Ele mențin ordinea și identitatea noastră.", 100)
            ]
        ),
        (
            "Ce părere ai despre schimbările sociale rapide din ultimii ani (rolurile de gen, structura familiei)?",
            "Society, Progress vs Conservation", 
            1, 
            [
                ("A) Sunt excelente, era nevoie de progres.", 0), 
                ("B) Unele sunt bune, altele exagerate.", 30), 
                ("C) Sunt sceptic, se pierde esența.", 70), 
                ("D) Sunt periculoase. Societatea își pierde valorile morale.", 100)
            ]
        ),
        (
            "În luarea deciziilor importante, te gândești la 'ce ar spune lumea' sau familia?",
            "Social Pressure, Reputation, Autonomy", 
            1, 
            [
                ("A) Nu, e viața mea, fac ce vreau.", 0), 
                ("B) Puțin, nu vreau să îmi supăr părinții.", 30), 
                ("C) Țin cont de părerea comunității.", 70), 
                ("D) Da, onoarea familiei/numelui este crucială.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Autoritate) ---
        (
            "La locul de muncă, preferi o structură ierarhică clară (șef-subaltern) sau una plată/egalitară?",
            "Hierarchy, Work Structure", 
            2, 
            [
                ("A) Egalitară. Toți suntem colegi.", 0), 
                ("B) Flexibilă.", 30), 
                ("C) Ierarhică, e mai clar așa.", 70), 
                ("D) Ierarhie strictă. Trebuie să știi cine comandă.", 100)
            ]
        ),
        (
            "Ce părere ai despre tatuaje, piercing-uri sau stiluri vestimentare neconvenționale la birou?",
            "Appearance, Norms, Judgement", 
            2, 
            [
                ("A) Sunt forme de exprimare, nu contează.", 0), 
                ("B) Dacă nu sunt ofensatoare, e ok.", 30), 
                ("C) Ar trebui evitate într-un mediu serios.", 70), 
                ("D) Inacceptabile. Arată lipsă de respect și profesionalism.", 100)
            ]
        ),
        (
            "Crezi că tinerii din ziua de azi ar trebui să asculte mai mult de sfaturile bătrânilor?",
            "Respect for Elders, Wisdom", 
            2, 
            [
                ("A) Nu neapărat, lumea s-a schimbat.", 0), 
                ("B) Depinde de bătrân.", 30), 
                ("C) Da, experiența contează.", 70), 
                ("D) Absolut. Lipsa de respect față de vârstnici e o problemă gravă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Rigiditate / Intoleranță / Conflict Generațional) ---
        (
            "Dacă copilul tău (sau un apropiat) ar adopta un stil de viață complet opus valorilor tale tradiționale, cum ai reacționa?",
            "Tolerance, Family, Values", 
            3, 
            [
                ("A) L-aș susține necondiționat.", 0), 
                ("B) Aș fi dezamăgit, dar e viața lui.", 30), 
                ("C) Aș încerca să îl aduc pe calea dreaptă.", 70), 
                ("D) Nu aș putea accepta. Ar fi o rușine pentru familie.", 100)
            ]
        ),
        (
            "Consideri că moralitatea este absolută (dată de religie/tradiție) sau relativă (fiecare decide)?",
            "Morality, Ethics, Religion", 
            3, 
            [
                ("A) Relativă. Depinde de context.", 0), 
                ("B) Există reguli de bun simț, dar sunt flexibile.", 30), 
                ("C) Moralitatea clasică e cea mai bună.", 70), 
                ("D) Absolută. Regulile străvechi nu se discută.", 100)
            ]
        ),
        (
            "Te simți mai confortabil când lucrurile rămân la fel ('Pe vremea mea...') decât atunci când se inovează?",
            "Nostalgia, Resistance to Change", 
            3, 
            [
                ("A) Nu, ador noutatea și viitorul.", 0), 
                ("B) Mă adaptez.", 30), 
                ("C) Prefer stabilitatea trecutului.", 60), 
                ("D) Da. Inovația a distrus multe lucruri bune.", 100)
            ]
        ),
        (
            "Cât de mult contează religia sau spiritualitatea tradițională în deciziile tale zilnice?",
            "Spirituality, Dogma, Life Guide", 
            3, 
            [
                ("A) Deloc. Sunt ateu/agnostic.", 0), 
                ("B) E ceva cultural, nu decisiv.", 30), 
                ("C) E un ghid moral important.", 70), 
                ("D) Este fundamentul vieții mele.", 100)
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