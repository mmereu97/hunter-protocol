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
AXIS_ID = 20
AXIS_NAME = "Blândețe"
# Pol Stânga (0): Dur / Critic / Aspru
# Pol Dreapta (100): Blând / Binevoitor / Milos

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
    # Punctaj: 0 = Dur (Critic), 100 = Blând (Milos)
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Feedback/Judecată) ---
        (
            "Când trebuie să evaluezi munca cuiva care a greșit, pe ce pui accent?",
            "Feedback, Management, Criticism", 
            1, 
            [
                ("A) Pe greșeală. Trebuie corectată ferm, fără menajamente.", 0), 
                ("B) Sunt obiectiv, dar direct.", 30), 
                ("C) Încerc să 'împachetez' critica într-un mod pozitiv.", 70), 
                ("D) Mă concentrez pe efortul depus, ca să nu îl descurajez.", 100)
            ]
        ),
        (
            "Ești genul de persoană care spune lucrurilor pe nume ('adevărul crud'), chiar dacă știi că asta va răni sentimentele cuiva?",
            "Honesty vs Kindness, Social", 
            1, 
            [
                ("A) Da, adevărul e mai important decât sentimentele.", 0), 
                ("B) De cele mai multe ori, da.", 30), 
                ("C) Prefer o minciună mică decât să rănesc pe cineva inutil.", 70), 
                ("D) Nu, sunt foarte atent la cum se simt ceilalți.", 100)
            ]
        ),
        (
            "Ce părere ai despre oamenii care cer clemență sau circumstanțe atenuante când încalcă o regulă?",
            "Rules, Mercy, Judgment", 
            1, 
            [
                ("A) Încearcă să scape ieftin. Regulile sunt reguli.", 0), 
                ("B) Sunt sceptic, trebuie dovezi clare.", 30), 
                ("C) Uneori viața e grea, trebuie înțeleși.", 70), 
                ("D) Sunt dispus să le ofer o a doua șansă, oricine greșește.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Justiție/Empatie) ---
        (
            "Crezi că sistemul legal (sau regulamentul firmei) ar trebui să fie aplicat dur, fără excepții, pentru a menține ordinea?",
            "Justice, Rigidity, Toughness", 
            2, 
            [
                ("A) Absolut. Fără disciplină e haos.", 0), 
                ("B) În general da.", 30), 
                ("C) Nu, trebuie analizat contextul uman.", 70), 
                ("D) Nu, reabilitarea și înțelegerea sunt mai importante decât pedeapsa.", 100)
            ]
        ),
        (
            "Dacă un coleg întârzie cu un proiect și îți spune că a avut probleme personale, îl crezi?",
            "Skepticism, Trust, Empathy", 
            2, 
            [
                ("A) Nu, sună a scuză penibilă pentru lene.", 0), 
                ("B) Verific dacă e adevărat.", 30), 
                ("C) Îl cred și încerc să îl ajut.", 70), 
                ("D) Îl cred imediat și preiau eu din sarcini ca să-l scutesc.", 100)
            ]
        ),
        (
            "Cât de critic ești cu tine însuți când greșești?",
            "Self-Criticism, Perfectionism", 
            2, 
            [
                ("A) Foarte dur. Nu îmi iert greșelile.", 0), 
                ("B) Mă analizez serios.", 30), 
                ("C) Sunt blând, învăț din greșeli.", 70), 
                ("D) Mă accept așa cum sunt, nimeni nu e perfect.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Psihopatie / Hărțuire / Sadism) ---
        (
            "Dacă cineva care ți-a greșit în trecut primește o pedeapsă aspră sau pățește ceva rău, simți o satisfacție?",
            "Vindictiveness, Schadenfreude, Cruelty", 
            3, 
            [
                ("A) Da, 'i-a dat Dumnezeu'. Merita.", 0), 
                ("B) Simt că s-a făcut dreptate.", 30), 
                ("C) Nu neapărat, e trist.", 70), 
                ("D) Nu, îmi pare rău pentru el, indiferent ce mi-a făcut.", 100)
            ]
        ),
        (
            "Consideri că 'mila' este o slăbiciune care îi împiedică pe oameni să se maturizeze?",
            "Philosophy, Tough Love, Machiavellianism", 
            3, 
            [
                ("A) Da, oamenii trebuie să se călească singuri.", 0), 
                ("B) Uneori mila face mai mult rău decât bine.", 30), 
                ("C) Mila este o virtute umană importantă.", 70), 
                ("D) Nu, empatia este baza societății.", 100)
            ]
        ),
        (
            "Te simți adesea mișcat de poveștile oamenilor defavorizați (cerșetori, oameni străzii) sau ai tendința să crezi că sunt responsabili pentru soarta lor?",
            "Social Empathy, Attribution Bias", 
            3, 
            [
                ("A) Sunt responsabili. Dacă munceau, nu ajungeau acolo.", 0), 
                ("B) Probabil au făcut alegeri greșite.", 30), 
                ("C) Mă întristează situația lor.", 70), 
                ("D) Mă afectează profund, aș vrea să ajut pe toată lumea.", 100)
            ]
        ),
        (
            "Într-o ceartă, ai tendința să folosești cuvinte dure, ironii sau sarcasme pentru a 'câștiga'?",
            "Conflict, Verbal Aggression", 
            3, 
            [
                ("A) Da, lovesc unde doare cel mai tare.", 0), 
                ("B) Folosesc sarcasmul ca armă.", 30), 
                ("C) Încerc să nu jignesc.", 70), 
                ("D) Niciodată. Nu vreau să rănesc pe nimeni, chiar dacă am dreptate.", 100)
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