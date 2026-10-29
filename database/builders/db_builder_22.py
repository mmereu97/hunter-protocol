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
AXIS_ID = 22
AXIS_NAME = "Altruism"
# Pol Stânga (0): Egoist / Centrat pe sine / Tranzacțional
# Pol Dreapta (100): Altruist / Generos / Săritor

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
    # Punctaj: 0 = Egoist, 100 = Altruist
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Situații Comune) ---
        (
            "Un prieten te roagă să îl ajuți la mutatul mobilei într-o zi de sâmbătă, când aveai planuri de relaxare. Ce faci?",
            "Helping, Sacrifice, Friendship", 
            1, 
            [
                ("A) Inventez o scuză credibilă. Ziua mea liberă e sfântă.", 0), 
                ("B) Îl ajut doar dacă îmi plătește el pizza și berea după.", 30), 
                ("C) Îl ajut, deși nu prea am chef.", 70), 
                ("D) Merg cu plăcere, pentru asta sunt prietenii.", 100)
            ]
        ),
        (
            "Ești pe stradă și un turist vizibil rătăcit încearcă să se orienteze pe o hartă. Te oprești?",
            "Strangers, Helpfulness, Initiative", 
            1, 
            [
                ("A) Nu, am treabă. Să întrebe pe altcineva.", 0), 
                ("B) Doar dacă mă oprește el.", 30), 
                ("C) Îi explic rapid direcția.", 70), 
                ("D) Mă opresc, îl întreb unde vrea să ajungă și îi explic detaliat sau îl conduc.", 100)
            ]
        ),
        (
            "La supermarket, casierul te întreabă dacă vrei să donezi restul de câțiva lei pentru o cauză umanitară.",
            "Charity, Money, Generosity", 
            1, 
            [
                ("A) Nu. E o țeapă, banii nu ajung unde trebuie.", 0), 
                ("B) Refuz politicos.", 30), 
                ("C) Donez uneori.", 70), 
                ("D) Da, donez aproape de fiecare dată.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Beneficiu Personal) ---
        (
            "Un coleg de muncă este copleșit de sarcini și stă peste program. Tu ți-ai terminat treaba. Ce faci?",
            "Teamwork, Empathy, Work Ethic", 
            2, 
            [
                ("A) Plec acasă. Nu e problema mea că e lent.", 0), 
                ("B) Îi urez spor la treabă și plec.", 20), 
                ("C) Îl întreb dacă îl pot ajuta cu ceva mic.", 70), 
                ("D) Rămân să îl ajut să termine, ca să plecăm amândoi.", 100)
            ]
        ),
        (
            "Ai tendința să ajuți oamenii de la care știi sigur că nu vei primi niciodată nimic în schimb?",
            "Transactional, Pure Altruism", 
            2, 
            [
                ("A) Sincer, nu prea. Timpul înseamnă bani.", 0), 
                ("B) Rar. Prefer relațiile reciproc avantajoase.", 30), 
                ("C) Da, destul de des.", 70), 
                ("D) Da, asta este definiția bunătății.", 100)
            ]
        ),
        (
            "La o masă cu prietenii, a mai rămas o singură felie de pizza (sau prăjitură). O vrei, dar o vrea și altcineva. Ce faci?",
            "Sharing, Greed, Politeness", 
            2, 
            [
                ("A) O iau eu rapid.", 0), 
                ("B) Propun să o împărțim.", 30), 
                ("C) O las lui, dar cu un mic regret.", 70), 
                ("D) I-o ofer lui cu drag, îmi face plăcere să-l văd mulțumit.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Machiavelism / Psihopatie) ---
        (
            "Un rival sau o persoană care nu îți place are o problemă jenantă în public. Ai interveni să îl ajuți?",
            "Empathy vs Rivalry, Character", 
            3, 
            [
                ("A) Nu, mă bucur să îl văd suferind (Schadenfreude).", 0), 
                ("B) Mă prefac că nu văd.", 20), 
                ("C) L-aș ajuta, din principiu uman.", 70), 
                ("D) Da, aș sări imediat în ajutor. Suferința nu are culoare.", 100)
            ]
        ),
        (
            "Vezi pe cineva făcând pană pe ploaie torențială. Ești cu mașina. Oprești?",
            "Inconvenience, Helpfulness, Moral Duty", 
            3, 
            [
                ("A) Nu, îmi ud hainele/mașina.", 0), 
                ("B) Încetinesc, dar probabil trec mai departe.", 30), 
                ("C) Opresc doar dacă pare o situație critică (copii, bătrâni).", 60), 
                ("D) Opresc și ajut sau ofer un telefon/transport.", 100)
            ]
        ),
        (
            "Ce părere ai despre afirmația: 'Dacă nu ai grijă de tine însuți, nimeni nu o va face'?",
            "Worldview, Selfishness, Survival", 
            3, 
            [
                ("A) Este regula de aur. Fiecare pentru el.", 0), 
                ("B) Este adevărată în mare parte.", 30), 
                ("C) E adevărată, dar trebuie să avem grijă și de alții.", 70), 
                ("D) Falsă sau incompletă. Puterea stă în comunitate și ajutor reciproc.", 100)
            ]
        ),
        (
            "Un prieten are nevoie de un împrumut urgent, dar știi că returnează banii greu. Îl ajuți?",
            "Generosity, Risk, Relationship", 
            3, 
            [
                ("A) Nu. Nu amestec banii cu prietenia.", 0), 
                ("B) Inventez o scuză că nu am.", 20), 
                ("C) Îi dau o sumă mai mică, pe care sunt dispus să o pierd.", 70), 
                ("D) Da, nevoia lui e mai importantă decât riscul meu.", 100)
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