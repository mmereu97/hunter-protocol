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
AXIS_ID = 49
AXIS_NAME = "Tensiune Nervoasă"
# Pol Stânga (0): Relaxat / Flegmatic / Calm
# Pol Dreapta (100): Tensionat / Nerăbdător / Încordat

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
    # Punctaj: 0 = Relaxat, 100 = Tensionat
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Nerăbdare/Fizic) ---
        (
            "Cum te simți când trebuie să aștepți la o coadă care nu se mișcă sau ești blocat în trafic?",
            "Patience, Physical Reaction, Impatience", 
            1, 
            [
                ("A) Relaxat. Ascult muzică sau mă gândesc la ale mele.", 0), 
                ("B) Mă uit la ceas, dar sunt ok.", 30), 
                ("C) Devin agitat, bat din picior, oftez.", 70), 
                ("D) Simt că explodez. Îmi vine să urlu sau să plec.", 100)
            ]
        ),
        (
            "Cât de des simți o tensiune fizică în corp (maxilar încleștat, umeri ridicați, pumni strânși) fără un motiv clar?",
            "Somatic, Muscle Tension, Stress", 
            1, 
            [
                ("A) Niciodată. Sunt relaxat muscular.", 0), 
                ("B) Rar, doar după efort.", 30), 
                ("C) Seara, după muncă.", 70), 
                ("D) Constant. Sunt mereu încordat, gata de atac.", 100)
            ]
        ),
        (
            "Îți este greu să adormi seara pentru că ești încă 'în priză' sau agitat mental?",
            "Sleep, Hyperarousal, Insomnia", 
            1, 
            [
                ("A) Nu, adorm imediat.", 0), 
                ("B) Adorm destul de ușor.", 30), 
                ("C) Am nevoie de timp să mă calmez.", 70), 
                ("D) Da, mintea mea aleargă și corpul nu se relaxează.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Timp) ---
        (
            "Te deranjează oamenii care vorbesc sau se mișcă lent?",
            "Time Urgency, Frustration, Speed", 
            2, 
            [
                ("A) Nu, fiecare are ritmul lui.", 0), 
                ("B) Puțin, dacă mă grăbesc.", 30), 
                ("C) Da, mă irită.", 70), 
                ("D) Îngrozitor. Îmi vine să termin eu propozițiile în locul lor.", 100)
            ]
        ),
        (
            "Ai tendința să faci mai multe lucruri deodată (multitasking) pentru că simți că timpul nu îți ajunge?",
            "Multitasking, Rushing, Efficiency", 
            2, 
            [
                ("A) Nu, fac un singur lucru, pe îndelete.", 0), 
                ("B) Uneori, dacă e necesar.", 30), 
                ("C) Deseori fac 2-3 lucruri simultan.", 70), 
                ("D) Da, sunt mereu pe fugă, mănânc în timp ce lucrez.", 100)
            ]
        ),
        (
            "Cât de repede te poți relaxa complet după o situație stresantă (ex: o ședință grea)?",
            "Recovery, Cool Down", 
            2, 
            [
                ("A) Imediat. Las problemele la ușă.", 0), 
                ("B) În câteva minute.", 30), 
                ("C) Îmi ia câteva ore.", 60), 
                ("D) Rămân tensionat toată ziua, poate și a doua zi.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Agresivitate / Burnout / HTA) ---
        (
            "Ți se întâmplă să te răstești la oameni apropiați doar pentru că ești tensionat, chiar dacă ei nu au făcut nimic?",
            "Snapping, Irritability, Displacement", 
            3, 
            [
                ("A) Nu, nu îmi vărs nervii pe alții.", 0), 
                ("B) Foarte rar, și îmi cer scuze.", 30), 
                ("C) Se mai întâmplă când sunt copleșit.", 70), 
                ("D) Da, sunt ca un butoi de pulbere. Orice scânteie mă aprinde.", 100)
            ]
        ),
        (
            "Simți o nevoie constantă de a face ceva, fiindu-ți imposibil să stai pur și simplu degeaba?",
            "Restlessness, Relaxation Induced Anxiety", 
            3, 
            [
                ("A) Nu, ador să lenevesc.", 0), 
                ("B) Pot sta degeaba fără probleme.", 30), 
                ("C) Mă simt vinovat dacă nu sunt productiv.", 70), 
                ("D) Da. Relaxarea mă agită. Trebuie să fiu activ.", 100)
            ]
        ),
        (
            "Ai ticuri nervoase (ros unghii, bătut din picior, jucat cu pixul) cauzate de tensiune?",
            "Fidgeting, Nervous Habits", 
            3, 
            [
                ("A) Nu.", 0), 
                ("B) Rar.", 20), 
                ("C) Am câteva obiceiuri când sunt stresat.", 60), 
                ("D) Da, nu pot sta nemișcat, am o energie nervoasă constantă.", 100)
            ]
        ),
        (
            "Te simți adesea copleșit de un sentiment de urgență, chiar și pentru lucruri care nu sunt importante?",
            "False Urgency, Stress Addiction", 
            3, 
            [
                ("A) Nu, sunt calm și metodic.", 0), 
                ("B) Doar la deadline-uri reale.", 30), 
                ("C) Uneori îmi creez singur presiune.", 70), 
                ("D) Da, totul pare o urgență de gradul zero. Trăiesc în modul 'luptă sau fugi'.", 100)
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