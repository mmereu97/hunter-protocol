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
AXIS_ID = 14
AXIS_NAME = "Asertivitate / Dominanță"
# Pol Stânga (0): Submisiv / Pasiv / Executant
# Pol Dreapta (100): Dominant / Lider / Asertiv

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
    # Punctaj: 0 = Submisiv, 100 = Dominant
    
    questions_data = [
        # --- VALUL 1 (SCREENING - General/Social) ---
        (
            "Într-o discuție de grup, dacă ai o opinie diferită de a majorității, o exprimi?",
            "Group Dynamics, Opinion, Courage", 
            1, 
            [
                ("A) Nu, tac pentru a nu crea tensiuni.", 0), 
                ("B) Doar dacă sunt întrebat direct.", 30), 
                ("C) Da, o spun politicos.", 70), 
                ("D) Da, o susțin cu tărie și încerc să-i conving.", 100)
            ]
        ),
        (
            "Cât de greu îți este să refuzi o rugăminte nerezonabilă din partea unui coleg sau prieten?",
            "Saying No, Boundaries, People Pleasing", 
            1, 
            [
                ("A) Foarte greu. De obicei accept, chiar dacă nu vreau.", 0), 
                ("B) Inventez o scuză ca să nu par nepoliticos.", 30), 
                ("C) Refuz, dar explic motivul.", 70), 
                ("D) Spun 'Nu' ferm și direct, fără justificări inutile.", 100)
            ]
        ),
        (
            "Îți place să preiei conducerea și să organizezi lucrurile în situații neclare?",
            "Leadership, Initiative, Control", 
            1, 
            [
                ("A) Deloc. Prefer să-mi spună alții ce să fac.", 0), 
                ("B) Doar dacă nu o face altcineva.", 30), 
                ("C) Da, îmi place să coordonez.", 70), 
                ("D) Întotdeauna. Mă simt natural în poziția de lider.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Conflict/Negociere) ---
        (
            "Dacă primești mâncarea greșită la restaurant (sau un serviciu prost), ce faci?",
            "Consumer, Confrontation, Rights", 
            2, 
            [
                ("A) O mănânc așa, nu vreau să fac scenă.", 0), 
                ("B) Mă plâng însoțitorului, dar nu chelnerului.", 20), 
                ("C) Îi atrag atenția politicos și cer schimbarea.", 70), 
                ("D) Cer imperativ să fie schimbată și să vorbesc cu managerul.", 100)
            ]
        ),
        (
            "Cât de confortabil te simți să negociezi un preț sau un salariu?",
            "Negotiation, Money, Value", 
            2, 
            [
                ("A) Foarte inconfortabil. Accept prima ofertă.", 0), 
                ("B) Am emoții, dar încerc puțin.", 30), 
                ("C) Mă descurc bine, știu ce merit.", 70), 
                ("D) Îmi place negocierea, e un joc de putere pe care îl câștig.", 100)
            ]
        ),
        (
            "Dacă cineva încearcă să te întrerupă în timp ce vorbești, cum reacționezi?",
            "Communication, Dominance, Respect", 
            2, 
            [
                ("A) Mă opresc și îl las să vorbească.", 0), 
                ("B) Aștept să termine și apoi continui.", 30), 
                ("C) Ridic puțin vocea și continui fraza.", 70), 
                ("D) Îi spun ferm: 'Nu am terminat, te rog nu mă întrerupe'.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Agresivitate vs Yes-Man) ---
        (
            "Consideri că pentru a reuși în viață trebuie să fii dur și să te impui în fața celorlalți?",
            "Worldview, Toughness, Machiavellianism", 
            3, 
            [
                ("A) Nu, blândețea e cheia.", 0), 
                ("B) Uneori trebuie să fii diplomat.", 30), 
                ("C) Da, trebuie să fii ferm și respectat.", 70), 
                ("D) Absolut. E o lume dură, cel mai puternic câștigă.", 100)
            ]
        ),
        (
            "Ai tendința de a monopoliza conversațiile și de a impune subiectul discuției?",
            "Social Dominance, Ego, Listening", 
            3, 
            [
                ("A) Nu, ascult mai mult decât vorbesc.", 0), 
                ("B) Încerc să mențin un echilibru.", 30), 
                ("C) Uneori, dacă subiectul mă pasionează.", 70), 
                ("D) Da, îmi place să fiu în centrul atenției și să direcționez discuția.", 100)
            ]
        ),
        (
            "Când apare un conflict, ai tendința să cedezi pentru a păstra pacea ('Peacekeeper')?",
            "Conflict Resolution, Submissiveness", 
            3, 
            [
                ("A) Aproape întotdeauna. Urăsc conflictul.", 0), 
                ("B) Cedez dacă nu e ceva important.", 30), 
                ("C) Nu cedez dacă am dreptate.", 70), 
                ("D) Niciodată. Lupt până îmi impun punctul de vedere.", 100)
            ]
        ),
        (
            "Îți place să dai ordine și să le spui altora ce au de făcut?",
            "Authority, Control, Management", 
            3, 
            [
                ("A) Nu, mă simt prost să comand pe cineva.", 0), 
                ("B) Doar dacă e necesar pentru organizare.", 30), 
                ("C) Da, îmi place să coordonez.", 70), 
                ("D) Da, ador să am putere și control asupra altora.", 100)
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