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
AXIS_ID = 62
AXIS_NAME = "Interes Artistic (RIASEC A)"
# Pol Stânga (0): Convențional / Structurat / Pratic
# Pol Dreapta (100): Artistic / Creativ / Expresiv

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
    # Punctaj: 0 = Convențional (Reguli), 100 = Artistic (Creație)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Preferințe de Lucru) ---
        (
            "Preferi activitățile care au reguli clare și proceduri stricte, sau pe cele care îți permit să improvizezi și să creezi?",
            "Work Style, Structure vs Chaos", 
            1, 
            [
                ("A) Reguli clare. Vreau să știu exact ce am de făcut.", 0), 
                ("B) Prefer structura, cu mici libertăți.", 30), 
                ("C) Îmi place să am libertate de decizie.", 70), 
                ("D) Improvizație totală. Regulile îmi omoară creativitatea.", 100)
            ]
        ),
        (
            "Cât de importantă este pentru tine componenta estetică/vizuală în munca ta sau în viața de zi cu zi?",
            "Aesthetics, Beauty, Utility", 
            1, 
            [
                ("A) Deloc. Funcționalitatea e tot ce contează.", 0), 
                ("B) E un bonus plăcut, dar nu esențial.", 30), 
                ("C) Este importantă.", 70), 
                ("D) Esențială. Nu pot lucra sau trăi într-un mediu urât sau anost.", 100)
            ]
        ),
        (
            "Când trebuie să rezolvi o problemă, cauți soluția standard (din manual) sau încerci să inventezi o abordare originală?",
            "Originality, Problem Solving", 
            1, 
            [
                ("A) Soluția standard. De ce să reinventez roata?", 0), 
                ("B) Mă bazez pe metode verificate.", 30), 
                ("C) Încerc să o adaptez creativ.", 70), 
                ("D) Vreau o soluție originală, unică, 'semnătura mea'.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Carieră/Hobby) ---
        (
            "Dacă ai putea alege între a fi contabil (reguli, cifre, precizie) și a fi designer/scriitor (creativitate, haos, expresie), ce ai alege?",
            "Career Choice, RIASEC C vs A", 
            2, 
            [
                ("A) Contabil, clar. Îmi place ordinea.", 0), 
                ("B) Probabil ceva administrativ.", 20), 
                ("C) Ceva creativ, dar stabil (ex: arhitect).", 70), 
                ("D) Designer/Scriitor. Vreau să creez ceva nou.", 100)
            ]
        ),
        (
            "Simți nevoia să te exprimi prin mijloace artistice (scris, muzică, pictură, design, modă, gătit creativ)?",
            "Self-Expression, Hobbies", 
            2, 
            [
                ("A) Nu. Nu am 'fibră artistică'.", 0), 
                ("B) Rar, poate fac o poză frumoasă.", 30), 
                ("C) Da, am hobby-uri creative.", 70), 
                ("D) Da, este o nevoie vitală. Mă ofilesc dacă nu creez.", 100)
            ]
        ),
        (
            "Te simți confortabil în medii nestructurate, unde nu există reguli clare și trebuie să îți folosești imaginația?",
            "Ambiguity Tolerance, Creativity", 
            2, 
            [
                ("A) Nu, mă stresez. Vreau claritate.", 0), 
                ("B) Prefer să primesc instrucțiuni.", 30), 
                ("C) Mă descurc bine.", 70), 
                ("D) Mă simt în elementul meu. Îmi place libertatea totală.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Gândire Bizară / Deschidere Extremă) ---
        (
            "Consideri că emoțiile și intuiția sunt un ghid valid în munca ta, sau doar logica rece contează?",
            "Intuition vs Logic, Subjectivity", 
            3, 
            [
                ("A) Doar logica și datele contează.", 0), 
                ("B) Emoțiile mai mult încurcă.", 30), 
                ("C) Intuiția ajută uneori.", 70), 
                ("D) Emoția este totul. Arta și munca trebuie să aibă suflet.", 100)
            ]
        ),
        (
            "Cum te simți dacă trebuie să faci o sarcină repetitivă, administrativă (data entry, arhivare), timp de 8 ore?",
            "Boredom, Routine Tolerance", 
            3, 
            [
                ("A) E ok, e o muncă relaxantă și clară.", 0), 
                ("B) O fac, e parte din job.", 30), 
                ("C) Mă plictisesc repede.", 70), 
                ("D) Simt că înnebunesc. Aș prefera să sap șanțuri decât să fac asta.", 100)
            ]
        ),
        (
            "Ești genul de persoană care vrea să spargă tiparele și să șocheze, sau preferi să te integrezi în normă?",
            "Non-conformity, Expression", 
            3, 
            [
                ("A) Să mă integrez. Nu vreau să ies în evidență.", 0), 
                ("B) Să fiu respectat pentru profesionalism standard.", 30), 
                ("C) Îmi place să fiu puțin diferit.", 70), 
                ("D) Să sparg tiparele. Convenționalul este inamicul artei.", 100)
            ]
        ),
        (
            "Vezi lumea mai degrabă ca pe o serie de fapte și date (Excel), sau ca pe o pânză de posibilități și semnificații (Artă)?",
            "Worldview, Abstract vs Concrete", 
            3, 
            [
                ("A) Fapte și date. Realitatea e concretă.", 0), 
                ("B) Mai mult pragmatic.", 30), 
                ("C) Văd potențialul din lucruri.", 70), 
                ("D) O pânză de semnificații. Totul este o metaforă.", 100)
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
        log("db_conn", f"SUCCES: {count} întrebări inserate pentru '{AXIS_NAME}' (ID {AXIS_ID}).")

    except Exception as e:
        log_error(f"Eroare Axa {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()