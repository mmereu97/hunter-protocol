import sqlite3
import hashlib
import json
import os
import sys

# SETUP PATHS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

AXIS_ID = 57
AXIS_NAME = "Influență Emoțională (EQ)"

def generate_hash(text, options_list):
    content_string = text + json.dumps(options_list, sort_keys=True)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()

def populate_questions():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path): return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    log("sys", f"Populăm {AXIS_NAME} (ID {AXIS_ID})...")

    # Punctaj: 0 = Pasiv, 100 = Influent/Persuasiv
    questions_data = [
        # --- VALUL 1: SCREENING (Impact Social General) ---
        (
            "Cât de ușor îți este să schimbi părerea cuiva într-o discuție, aducându-l de partea ta?",
            "Persuasion, Influence, Debate", 1, 
            [
                ("A) Foarte greu. De obicei cedez eu.", 0), 
                ("B) Reușesc doar dacă am argumente logice imbatabile.", 30), 
                ("C) Destul de ușor, știu ce corzi să ating.", 70), 
                ("D) Foarte ușor. Oamenii tind să fie de acord cu mine natural.", 100)
            ]
        ),
        (
            "Dacă un prieten este trist sau deprimat, reușești să îi ridici moralul?",
            "Comforting, Mood Regulation, Empathy", 1, 
            [
                ("A) Nu, mă simt neputincios și tac.", 0), 
                ("B) Încerc, dar uneori îl supăr mai tare.", 30), 
                ("C) Da, de obicei îl fac să se simtă mai bine.", 70), 
                ("D) Da, sunt persoana la care toți vin pentru încurajare.", 100)
            ]
        ),
        (
            "Când intri într-un grup nou, cât de repede te faci remarcat sau ascultat?",
            "Charisma, Social Presence", 1, 
            [
                ("A) Rămân invizibil mult timp.", 0), 
                ("B) Vorbesc doar cu 1-2 persoane.", 30), 
                ("C) Mă integrez repede.", 70), 
                ("D) Imediat. Captez atenția camerei fără efort.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Negociere / Conflict) ---
        (
            "Te afli în fața unei persoane furioase și iraționale. Ce șanse ai să o calmezi?",
            "De-escalation, Conflict Resolution", 2, 
            [
                ("A) Zero. Mă panichez sau mă enervez și eu.", 0), 
                ("B) Aștept să-i treacă.", 30), 
                ("C) Încerc să-i vorbesc calm și rațional.", 60), 
                ("D) Mari. Știu exact ce ton și ce cuvinte să folosesc pentru a dezamorsa bomba.", 100)
            ]
        ),
        (
            "Cât de bun ești la negocieri (prețuri, salarii, favoruri)?",
            "Negotiation, Sales, Assertiveness", 2, 
            [
                ("A) Slab. Accept ce mi se oferă.", 0), 
                ("B) Încerc, dar mă simt inconfortabil.", 30), 
                ("C) Bun. Obțin adesea ce vreau.", 70), 
                ("D) Excelent. Negocierea este un joc psihologic pe care îl domin.", 100)
            ]
        ),
        (
            "Dacă ai nevoie de ajutor pentru un proiect, cât de ușor convingi oamenii să ți se alăture voluntar?",
            "Leadership, Mobilization", 2, 
            [
                ("A) Trebuie să mă rog de ei.", 0), 
                ("B) Dacă le explic beneficiile logice, vin.", 30), 
                ("C) Destul de ușor.", 70), 
                ("D) Foarte ușor. Îi inspir și îi motivez să vrea să ajute.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Manipulare vs Inspirație) ---
        (
            "Oamenii îți spun adesea că ai o 'energie bună' care îi calmează sau îi înviorează?",
            "Vibe, Aura, Charisma", 3, 
            [
                ("A) Nu.", 0), 
                ("B) Unii prieteni apropiați.", 30), 
                ("C) Da, destul de des.", 70), 
                ("D) Da, mi se spune că sunt 'terapeutic' sau 'magnetic'.", 100)
            ]
        ),
        (
            "Poți să faci pe cineva să se simtă vinovat sau responsabil fără să îi spui asta direct?",
            "Subtle Influence, Emotional Manipulation", 3, 
            [
                ("A) Nu, sunt foarte direct.", 0), 
                ("B) Nu îmi place să fac asta.", 20), 
                ("C) Da, prin tăcere sau privire.", 70), 
                ("D) Da. Pot controla emoțiile altora ca pe un instrument.", 100)
            ]
        ),
        (
            "Dacă ești oprit de poliție sau prins într-o situație dificilă, încerci să 'te scoți' prin vorbe?",
            "Charm, Social Agility", 3, 
            [
                ("A) Nu, îmi asum consecințele tăcut.", 0), 
                ("B) Răspund politicos, dar atât.", 30), 
                ("C) Încerc să fiu simpatic, poate scap.", 70), 
                ("D) Da, și îmi iese des. Vorba dulce mult aduce.", 100)
            ]
        ),
        (
            "Cât de importantă este pentru tine capacitatea de a 'citi' și influența oamenii pentru succesul tău?",
            "Values, Machiavellianism vs EQ", 3, 
            [
                ("A) Deloc. Competența tehnică contează.", 0), 
                ("B) E utilă, dar nu esențială.", 30), 
                ("C) Este o abilitate cheie.", 70), 
                ("D) Este arma mea secretă și cea mai importantă calitate.", 100)
            ]
        )
    ]

    try:
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
        # MESAJUL DE SUCCES CU ID INCLUS
        log("db_conn", f"SUCCES: Întrebări '{AXIS_NAME}' (ID {AXIS_ID}) inserate.")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_questions()