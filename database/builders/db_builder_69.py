import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# DEFINIȚII
AXIS_ID = 69
AXIS_NAME = "Cinism (Mizantropie)"
# Pol 0: Încredere în Umanitate / Idealist
# Pol 100: Cinic / Mizantrop / Oamenii sunt Răi

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date nu există: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm Clinicul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = CINIC (MONSTRU CLINIC)
    questions_data = [
        # --- VALUL 1: SCREENING (Natura Umană) ---
        (
            "Care dintre următoarele afirmații descrie cel mai bine părerea ta despre majoritatea oamenilor?",
            "Worldview, Humanity, Trust", 
            1, 
            [
                ("A) Sunt buni și vor să ajute dacă pot.", 0), 
                ("B) Sunt neutri, își văd de viața lor.", 30), 
                ("C) Sunt egoiști, dar inofensivi.", 60), 
                ("D) Sunt răi, prefăcuți și ar profita de tine oricând.", 100)
            ]
        ),
        (
            "Ce crezi că îi motivează pe oameni să facă acte de caritate sau fapte bune?",
            "Altruism vs Egoism, Beliefs", 
            1, 
            [
                ("A) Dorința sinceră de a ajuta.", 0), 
                ("B) Empatia, dar și imaginea.", 30), 
                ("C) Nevoia de a se simți ei bine (egoism mascat).", 70), 
                ("D) Doar ipocrizia și dorința de a fi lăudați.", 100)
            ]
        ),
        (
            "Crezi că onestitatea este cea mai bună politică în afaceri și viață?",
            "Honesty, Strategy, Ethics", 
            1, 
            [
                ("A) Da, întotdeauna. Minciuna are picioare scurte.", 0), 
                ("B) De cele mai multe ori, da.", 20), 
                ("C) Uneori trebuie să fii 'flexibil' ca să reușești.", 70), 
                ("D) Nu. Cine e onest 100% este mâncat de vii de ceilalți.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Suspiciune / Relații) ---
        (
            "Dacă cineva este foarte amabil cu tine fără un motiv aparent, ce gândești?",
            "Hidden Motives, Suspicion", 
            2, 
            [
                ("A) Că e o persoană plăcută.", 0), 
                ("B) Mă bucur de interacțiune.", 20), 
                ("C) Mă întreb ce vrea de la mine.", 70), 
                ("D) Sigur pregătește o țeapă sau vrea să mă manipuleze.", 100)
            ]
        ),
        (
            "Consideri că majoritatea oamenilor mint dacă știu că nu pot fi prinși?",
            "Lying, Integrity, Society", 
            2, 
            [
                ("A) Nu, conștiința îi oprește.", 0), 
                ("B) Unii da, dar nu majoritatea.", 30), 
                ("C) Probabil că da.", 70), 
                ("D) Absolut. Doar frica de pedeapsă îi ține corecți.", 100)
            ]
        ),
        (
            "Cum te raportezi la regulile sociale și politețe?",
            "Social Norms, Hypocrisy", 
            2, 
            [
                ("A) Sunt necesare pentru armonie.", 0), 
                ("B) Le respect.", 20), 
                ("C) Sunt uneori obositoare.", 60), 
                ("D) Sunt o mască falsă. Toți sunt niște ipocriți zâmbitori.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Mizantropie Pură / Ostilitate) ---
        (
            "Te simți adesea dezgustat de prostia sau răutatea speciei umane?",
            "Misanthropy, Disgust, Superiority", 
            3, 
            [
                ("A) Nu, iubesc oamenii cu defectele lor.", 0), 
                ("B) Rareori.", 30), 
                ("C) Da, uneori îmi pierd speranța în omenire.", 70), 
                ("D) Da. Oamenii sunt o specie ratată, o 'ciumă' pe pământ.", 100)
            ]
        ),
        (
            "Ai tendința să interpretezi remarcile neutre ale altora ca fiind insulte ascunse sau atacuri?",
            "Paranoid Ideation, Hostility", 
            3, 
            [
                ("A) Nu, nu iau lucrurile personal.", 0), 
                ("B) Doar dacă tonul e ciudat.", 30), 
                ("C) Sunt vigilent, nu vreau să fiu luat peste picior.", 70), 
                ("D) Da. Oamenii sunt pasiv-agresivi mereu, trebuie să îi ghicești.", 100)
            ]
        ),
        (
            "Crezi că este mai sigur să nu te bazezi pe nimeni în viață?",
            "Independence vs Trust, Isolation", 
            3, 
            [
                ("A) Nu, avem nevoie unii de alții.", 0), 
                ("B) E bine să ai autonomie, dar și prieteni.", 30), 
                ("C) E riscant să depinzi de alții.", 70), 
                ("D) Da. La finalul zilei, ești singur. Toți te vor trăda.", 100)
            ]
        ),
        (
            "Dacă ai vedea pe cineva înșelat sau păcălit, ai simți compasiune sau ai gândi că 'și-a meritat-o dacă e prost'?",
            "Empathy vs Contempt, Victim Blaming", 
            3, 
            [
                ("A) Compasiune și furie pe escroc.", 0), 
                ("B) Îmi pare rău pentru el.", 20), 
                ("C) E trist, dar trebuia să fie atent.", 60), 
                ("D) Dacă ești naiv, meriți să fii mâncat. Așa e natura.", 100)
            ]
        )
    ]

    try:
        # CLEANUP & INSERT
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))

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
        
        conn.commit()
        log("db_conn", f"SUCCES: {len(questions_data)} întrebări inserate pentru {AXIS_NAME}.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()