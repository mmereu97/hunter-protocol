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
AXIS_ID = 63
AXIS_NAME = "Interes Social (RIASEC S)"
# Pol Stânga (0): Lucru cu Obiecte / Tehnic
# Pol Dreapta (100): Lucru cu Oameni / Ajutor

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
    # Punctaj: 0 = Obiecte, 100 = Oameni
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe Generale) ---
        (
            "Dacă ai putea alege între un job unde repari mașinării complexe toată ziua (fără să vorbești cu nimeni) și un job unde consiliezi oameni cu probleme, ce alegi?",
            "Career, People vs Things", 
            1, 
            [
                ("A) Mașinăriile, clar. Sunt logice și nu se plâng.", 0), 
                ("B) Probabil mașinăriile.", 30), 
                ("C) Consilierea, dacă pot ajuta.", 70), 
                ("D) Consilierea. Vreau să lucrez cu suflete, nu cu fiare.", 100)
            ]
        ),
        (
            "Cât de multă răbdare ai să explici cuiva cum să facă un lucru, pas cu pas, chiar dacă înțelege greu?",
            "Teaching, Patience, Pedagogy", 
            1, 
            [
                ("A) Zero. Prefer să fac eu în locul lui.", 0), 
                ("B) Puțină. Mă irită dacă trebuie să repet.", 30), 
                ("C) Am răbdare.", 70), 
                ("D) Foarte multă. Îmi place să învăț oamenii.", 100)
            ]
        ),
        (
            "În grupul tău de prieteni, ești cel la care vine lumea să se plângă sau să ceară sfaturi emoționale?",
            "Empathy, Social Role, Listening", 
            1, 
            [
                ("A) Nu. Știu că nu mă pricep la asta.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori.", 70), 
                ("D) Da, sunt 'psihologul' grupului.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Voluntariat/Energie) ---
        (
            "Dacă ar trebui să faci voluntariat, ce activitate ai alege?",
            "Volunteering, Interests", 
            2, 
            [
                ("A) Să construiesc case sau să plantez copaci (fizic).", 0), 
                ("B) Să mă ocup de contabilitatea ONG-ului (date).", 20), 
                ("C) Să organizez evenimente.", 60), 
                ("D) Să lucrez cu copii defavorizați sau bătrâni (social).", 100)
            ]
        ),
        (
            "Cum te simți după o zi în care a trebuit să asculți problemele altora și să încerci să îi ajuți?",
            "Emotional Labor, Burnout vs Satisfaction", 
            2, 
            [
                ("A) Epuizat și iritat. Nu e pentru mine.", 0), 
                ("B) Obosit.", 30), 
                ("C) Bine, simt că am fost util.", 70), 
                ("D) Împlinit. Asta îmi dă energie și sens.", 100)
            ]
        ),
        (
            "Te-ar atrage o carieră în asistență socială, psihologie, resurse umane sau medicină?",
            "Career Interest, RIASEC S", 
            2, 
            [
                ("A) Nu, deloc.", 0), 
                ("B) Poate medicină (partea tehnică/chirurgie).", 30), 
                ("C) Resurse umane ar fi ok.", 70), 
                ("D) Da, sunt domeniile mele ideale.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Sindromul Salvatorului / Neglijență de sine) ---
        (
            "Cât de important este pentru tine să simți că munca ta are un impact direct și pozitiv asupra vieții altor oameni?",
            "Values, Meaning, Impact", 
            3, 
            [
                ("A) Puțin. Mă interesează salariul și provocarea tehnică.", 0), 
                ("B) E un bonus.", 30), 
                ("C) Important.", 70), 
                ("D) Crucial. Nu pot face o muncă care nu ajută pe nimeni.", 100)
            ]
        ),
        (
            "Te simți confortabil să lucrezi cu oameni bolnavi, supărați, vulnerabili sau dificili?",
            "Tolerance, Compassion, Resilience", 
            3, 
            [
                ("A) Nu, mă deprimă sau mă enervează.", 0), 
                ("B) Prefer să evit.", 20), 
                ("C) Mă descurc.", 70), 
                ("D) Da, am empatia necesară să îi susțin.", 100)
            ]
        ),
        (
            "Preferi să rezolvi tu problema rapid (tehnic) sau să îi înveți pe alții cum să o facă (pedagogic)?",
            "Mentoring, Doing vs Teaching", 
            3, 
            [
                ("A) Să o rezolv eu. E mai eficient.", 0), 
                ("B) Le arăt o dată și gata.", 30), 
                ("C) Îmi place să le explic.", 70), 
                ("D) Să îi învăț. Scopul meu e să îi dezvolt pe ei.", 100)
            ]
        ),
        (
            "Cât de des pui nevoile altora mai presus de ale tale, încercând să îi 'salvezi'?",
            "Altruism vs Sacrifice, Boundaries", 
            3, 
            [
                ("A) Niciodată. Fiecare e responsabil pentru el.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori, pentru familie.", 60), 
                ("D) Deseori. Nu pot refuza pe cineva care suferă.", 100)
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