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
AXIS_ID = 8
AXIS_NAME = "Sentimentalism"
# Pol Stânga (0): Rece / Rațional / Detașat
# Pol Dreapta (100): Empatic / Sentimental / Emotiv

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
    # Punctaj: 0 = Rece (Logic), 100 = Sentimental (Inimă)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Decizii) ---
        (
            "Când trebuie să iei o decizie importantă, pe ce te bazezi în primul rând?",
            "Decision Making, Logic vs Emotion", 
            1, 
            [
                ("A) Strict pe fapte, cifre și logică. Emoțiile încurcă.", 0), 
                ("B) Analizez logic, dar țin cont și de cum mă simt.", 30), 
                ("C) Intuiția și sentimentele contează mult pentru mine.", 70), 
                ("D) Îmi ascult inima. Dacă nu se simte bine, nu fac.", 100)
            ]
        ),
        (
            "Cum reacționezi de obicei la filmele, cărțile sau știrile triste?",
            "Empathy, Crying, Sensitivity", 
            1, 
            [
                ("A) Nu mă afectează vizibil. Este doar o poveste.", 0), 
                ("B) Pot fi mișcat, dar rar plâng.", 30), 
                ("C) Mi se umezesc ochii destul de des.", 70), 
                ("D) Plâng ușor și mă consumă emoțional.", 100)
            ]
        ),
        (
            "Cât de greu îți este să te desparți de obiecte vechi care au amintiri (bilete, cadouri mici, haine vechi)?",
            "Nostalgia, Hoarding, Memory", 
            1, 
            [
                ("A) Deloc. Dacă nu e util, îl arunc.", 0), 
                ("B) Păstrez doar lucrurile cu adevărat importante.", 30), 
                ("C) Mă atașez de obiecte și le arunc cu greu.", 70), 
                ("D) Păstrez tot. Fiecare obiect are o poveste și un suflet.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Relații/Empatie) ---
        (
            "Dacă un prieten plânge în fața ta, cum te simți?",
            "Empathy, Reaction to Distress", 
            2, 
            [
                ("A) Incomod. Nu știu ce să fac, prefer să fiu rațional.", 0), 
                ("B) Încerc să îi ofer o soluție practică la problemă.", 30), 
                ("C) Îl compătimesc și îl ascult.", 70), 
                ("D) Simt durerea lui fizic, îmi vine și mie să plâng.", 100)
            ]
        ),
        (
            "Cum gestionezi despărțirile sau 'la revedere' (aeroport, mutări)?",
            "Goodbyes, Attachment, Emotion", 
            2, 
            [
                ("A) Scurt și la obiect. Nu îmi plac dramele.", 0), 
                ("B) Sunt politicos, poate puțin trist.", 30), 
                ("C) Sunt momente grele, mă emoționez.", 70), 
                ("D) Plâng și mă afectează zile întregi.", 100)
            ]
        ),
        (
            "Te consideri o persoană nostalgică, care se gândește des la 'vremurile bune' din trecut?",
            "Nostalgia, Past Focus", 
            2, 
            [
                ("A) Nu. Trăiesc în prezent și viitor.", 0), 
                ("B) Rareori, poate la o reuniune.", 30), 
                ("C) Da, îmi place să rememorez trecutul.", 70), 
                ("D) Foarte des. Trecutul pare mereu mai frumos.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Psihopatie/Răceală vs Instabilitate) ---
        (
            "Dacă ar trebui să concediezi un angajat simpatic dar incompetent, cât de greu ți-ar fi?",
            "Management, Tough-mindedness, Empathy", 
            3, 
            [
                ("A) Ușor. Afacerile sunt afaceri, competența primează.", 0), 
                ("B) Neplăcut, dar aș face-o rapid.", 30), 
                ("C) Foarte greu, m-aș simți vinovat.", 70), 
                ("D) Nu aș putea să o fac. Aș căuta orice altă soluție.", 100)
            ]
        ),
        (
            "Ce părere ai despre manifestarea emoțiilor în public?",
            "Social Norms, Emotional Expression", 
            3, 
            [
                ("A) Este un semn de slăbiciune sau lipsă de control.", 0), 
                ("B) Ar trebui evitată, e o chestiune privată.", 30), 
                ("C) E naturală, suntem oameni.", 70), 
                ("D) Este o dovadă de autenticitate și curaj.", 100)
            ]
        ),
        (
            "Cât de mult te afectează suferința animalelor?",
            "Animals, Empathy, Sensitivity", 
            3, 
            [
                ("A) Puțin. Sunt animale, nu oameni.", 0), 
                ("B) Nu îmi place să văd, dar e parte din natură.", 30), 
                ("C) Mă întristează vizibil.", 70), 
                ("D) Nu pot suporta. Donez, salvez, sufăr pentru ele.", 100)
            ]
        ),
        (
            "Îți bazezi vreodată acțiunile pe 'presimțiri' sau 'vibrații', chiar dacă datele spun altceva?",
            "Intuition vs Logic, Mysticism", 
            3, 
            [
                ("A) Niciodată. Datele sunt sfinte.", 0), 
                ("B) Sunt sceptic, verific datele de două ori.", 30), 
                ("C) Uneori, dacă instinctul e puternic.", 70), 
                ("D) Da, intuiția mea nu dă greș niciodată.", 100)
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