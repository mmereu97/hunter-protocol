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
AXIS_ID = 27
AXIS_NAME = "Prudență / Deliberare"
# Pol Stânga (0): Spontan / Riscant / Instinctiv
# Pol Dreapta (100): Calculat / Precaut / Analitic

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
    # Punctaj: 0 = Spontan, 100 = Prudent
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Decizii Zilnice) ---
        (
            "Când trebuie să iei o decizie importantă, cum procedezi de obicei?",
            "Decision Making, Speed, Analysis", 
            1, 
            [
                ("A) Mă bazez pe instinct și decid pe loc.", 0), 
                ("B) Mă gândesc puțin, dar nu ezit prea mult.", 30), 
                ("C) Cântăresc bine opțiunile înainte.", 70), 
                ("D) Fac liste pro/contra și analizez toate scenariile posibile.", 100)
            ]
        ),
        (
            "Cât de des ți se întâmplă să spui sau să faci ceva și să regreți imediat pentru că nu te-ai gândit la consecințe?",
            "Regret, Impulse Control, Forethought", 
            1, 
            [
                ("A) Foarte des. Sunt o fire impulsivă.", 0), 
                ("B) Uneori, când sunt sub presiune.", 30), 
                ("C) Rar, de obicei sunt atent.", 70), 
                ("D) Niciodată. Îmi măsor fiecare cuvânt și faptă.", 100)
            ]
        ),
        (
            "Dacă un prieten îți propune o excursie spontană cu plecare în 2 ore, ce faci?",
            "Spontaneity, Planning, Flexibility", 
            1, 
            [
                ("A) Îmi fac bagajul și am plecat! Ador spontaneitatea.", 0), 
                ("B) Probabil accept, sună distractiv.", 30), 
                ("C) Aș ezita, trebuie să verific ce obligații am.", 70), 
                ("D) Refuz. Am nevoie de timp să mă organizez și să planific.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Bani/Siguranță) ---
        (
            "În chestiuni financiare (investiții, achiziții mari), care este stilul tău?",
            "Money, Risk Aversion, Strategy", 
            2, 
            [
                ("A) Îmi place riscul. Pot câștiga mult sau pierde tot.", 0), 
                ("B) Sunt dispus la riscuri moderate.", 30), 
                ("C) Prefer siguranța, chiar dacă profitul e mic.", 70), 
                ("D) Analizez fiecare detaliu și aleg varianta cu risc zero.", 100)
            ]
        ),
        (
            "Când pleci la drum lung, îți planifici ruta și opririle în detaliu?",
            "Travel, Preparation, Caution", 
            2, 
            [
                ("A) Nu, pornesc GPS-ul și văd eu pe drum.", 0), 
                ("B) Știu în mare pe unde o iau.", 30), 
                ("C) Verific traficul și vremea înainte.", 70), 
                ("D) Da, știu exact unde opresc, cât combustibil am și rutele de rezervă.", 100)
            ]
        ),
        (
            "Ce părere ai despre proverbul 'Măsoară de două ori, taie o dată'?",
            "Philosophy, Work Style", 
            2, 
            [
                ("A) E pentru cei nehotărâți. Eu tai și rezolv.", 0), 
                ("B) E un sfat bun, dar uneori te încetinește.", 30), 
                ("C) Îl aplic des.", 70), 
                ("D) Este regula mea de bază în orice fac.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Dezinhibiție vs Analysis Paralysis) ---
        (
            "Ți se întâmplă să pierzi oportunități bune pentru că ai stat prea mult să le analizezi (Analysis Paralysis)?",
            "Hesitation, Overthinking, Missed Opportunities", 
            3, 
            [
                ("A) Nu, eu sar pe oportunitate imediat.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori am ezitat prea mult.", 60), 
                ("D) Da, des. Frica de a greși mă blochează.", 100)
            ]
        ),
        (
            "Ai tendința de a anticipa mereu ce ar putea merge prost (scenarii negative)?",
            "Pessimism, Risk Assessment, Anxiety", 
            3, 
            [
                ("A) Nu, sunt optimist, cred că va fi bine.", 0), 
                ("B) Mă gândesc la riscuri, dar nu exagerez.", 30), 
                ("C) Da, e bine să fii pregătit.", 70), 
                ("D) Da, văd pericole la tot pasul și îmi iau măsuri de precauție.", 100)
            ]
        ),
        (
            "Te consideri o persoană care gândește mult înainte să vorbească?",
            "Communication, Filter, Diplomacy", 
            3, 
            [
                ("A) Nu, spun ce am pe suflet imediat.", 0), 
                ("B) Uneori vorbesc prea repede.", 30), 
                ("C) De obicei îmi aleg cuvintele.", 70), 
                ("D) Da, analizez impactul fiecărui cuvânt.", 100)
            ]
        ),
        (
            "Dacă ai o idee de afacere sau proiect, cât timp îți ia să o pui în practică?",
            "Action, Strategy, Delay", 
            3, 
            [
                ("A) O încep în aceeași zi.", 0), 
                ("B) Câteva zile, cât fac un plan sumar.", 30), 
                ("C) Săptămâni de cercetare.", 70), 
                ("D) Luni sau ani. Nu încep până nu am planul perfect.", 100)
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