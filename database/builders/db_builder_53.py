import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 53
AXIS_NAME = "Psihopatie"
# Pol Stânga (0): Empatic / Conștiincios
# Pol Dreapta (100): Psihopat / Rece / Fără Remușcări

# 3. HASHING
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
    # Punctaj: 0 = Empatic, 100 = Psihopat (Risc Maxim)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Răceală Emoțională/Plictiseală) ---
        (
            "Cum reacționezi de obicei când vezi pe cineva plângând în public?",
            "Empathy, Reaction to Distress", 
            1, 
            [
                ("A) Mă simt trist și aș vrea să ajut.", 0), 
                ("B) Mă simt stânjenit, dar empatic.", 30), 
                ("C) Nu simt nimic, e problema lor.", 70), 
                ("D) Mă irită sau mi se pare patetic.", 100)
            ]
        ),
        (
            "Cât de repede te plictisești de rutină sau de siguranță?",
            "Need for Stimulation, Boredom", 
            1, 
            [
                ("A) Îmi place siguranța.", 0), 
                ("B) Rezist bine la rutină.", 30), 
                ("C) Mă plictisesc repede.", 60), 
                ("D) Insuportabil de repede. Am nevoie constantă de acțiune și risc.", 100)
            ]
        ),
        (
            "Dacă ai făcut o greșeală care a afectat pe altcineva, cât de mult te frământă sentimentul de vinovăție?",
            "Guilt, Remorse, Conscience", 
            1, 
            [
                ("A) Foarte mult, nu pot dormi.", 0), 
                ("B) Mă simt prost și îmi cer scuze.", 30), 
                ("C) Trec peste destul de repede.", 70), 
                ("D) Deloc. Ce s-a întâmplat, s-a întâmplat. Nu are rost să regret.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Impulsivitate/Utilitarism) ---
        (
            "Ești dispus să îți asumi riscuri mari (fizice sau financiare) doar pentru plăcerea jocului?",
            "Risk Taking, Impulsivity", 
            2, 
            [
                ("A) Nu, sunt precaut.", 0), 
                ("B) Doar riscuri calculate.", 30), 
                ("C) Uneori, viața trebuie trăită.", 70), 
                ("D) Da, trăiesc pentru adrenalină, indiferent de consecințe.", 100)
            ]
        ),
        (
            "Dacă cineva stă în calea succesului tău, cât de departe ai merge pentru a-l înlătura?",
            "Ruthlessness, Ambition, Obstacles", 
            2, 
            [
                ("A) Aș căuta o altă cale sau aș negocia.", 0), 
                ("B) Aș concura corect.", 30), 
                ("C) L-aș sabota subtil dacă e nevoie.", 70), 
                ("D) Aș face orice e necesar. Îl calc în picioare.", 100)
            ]
        ),
        (
            "Ți s-a spus vreodată că ai un 'farmec superficial' sau că poți convinge pe oricine de orice?",
            "Superficial Charm, Manipulation", 
            2, 
            [
                ("A) Nu, sunt destul de timid.", 0), 
                ("B) Sunt sociabil, dar sincer.", 30), 
                ("C) Da, știu să vorbesc frumos când vreau ceva.", 70), 
                ("D) Da, pot vrăji pe oricine. E un talent.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Criminalitate / Cruzime / Agresivitate) ---
        (
            "Ai simțit vreodată plăcere văzând un animal sau o persoană suferind fizic?",
            "Sadism, Cruelty, Callousness", 
            3, 
            [
                ("A) Doamne ferește, nu! Mă oripilează.", 0), 
                ("B) Nu, îmi întorc privirea.", 20), 
                ("C) Nu plăcere, dar curiozitate.", 70), 
                ("D) Da, este fascinant sau satisfăcător.", 100)
            ]
        ),
        (
            "Ai încălcat vreodată legea (furt, vandalism, agresiune) doar pentru că ai simțit că poți scăpa?",
            "Criminal Versatility, Law Breaking", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Poate lucruri minore în copilărie.", 20), 
                ("C) Câteva 'scurtături' legale.", 60), 
                ("D) Da. Legile sunt pentru cei care se lasă prinși.", 100)
            ]
        ),
        (
            "Când minți, simți vreo emoție fizică (transpirație, puls mărit) sau rămâi complet calm?",
            "Lying, Physiological Response", 
            3, 
            [
                ("A) Mă panichez și mă înroșesc.", 0), 
                ("B) Am emoții, dar le ascund.", 30), 
                ("C) Sunt destul de calm.", 70), 
                ("D) Sunt gheață. Nu am nicio reacție, pot minți la detectorul de minciuni.", 100)
            ]
        ),
        (
            "Consideri că majoritatea oamenilor sunt slabi și merită să fie exploatați de cei puternici?",
            "Predatory Worldview, Social Darwinism", 
            3, 
            [
                ("A) Nu, toți oamenii merită respect.", 0), 
                ("B) Nu neapărat, dar cei puternici câștigă.", 30), 
                ("C) Lumea e dură, supraviețuiește cine poate.", 60), 
                ("D) Da. Există lupi și oi. Eu sunt lup.", 100)
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