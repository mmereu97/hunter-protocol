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
AXIS_ID = 38
AXIS_NAME = "Receptivitate Emoțională"
# Pol Stânga (0): Ignoră Emoțiile / Insensibil / Pragmatic
# Pol Dreapta (100): Trăiește Intens / Profund / Introspectiv

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
    # Punctaj: 0 = Insensibil (Closed), 100 = Receptiv (Open)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Valoarea Emoțiilor) ---
        (
            "Consideri că emoțiile sunt o sursă importantă de informație sau mai degrabă un obstacol în calea gândirii logice?",
            "Philosophy, Logic vs Emotion, Worldview", 
            1, 
            [
                ("A) Un obstacol. Deciziile bune se iau la rece.", 0), 
                ("B) Mai degrabă încurcă, dar sunt inevitabile.", 30), 
                ("C) Sunt utile dacă sunt înțelese.", 70), 
                ("D) Sunt esențiale. O viață fără emoții profunde e goală.", 100)
            ]
        ),
        (
            "Cât de des ești atent la propriile tale stări interioare și la nuanțele felului în care te simți?",
            "Introspection, Self-Awareness, Mood", 
            1, 
            [
                ("A) Niciodată. Nu am timp de analize.", 0), 
                ("B) Doar când mă simt foarte rău sau foarte bine.", 30), 
                ("C) Destul de des.", 70), 
                ("D) Constant. Îmi analizez mereu trăirile.", 100)
            ]
        ),
        (
            "Preferi o viață stabilă, fără prea multe suișuri și coborâșuri, sau una intensă, chiar dacă asta înseamnă și suferință?",
            "Stability vs Intensity, Life Choices", 
            1, 
            [
                ("A) Stabilitate totală. Vreau liniște plată.", 0), 
                ("B) Prefer să evit dramele.", 30), 
                ("C) Un echilibru, dar cu momente intense.", 70), 
                ("D) Intensitate. Vreau să simt că trăiesc, cu bune și rele.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Expresivitate/Conexiune) ---
        (
            "Ți se întâmplă să ai o reacție fizică la emoții (nod în gât, fluturi în stomac, fiori pe șira spinării)?",
            "Somatic Markers, Sensitivity, Feeling", 
            2, 
            [
                ("A) Nu, nu știu despre ce vorbești.", 0), 
                ("B) Rar, la emoții extreme.", 30), 
                ("C) Da, uneori.", 70), 
                ("D) Da, frecvent. Emoțiile mele sunt viscerale.", 100)
            ]
        ),
        (
            "Cât de ușor îți este să vorbești despre sentimentele tale cu cineva apropiat?",
            "Communication, Vulnerability, Expression", 
            2, 
            [
                ("A) Foarte greu. Nu îmi place să mă expun.", 0), 
                ("B) Vorbesc doar despre fapte, nu despre ce simt.", 30), 
                ("C) Pot discuta dacă e nevoie.", 70), 
                ("D) Foarte ușor. Îmi place să împărtășesc ce simt.", 100)
            ]
        ),
        (
            "Observi schimbările subtile de dispoziție la tine sau la ceilalți?",
            "Empathy, Awareness, Perception", 
            2, 
            [
                ("A) Nu, deseori sunt luat prin surprindere.", 0), 
                ("B) Observ doar dacă e evident.", 30), 
                ("C) De obicei da.", 70), 
                ("D) Imediat. Sunt foarte sensibil la atmosferă.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Alexitimie / Psihopatie vs BPD) ---
        (
            "Dacă ai putea apăsa un buton ca să nu mai simți niciodată tristețe, frică sau durere sufletească, dar nici bucurie intensă, l-ai apăsa?",
            "Hypothetical, Emotional Value, Stoicism", 
            3, 
            [
                ("A) Da, imediat. Vreau doar eficiență și liniște.", 0), 
                ("B) Probabil da, viața ar fi mai simplă.", 30), 
                ("C) Probabil nu.", 70), 
                ("D) Nu! Asta ar însemna să fiu un robot, nu un om.", 100)
            ]
        ),
        (
            "Te-ai simțit vreodată copleșit de frumusețea unui peisaj, a unei poezii sau a unui moment, până la punctul în care ai rămas fără cuvinte?",
            "Awe, Aesthetic Chills, Depth", 
            3, 
            [
                ("A) Nu. E doar un peisaj.", 0), 
                ("B) Am zis 'ce frumos', dar atât.", 30), 
                ("C) Da, am avut momente de admirație.", 70), 
                ("D) Da, des. Am o capacitate mare de a simți uimirea (awe).", 100)
            ]
        ),
        (
            "Crezi că oamenii care plâng la filme sau sunt emotivi sunt slabi?",
            "Judgment, Stereotypes, Toughness", 
            3, 
            [
                ("A) Da, trebuie să te controlezi.", 0), 
                ("B) Puțin cam melodramatici.", 30), 
                ("C) Nu, e normal.", 70), 
                ("D) Nu, e o dovadă de sensibilitate și umanitate.", 100)
            ]
        ),
        (
            "Ai trăiri interioare complexe pe care îți este greu să le descrii în cuvinte?",
            "Emotional Complexity, Nuance", 
            3, 
            [
                ("A) Nu. Mă simt bine sau rău, simplu.", 0), 
                ("B) Rar.", 30), 
                ("C) Uneori am stări amestecate.", 70), 
                ("D) Da, viața mea interioară e un labirint de nuanțe.", 100)
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