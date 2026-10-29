import sqlite3
import hashlib
import json
import os
from logger import log, log_error

DATABASE_NAME = "hunter_protocol.db"
AXIS_ID = 1  # Sinceritate

def generate_hash(text, options_list):
    """
    Creează un HASH unic bazat pe textul întrebării și variantele ei.
    Dacă modifici o literă, hash-ul se schimbă -> Versiune Nouă.
    """
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_sincerity_questions():
    if not os.path.exists(DATABASE_NAME):
        log_error("Baza de date nu există.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    log("sys", f"Populăm întrebările pentru Axa {AXIS_ID} (Sinceritate)...")

    # Structura datelor: (Text, Tags, Wave, [Lista Optiuni])
    # Punctaj: 0 = Machiavelic, 100 = Sincer
    questions_dataset = [
        # --- VALUL 1: SCREENING (Context General & Corporate) ---
        (
            "Dacă ai găsi o metodă legală, dar imorală, de a plăti mai puține taxe, ai folosi-o?",
            "Money, Ethics, Corporate",
            1,
            [("A) Cu siguranță, toți fac asta.", 0), ("B) Probabil că da.", 30), ("C) M-aș gândi bine înainte.", 70), ("D) Nu, corectitudinea e prioritară.", 100)]
        ),
        (
            "Crezi că este necesar să 'înflorești' puțin adevărul pentru a avansa în carieră?",
            "Career, Ambition, Strategy",
            1,
            [("A) Absolut, este o junglă.", 0), ("B) Uneori este necesar.", 30), ("C) Prefer să evit, dar depinde.", 70), ("D) Nu, performanța trebuie să vorbească.", 100)]
        ),
        (
            "Dacă un casier îți dă restul greșit în favoarea ta, te întorci să îl dai înapoi?",
            "Ethics, Small Theft, Character",
            1,
            [("A) Nu, e greșeala lui/norocul meu.", 0), ("B) Depinde de sumă.", 30), ("C) De cele mai multe ori, da.", 70), ("D) Întotdeauna.", 100)]
        ),

        # --- VALUL 2: CONFIRMARE (Dacă a fost contradictoriu) ---
        (
            "Ai lingușit vreodată un superior pe care nu îl respectai, doar pentru a obține un avantaj?",
            "Hierarchy, Manipulation, Power",
            2,
            [("A) Da, face parte din joc.", 0), ("B) Am fost nevoit uneori.", 30), ("C) Am evitat, dar am fost diplomat.", 70), ("D) Nu pot să fac asta, sunt autentic.", 100)]
        ),
        (
            "Cât de important este pentru tine să pari un om de succes în fața celorlalți, chiar dacă realitatea e alta?",
            "Image, Narcissism, Social",
            2,
            [("A) Este crucial.", 0), ("B) Este destul de important.", 30), ("C) Nu prea contează.", 70), ("D) Prefer să fiu eu însumi, indiferent de imagine.", 100)]
        ),
        (
            "Dacă ai lovi o mașină parcată și nimeni nu ar vedea, ai lăsa un bilet cu numărul tău?",
            "Traffic, Integrity, Law",
            2,
            [("A) Nu, aș pleca repede.", 0), ("B) M-aș uita dacă sunt camere.", 20), ("C) Probabil aș lăsa.", 80), ("D) Da, cu siguranță.", 100)]
        ),

        # --- VALUL 3: INTEROGATORIU (Deep Dive - Monstru Activat) ---
        (
            "Consideri că oamenii care spun mereu adevărul sunt naivi și vor pierde în viață?",
            "Worldview, Cynicism, Philosophy",
            3,
            [("A) Da, sunt fraieri.", 0), ("B) Adesea au de pierdut.", 30), ("C) Este o virtute, chiar dacă e greu.", 70), ("D) Nu, adevărul este puterea supremă.", 100)]
        ),
        (
            "Ai folosit vreodată informații confidențiale despre un coleg pentru a-l sabota?",
            "Sabotage, Malicious, Conflict",
            3,
            [("A) Da, dacă a meritat-o.", 0), ("B) Doar ca să mă apăr.", 30), ("C) Nu, nu îmi stă în fire.", 80), ("D) Niciodată, este inacceptabil.", 100)]
        ),
        (
            "Te-ai prefăcut vreodată că ești bolnav ca să nu mergi la muncă sau la o întâlnire?",
            "Lie, Responsibility, Avoidance",
            3,
            [("A) Da, des.", 0), ("B) De câteva ori.", 40), ("C) Foarte rar.", 80), ("D) Nu.", 100)]
        ),
        (
            "Dacă ai ști că poți fura o sumă mare de bani fără nicio șansă de a fi prins, ai face-o?",
            "Theft, Greed, Hypothetical",
            3,
            [("A) Fără ezitare.", 0), ("B) M-aș gândi serios.", 20), ("C) Probabil nu.", 80), ("D) Nu, nu aș putea trăi cu mine.", 100)]
        )
    ]

    count_inserted = 0
    
    try:
        # 1. Ștergem întrebările vechi pentru acest ID (ca să nu le duplicăm la rulări multiple)
        # NOTA: În producție, nu ștergem, doar arhivăm. Aici e development.
        cursor.execute("DELETE FROM question_options WHERE question_hash IN (SELECT version_hash FROM questions_bank WHERE axis_id=?)", (AXIS_ID,))
        cursor.execute("DELETE FROM questions_bank WHERE axis_id=?", (AXIS_ID,))
        
        # 2. Inserare Întrebări Noi
        for q_text, tags, wave, options in questions_dataset:
            
            # Generăm Hash-ul (Amprenta unică)
            v_hash = generate_hash(q_text, options)
            
            # Inserăm Întrebarea
            cursor.execute("""
                INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (AXIS_ID, v_hash, q_text, tags, wave))
            
            # Inserăm Opțiunile
            labels = ['A', 'B', 'C', 'D']
            for idx, (opt_text, score) in enumerate(options):
                cursor.execute("""
                    INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                    VALUES (?, ?, ?, ?)
                """, (v_hash, labels[idx], opt_text, score))
            
            count_inserted += 1

        conn.commit()
        log("db_conn", f"Succes! S-au adăugat {count_inserted} întrebări pentru Axa ID {AXIS_ID}.")

    except sqlite3.Error as e:
        log_error("Eroare la popularea întrebărilor", e)
    finally:
        conn.close()

if __name__ == "__main__":
    populate_sincerity_questions()