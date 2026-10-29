import sqlite3
import hashlib
import json
import os
import sys

# 1. SETUP PATHS & IMPORTS
# Ne asigurăm că putem importa din rădăcină
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

# 2. DEFINIȚII
AXIS_ID = 2
AXIS_NAME = "Corectitudine"
# Pol Stânga (0): Oportunist / Fraudulos
# Pol Dreapta (100): Principial / Corect

# 3. FUNCȚIA DE HASHING (Time Machine)
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

    # 4. DATASET-UL (Întrebări în Română)
    # Format: (Text Întrebare, Tag-uri AI, Val Țintă, [Lista Opțiuni])
    # Punctaj: 0 = Oportunist, 100 = Corect
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Subtil/Corporate) ---
        (
            "La locul de muncă, sunt disponibile consumabile (pixuri, hârtie, baterii). Iei uneori acasă pentru uz personal?",
            "Corporate, Theft, Petty", 
            1, 
            [
                ("A) Da, toată lumea face asta, e un beneficiu implicit.", 0), 
                ("B) Doar dacă am uitat să îmi cumpăr și am neapărată nevoie.", 30), 
                ("C) Evit, dar poate s-a întâmplat accidental.", 70), 
                ("D) Niciodată. Ce e al firmei rămâne la firmă.", 100)
            ]
        ),
        (
            "Ai descoperit o eroare în sistemul de pontaj care te plătește pentru o oră în plus zilnic. Ce faci?",
            "Money, Integrity, Work", 
            1, 
            [
                ("A) Tac și mă bucur de bani. E greșeala lor.", 0), 
                ("B) Aștept să văd dacă observă cineva.", 30), 
                ("C) Probabil aș semnala, dar nu urgent.", 70), 
                ("D) Anunț imediat departamentul HR/Contabilitate.", 100)
            ]
        ),
        (
            "Cumperi un produs electronic și îl folosești o săptămână pentru un eveniment, apoi îl returnezi ca 'necorespunzător'. Cum ți se pare?",
            "Retail, Ethics, Loophole", 
            1, 
            [
                ("A) Este o strategie inteligentă. Sistemul permite.", 0), 
                ("B) Nu e ideal, dar aș face-o la nevoie.", 30), 
                ("C) Mi-ar fi rușine să fac asta.", 70), 
                ("D) Este o formă de furt/înșelăciune. Nu aș face asta.", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Direct/Social/Trafic) ---
        (
            "Te grăbești foarte tare și ești oprit de poliție pentru viteză. Dacă polițistul pare dispus la o 'înțelegere', îi oferi mită?",
            "Traffic, Bribery, Law", 
            2, 
            [
                ("A) Da, imediat. Timpul meu e mai scump decât amenda.", 0), 
                ("B) Aș încerca să sugerez subtil o 'cafea'.", 20), 
                ("C) Aș prefera amenda, e prea riscant.", 80), 
                ("D) Nu. Corupția este inacceptabilă, indiferent de urgență.", 100)
            ]
        ),
        (
            "Găsești un portofel pe stradă cu 500 RON și un act de identitate. Ce faci?",
            "Money, Civic Duty", 
            2, 
            [
                ("A) Iau banii și arunc portofelul.", 0), 
                ("B) Iau banii și las portofelul undeva vizibil.", 20), 
                ("C) Încerc să găsesc proprietarul, dar poate păstrez o 'taxă' de efort.", 60), 
                ("D) Returnez totul intact proprietarului sau poliției.", 100)
            ]
        ),
        (
            "Ai lovit ușor o mașină în parcare. Nu te-a văzut nimeni și nu sunt camere. Ce faci?",
            "Traffic, Responsibility", 
            2, 
            [
                ("A) Plec repede. Nu e vina mea că a parcat prost.", 0), 
                ("B) Mă uit să văd dacă e daună mare. Dacă e mică, plec.", 30), 
                ("C) Aștept puțin, poate vine proprietarul.", 70), 
                ("D) Las un bilet cu numărul meu de telefon în parbriz.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Confruntare/Monștri Activați) ---
        (
            "Dacă ai ști cu certitudine că poți face o fraudă financiară majoră fără să fii prins vreodată, ai face-o?",
            "Hypothetical, Fraud, Dark Triad", 
            3, 
            [
                ("A) Da, ar fi prostie să ratez ocazia.", 0), 
                ("B) M-aș gândi serios la asta.", 20), 
                ("C) Probabil că nu, conștiința nu m-ar lăsa.", 80), 
                ("D) Nu. Principiile mele nu sunt de vânzare.", 100)
            ]
        ),
        (
            "Pentru a obține un post de conducere mult dorit, ai fi dispus să falsifici ușor datele din CV sau să minți despre o realizare?",
            "Career, Lie, Ambition", 
            3, 
            [
                ("A) Da, toată lumea își 'înflorește' CV-ul.", 0), 
                ("B) Aș exagera adevărul, dar fără minciuni gogonate.", 30), 
                ("C) Aș prezenta totul în cea mai bună lumină posibilă, dar onest.", 80), 
                ("D) Nu. Vreau să fiu angajat pentru cine sunt cu adevărat.", 100)
            ]
        ),
        (
            "Un prieten bun îți cere să minți pentru el într-o situație legală (alibi fals). Ce faci?",
            "Loyalty vs Integrity, Law", 
            3, 
            [
                ("A) Îl ajut. Prietenia e mai presus de lege.", 0), 
                ("B) Îl ajut dacă nu e ceva grav (crimă/violență).", 30), 
                ("C) Îl refuz și îi spun să își asume responsabilitatea.", 80), 
                ("D) Nu pot face asta. Integritatea mea e non-negociabilă.", 100)
            ]
        ),
        (
            "Crezi că regulile și legile sunt făcute pentru proști și că oamenii deștepți știu să le ocolească?",
            "Worldview, Rules, Narcissism", 
            3, 
            [
                ("A) Da, absolut. Scopul scuză mijloacele.", 0), 
                ("B) Uneori regulile sunt absurde și trebuie ignorate.", 30), 
                ("C) Regulile sunt necesare, dar uneori rigide.", 70), 
                ("D) Nu. O societate funcționează doar dacă respectăm regulile.", 100)
            ]
        )
    ]

    try:
        # 5. CURĂȚARE DATE VECHI (Pentru a evita duplicate la rulări multiple)
        # Luăm hash-urile existente pentru a șterge opțiunile orfane
        c.execute("SELECT version_hash FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        old_hashes = [r[0] for r in c.fetchall()]
        
        if old_hashes:
            placeholders = ','.join('?' * len(old_hashes))
            c.execute(f"DELETE FROM question_options WHERE question_hash IN ({placeholders})", old_hashes)
            c.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
            log("db_query", f"S-au șters întrebările vechi pentru Axa {AXIS_ID}.")

        # 6. INSERARE DATE NOI
        count = 0
        for q_text, tags, wave, opts in questions_data:
            v_hash = generate_hash(q_text, opts)
            
            # Insert Header Întrebare
            c.execute("""
                INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (AXIS_ID, v_hash, q_text, tags, wave))
            
            # Insert Opțiuni
            labels = ['A', 'B', 'C', 'D']
            for idx, (opt_text, score) in enumerate(opts):
                c.execute("""
                    INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                    VALUES (?, ?, ?, ?)
                """, (v_hash, labels[idx], opt_text, score))
            count += 1

        conn.commit()
        log("db_conn", f"SUCCES: S-au inserat {count} întrebări pentru {AXIS_NAME} (ID {AXIS_ID}).")

    except Exception as e:
        log_error(f"Eroare la popularea Axei {AXIS_ID}", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()