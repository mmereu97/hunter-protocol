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
AXIS_ID = 13
AXIS_NAME = "Stimă de Sine Socială"
# Pol Stânga (0): Nesigur / Neimportant / Retras
# Pol Dreapta (100): Încrezător / Popular / Carismatic

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

    # --- PASUL DE SIGURANȚĂ: Actualizăm definiția axei (în caz că a rămas Empatie) ---
    c.execute("""
        UPDATE axes 
        SET name=?, left_pole=?, right_pole=?, category=?, description=?
        WHERE id=?
    """, (AXIS_NAME, "Nesigur / Retras", "Încrezător / Popular", "Core", "HEXACO X - Social Self-Esteem", AXIS_ID))
    conn.commit()

    # 4. DATASET-UL
    # Punctaj: 0 = Nesigur (Low Self-Esteem), 100 = Încrezător (High Self-Esteem)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Grup) ---
        (
            "Când ești într-un grup de oameni, simți că ai lucruri interesante de spus?",
            "Social Worth, Conversation, Confidence", 
            1, 
            [
                ("A) Nu, de obicei tac pentru că mă simt plictisitor.", 0), 
                ("B) Uneori, depinde de subiect.", 30), 
                ("C) Da, cred că pot contribui la discuție.", 70), 
                ("D) Categoric. Oamenii sunt captivați când vorbesc.", 100)
            ]
        ),
        (
            "Cum crezi că te percep ceilalți la o primă întâlnire?",
            "First Impressions, Self-Image", 
            1, 
            [
                ("A) Ca pe cineva șters sau ciudat.", 0), 
                ("B) Ca pe o persoană obișnuită.", 30), 
                ("C) Ca pe cineva simpatic și capabil.", 70), 
                ("D) Ca pe un lider sau o persoană carismatică.", 100)
            ]
        ),
        (
            "Te simți confortabil să îți exprimi opiniile, chiar dacă sunt contrare grupului?",
            "Assertiveness, Confidence, Group Pressure", 
            1, 
            [
                ("A) Nu. Îmi e teamă că voi fi judecat sau respins.", 0), 
                ("B) Ezit, prefer să nu fac valuri.", 30), 
                ("C) Da, dacă sunt sigur pe mine.", 70), 
                ("D) Da, opinia mea contează și merită auzită.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Muncă/Feedback) ---
        (
            "La locul de muncă, dacă primești o sarcină grea, care e primul gând?",
            "Competence, Self-Efficacy", 
            2, 
            [
                ("A) 'Nu voi reuși, o să mă fac de râs'.", 0), 
                ("B) 'Sper să nu greșesc'.", 30), 
                ("C) 'E o provocare, mă voi descurca'.", 70), 
                ("D) 'Sunt omul potrivit pentru asta, voi excela'.", 100)
            ]
        ),
        (
            "Cum reacționezi când primești un compliment sincer?",
            "Compliments, Self-Worth", 
            2, 
            [
                ("A) Mă simt stânjenit și cred că nu îl merit.", 0), 
                ("B) Îl minimizez ('eh, n-a fost mare lucru').", 30), 
                ("C) Mulțumesc și mă bucur.", 70), 
                ("D) Mă simt bine, știu că am muncit pentru asta.", 100)
            ]
        ),
        (
            "Simți adesea că ceilalți sunt mai buni, mai deștepți sau mai capabili decât tine?",
            "Comparison, Inferiority", 
            2, 
            [
                ("A) Da, aproape tot timpul.", 0), 
                ("B) Deseori mă compar în defavoarea mea.", 30), 
                ("C) Uneori, dar știu că și eu am calități.", 70), 
                ("D) Nu. Mă consider egal sau superior în domeniul meu.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Narcisism vs Sindrom Impostor) ---
        (
            "Te consideri o persoană populară?",
            "Popularity, Social Status", 
            3, 
            [
                ("A) Nu, sunt adesea ignorat.", 0), 
                ("B) Am câțiva prieteni, dar nu sunt popular.", 30), 
                ("C) Da, mă înțeleg bine cu multă lume.", 70), 
                ("D) Da, sunt adesea centrul atenției și sufletul grupului.", 100)
            ]
        ),
        (
            "Când intri într-o cameră plină de necunoscuți, ce simți?",
            "Social Presence, Anxiety vs Confidence", 
            3, 
            [
                ("A) Vreau să mă ascund într-un colț.", 0), 
                ("B) O ușoară anxietate.", 30), 
                ("C) Curiozitate.", 70), 
                ("D) Simt că 'dețin' spațiul, am o prezență puternică.", 100)
            ]
        ),
        (
            "Dacă organizezi o ieșire sau un proiect, crezi că oamenii te vor urma?",
            "Leadership Potential, Influence", 
            3, 
            [
                ("A) Nu, probabil nu ar veni nimeni.", 0), 
                ("B) Doar prietenii foarte apropiați.", 30), 
                ("C) Cred că aș putea convinge destui.", 70), 
                ("D) Da, am putere de convingere și oamenii au încredere în mine.", 100)
            ]
        ),
        (
            "În general, ești mulțumit de cine ești ca persoană?",
            "Self-Acceptance, General Self-Esteem", 
            3, 
            [
                ("A) Nu, aș vrea să fiu altcineva.", 0), 
                ("B) Sunt multe lucruri pe care vreau să le schimb.", 30), 
                ("C) În mare parte da.", 70), 
                ("D) Da, sunt mândru de persoana care am devenit.", 100)
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