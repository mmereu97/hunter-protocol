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
AXIS_ID = 82
AXIS_NAME = "Stil de Învățare"
# Pol Stânga (0): Teoretic / Carte / Conceptual
# Pol Dreapta (100): Practic / Experiment / Trial & Error

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
    # Punctaj: 0 = Teoretic, 100 = Practic
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Abordare Generală) ---
        (
            "Când îți cumperi un aparat nou (telefon, electrocasnic), cum înveți să îl folosești?",
            "Learning, Manuals, Tech", 
            1, 
            [
                ("A) Citesc manualul de instrucțiuni cap-coadă înainte să îl pornesc.", 0), 
                ("B) Mă uit peste ghidul rapid.", 30), 
                ("C) Îl pornesc și mă uit în manual doar dacă mă blochez.", 70), 
                ("D) Îl pornesc și butonez tot până îmi dau seama cum merge.", 100)
            ]
        ),
        (
            "Dacă vrei să înveți să gătești un fel nou de mâncare, ce preferi?",
            "Hobbies, Instructions, Intuition", 
            1, 
            [
                ("A) Să am o rețetă exactă, cu gramaje, pe care o respect strict.", 0), 
                ("B) Să urmăresc un tutorial video detaliat.", 30), 
                ("C) Să știu ingredientele și să improvizez.", 70), 
                ("D) Să gust și să experimentez până iese ceva bun.", 100)
            ]
        ),
        (
            "În școală sau la cursuri, ce stil de predare ți se părea cel mai eficient?",
            "Education, Theory vs Practice", 
            1, 
            [
                ("A) Prelegeri teoretice, bine structurate, cu notițe.", 0), 
                ("B) Discuții și analize de concepte.", 30), 
                ("C) Studii de caz concrete.", 70), 
                ("D) Laboratoare sau ateliere practice ('Hands-on').", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Rezolvare Probleme/Muncă) ---
        (
            "Când te confrunți cu o problemă la muncă, cum preferi să găsești soluția?",
            "Problem Solving, Analysis vs Action", 
            2, 
            [
                ("A) Mă retrag, analizez datele și fac un plan mental complet.", 0), 
                ("B) Caut documentație despre cum au făcut alții.", 30), 
                ("C) Încerc o soluție rapidă să văd ce se întâmplă.", 70), 
                ("D) Încerc mai multe variante rapid (Trial & Error) până merge una.", 100)
            ]
        ),
        (
            "Ce te plictisește mai tare într-o ședință sau training?",
            "Boredom, Abstract vs Concrete", 
            2, 
            [
                ("A) Lipsa de structură și logica deficitară.", 0), 
                ("B) Când se sare de la un subiect la altul.", 30), 
                ("C) Prea multe detalii teoretice fără aplicație.", 70), 
                ("D) Teoria pură. Dacă nu facem ceva practic, adorm.", 100)
            ]
        ),
        (
            "Cum preferi să primești feedback despre munca ta?",
            "Feedback, Style", 
            2, 
            [
                ("A) În scris, detaliat, ca să pot analiza.", 0), 
                ("B) Într-o discuție unu-la-unu.", 30), 
                ("C) Prin exemple de 'așa da, așa nu'.", 60), 
                ("D) Să mi se arate fizic cum se face mai bine.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: OCPD / ADHD / Rigiditate Cognitivă) ---
        (
            "Ești genul de persoană care trebuie să înțeleagă 'DE CE' funcționează un lucru înainte să îl folosească?",
            "Curiosity, Systems Thinking, Action", 
            3, 
            [
                ("A) Da, absolut. Altfel nu am încredere.", 0), 
                ("B) De cele mai multe ori.", 30), 
                ("C) Nu neapărat, dacă funcționează e ok.", 70), 
                ("D) Nu. Mă interesează 'CUM' îl folosesc să obțin rezultatul, nu teoria din spate.", 100)
            ]
        ),
        (
            "Cât de mult te temi să faci greșeli atunci când înveți ceva nou?",
            "Failure, Perfectionism vs Growth", 
            3, 
            [
                ("A) Mult. Prefer să studiez bine înainte să încerc, ca să nu greșesc.", 0), 
                ("B) Sunt precaut.", 30), 
                ("C) Greșelile sunt parte din proces.", 70), 
                ("D) Deloc. 'Fail fast, learn fast' e motto-ul meu.", 100)
            ]
        ),
        (
            "Dacă ai de asamblat o piesă de mobilier (IKEA), cum procedezi?",
            "Assembly, Process, Patience", 
            3, 
            [
                ("A) Sortez toate șuruburile și citesc instrucțiunile de două ori.", 0), 
                ("B) Urmăresc schițele pas cu pas.", 30), 
                ("C) Mă uit la poze și asamblez.", 70), 
                ("D) Mă prind eu unde vine fiecare piesă. Mă uit la foaie doar dacă rămân piese în plus.", 100)
            ]
        ),
        (
            "Preferi un mentor care îți explică conceptele și filozofia (Guru) sau unul care te pune la treabă (Antrenor)?",
            "Mentorship, Preferences", 
            3, 
            [
                ("A) Guru. Vreau să înțeleg esența.", 0), 
                ("B) O combinație.", 30), 
                ("C) Antrenor.", 60), 
                ("D) Antrenor. Vreau exerciții, practică și transpirație, nu vorbe.", 100)
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