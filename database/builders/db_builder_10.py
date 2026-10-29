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
AXIS_ID = 10
AXIS_NAME = "Timiditate Socială (Jena)"
# Pol Stânga (0): Tupeist / Direct / Lider Social
# Pol Dreapta (100): Timid / Rușinos / Anxios

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
    # Punctaj: 0 = Tupeist (Bold), 100 = Timid (Shy)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Public Speaking/Străini) ---
        (
            "Cum te simți dacă trebuie să vorbești în fața unui grup mare de oameni (prezentare, discurs)?",
            "Public Speaking, Stage Fright", 
            1, 
            [
                ("A) Îmi place, mă simt în elementul meu.", 0), 
                ("B) Am puține emoții, dar mă descurc bine.", 30), 
                ("C) Sunt foarte nervos, îmi tremură vocea.", 70), 
                ("D) Sunt terifiat, evit cu orice preț.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să abordezi o persoană necunoscută (de exemplu, la o petrecere sau pentru a cere informații)?",
            "Social Boldness, Strangers", 
            1, 
            [
                ("A) Foarte ușor, intru în vorbă imediat.", 0), 
                ("B) Destul de ușor, dacă am un motiv.", 30), 
                ("C) Ezit, îmi fac curaj înainte.", 70), 
                ("D) Foarte greu. Aștept să fiu abordat eu.", 100)
            ]
        ),
        (
            "Dacă faci o greșeală minoră în public (te împiedici, scapi ceva), cât timp te gândești la asta după?",
            "Embarrassment, Rumination", 
            1, 
            [
                ("A) Deloc. Râd și trec mai departe.", 0), 
                ("B) Câteva minute, apoi uit.", 30), 
                ("C) Mă simt rușinat o bună parte din zi.", 70), 
                ("D) Mă gândesc la asta zile întregi, îmi vine să intru în pământ.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Autoritate/Grup) ---
        (
            "Într-o ședință sau discuție de grup, dacă nu ești de acord cu cineva, intervii?",
            "Assertiveness, Conflict, Group Dynamics", 
            2, 
            [
                ("A) Da, spun direct ce gândesc.", 0), 
                ("B) Da, dar încerc să fiu diplomat.", 30), 
                ("C) Doar dacă este absolut necesar.", 70), 
                ("D) Nu, tac pentru a nu atrage atenția.", 100)
            ]
        ),
        (
            "Cum te simți în prezența figurilor de autoritate (șefi, oficialități)?",
            "Authority, Intimidation", 
            2, 
            [
                ("A) Ca de la egal la egal.", 0), 
                ("B) Respectuos, dar relaxat.", 30), 
                ("C) Ușor intimidat și precaut.", 70), 
                ("D) Foarte inhibat, nu îmi găsesc cuvintele.", 100)
            ]
        ),
        (
            "Te îngrijorează des faptul că ceilalți te-ar putea judeca sau ar putea crede ceva rău despre tine?",
            "Fear of Judgement, Social Anxiety", 
            2, 
            [
                ("A) Nu. 'Câinii latră, caravana trece'.", 0), 
                ("B) Uneori, depinde de persoană.", 30), 
                ("C) Da, încerc să fac o impresie bună mereu.", 70), 
                ("D) Da, este o sursă constantă de stres.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Anxietate Socială Clinică / Evitant) ---
        (
            "Ai refuzat vreodată o oportunitate (job, întâlnire, eveniment) doar din cauza fricii de interacțiune socială?",
            "Avoidance, Missed Opportunities", 
            3, 
            [
                ("A) Niciodată.", 0), 
                ("B) Poate o dată, când eram obosit.", 30), 
                ("C) De câteva ori, și am regretat.", 70), 
                ("D) Da, des. Frica mă blochează în viață.", 100)
            ]
        ),
        (
            "Simți simptome fizice (roșeață, transpirație, bătăi rapide ale inimii) înainte de un eveniment social?",
            "Somatic, Panic, Social Phobia", 
            3, 
            [
                ("A) Nu, sunt calm.", 0), 
                ("B) Doar o ușoară emoție constructivă.", 30), 
                ("C) Da, roșesc sau transpir când sunt privit.", 70), 
                ("D) Da, uneori am stări de greață sau panică.", 100)
            ]
        ),
        (
            "Te simți ca un 'impostor' sau că nu te integrezi, chiar și printre prieteni?",
            "Belonging, Insecurity", 
            3, 
            [
                ("A) Nu, sunt sufletul petrecerii.", 0), 
                ("B) Mă simt bine în cercul meu.", 30), 
                ("C) Uneori mă simt în plus.", 70), 
                ("D) Da, simt că nu aparțin nicăieri.", 100)
            ]
        ),
        (
            "Dacă trebuie să suni pe cineva necunoscut la telefon, amâni momentul?",
            "Phone Anxiety, Procrastination", 
            3, 
            [
                ("A) Nu, sun imediat.", 0), 
                ("B) Nu îmi place, dar o fac.", 30), 
                ("C) Îmi repet în gând ce am de spus înainte.", 60), 
                ("D) Amân cât pot de mult sau trimit email/mesaj.", 100)
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