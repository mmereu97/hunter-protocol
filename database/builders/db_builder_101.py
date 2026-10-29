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
AXIS_ID = 101
AXIS_NAME = "Sindrom Impostor"
# Pol 0: Încrezător / Autentic
# Pol 100: Fals / Frică / Impostor

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
    log("sys", f"Populăm Monstrul {AXIS_ID}: {AXIS_NAME}...")

    # Punctaj: 100 = SINDROM IMPOSTOR (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Atribuirea Succesului) ---
        (
            "Când ai un succes major la muncă, care este primul gând?",
            "Success Attribution, Luck vs Skill", 
            1, 
            [
                ("A) 'Am muncit mult, merit asta'.", 0), 
                ("B) 'A fost o muncă de echipă bună'.", 30), 
                ("C) 'Am avut noroc că nu s-a complicat situația'.", 70), 
                ("D) 'Sper să nu își dea seama că nu știu ce fac'.", 100)
            ]
        ),
        (
            "Cum reacționezi la laude și complimente profesionale?",
            "Compliments, Acceptance", 
            1, 
            [
                ("A) Le accept cu plăcere.", 0), 
                ("B) Mulțumesc modest.", 30), 
                ("C) Mă simt stânjenit și schimb subiectul.", 70), 
                ("D) Simt că persoana respectivă se înșală sau vrea ceva.", 100)
            ]
        ),
        (
            "Te compari adesea cu colegii tăi și simți că ei sunt mai inteligenți sau mai competenți?",
            "Comparison, Inferiority", 
            1, 
            [
                ("A) Nu, îmi știu valoarea.", 0), 
                ("B) Uneori, e o competiție sănătoasă.", 30), 
                ("C) Da, adesea mă simt inferior.", 70), 
                ("D) Da, simt că eu doar mă prefac, iar ei chiar știu.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Perfecționism / Frică) ---
        (
            "Muncești excesiv de mult la sarcini simple doar pentru a te asigura că nu există nicio greșeală?",
            "Overworking, Perfectionism, Fear", 
            2, 
            [
                ("A) Nu, lucrez eficient.", 0), 
                ("B) Verific, dar nu exagerez.", 30), 
                ("C) Da, uneori pierd mult timp.", 70), 
                ("D) Da, muncesc dublu față de alții doar ca să nu fiu criticat.", 100)
            ]
        ),
        (
            "Eziti să îți exprimi opinia în ședințe de teamă că vei spune o prostie?",
            "Speaking Up, Anxiety, Confidence", 
            2, 
            [
                ("A) Nu, vorbesc deschis.", 0), 
                ("B) Vorbesc dacă sunt sigur.", 30), 
                ("C) Prefer să tac și să ascult.", 70), 
                ("D) Da, sunt terifiat să nu zic ceva greșit și să mă judece.", 100)
            ]
        ),
        (
            "Dacă faci o greșeală mică, te gândești că asta îți va ruina reputația sau cariera?",
            "Catastrophizing, Mistakes", 
            2, 
            [
                ("A) Nu, toți greșim.", 0), 
                ("B) Mă supăr, dar repar.", 30), 
                ("C) Mă îngrijorez destul de mult.", 70), 
                ("D) Da, simt că acum 'masca va cădea' și voi fi concediat.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Frica de Demascare / "Frauda") ---
        (
            "Trăiești cu frica constantă că într-o zi cineva va intra pe ușă și va spune: 'Tu nu ai ce căuta aici'?",
            "The Fraud Fear, Core Impostor", 
            3, 
            [
                ("A) Niciodată. Sunt la locul potrivit.", 0), 
                ("B) Am avut gândul ăsta la început, dar a trecut.", 20), 
                ("C) Uneori am dubii.", 70), 
                ("D) Da, este coșmarul meu recurent.", 100)
            ]
        ),
        (
            "Ai refuzat oportunități de promovare sau proiecte noi pentru că ți-a fost frică că nu vei face față?",
            "Avoidance, Career Sabotage", 
            3, 
            [
                ("A) Nu, caut provocările.", 0), 
                ("B) Sunt precaut, dar accept.", 30), 
                ("C) Am ezitat mult.", 70), 
                ("D) Da, am refuzat pentru că știam că voi eșua.", 100)
            ]
        ),
        (
            "Simți că succesul tău se datorează unor factori externi (noroc, relații, timing) și nu abilităților tale?",
            "External Attribution, Discounting", 
            3, 
            [
                ("A) Nu, e munca mea.", 0), 
                ("B) Norocul ajută, dar munca e baza.", 30), 
                ("C) Adesea cred că am avut doar noroc.", 70), 
                ("D) Da. Am păcălit pe toată lumea până acum.", 100)
            ]
        ),
        (
            "Cât de greu îți este să accepți că ești un expert în domeniul tău?",
            "Identity, Expertise", 
            3, 
            [
                ("A) Ușor. Știu ce pot.", 0), 
                ("B) Mă consider competent, nu expert.", 30), 
                ("C) Mi se pare un cuvânt prea mare.", 70), 
                ("D) Imposibil. Mai am atâtea de învățat, nu știu nimic.", 100)
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