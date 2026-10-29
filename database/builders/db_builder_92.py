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
AXIS_ID = 92
AXIS_NAME = "Neglijență (Safety Risk)"
# Pol 0: Responsabil / Atent
# Pol 100: Neglijent / Pericol Accident

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

    # Punctaj: 100 = NEGLIJENT (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Ordine / Proceduri) ---
        (
            "Cât de des ți se întâmplă să pierzi lucruri importante (chei, acte, telefon) sau să uiți unde le-ai pus?",
            "Organization, Memory, Carelessness", 
            1, 
            [
                ("A) Niciodată. Sunt foarte organizat.", 0), 
                ("B) Rar, când sunt foarte obosit.", 30), 
                ("C) Destul de des, sunt puțin împrăștiat.", 70), 
                ("D) Zilnic. Pierd tot timpul câte ceva.", 100)
            ]
        ),
        (
            "Ce părere ai despre regulile stricte de protecție a muncii (ex: purtarea căștii, proceduri de verificare)?",
            "Safety, Rules, Attitude", 
            1, 
            [
                ("A) Sunt vitale. Le respect cu sfințenie.", 0), 
                ("B) Sunt bune, dar uneori exagerate.", 30), 
                ("C) Încetinesc munca inutil.", 70), 
                ("D) Sunt birocrație pură. Dacă ești atent, nu pățești nimic.", 100)
            ]
        ),
        (
            "Dacă verși cafea pe birou sau faci mizerie în spațiul comun, ce faci?",
            "Hygiene, Responsibility, Consideration", 
            1, 
            [
                ("A) Curăț imediat totul lună.", 0), 
                ("B) Șterg mare parte.", 20), 
                ("C) Las așa, vine femeia de serviciu.", 80), 
                ("D) Nu observ sau nu-mi pasă.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Detalii / Calitate) ---
        (
            "Când completezi un formular sau un raport, verifici datele înainte de a-l trimite?",
            "Attention to Detail, Quality Control", 
            2, 
            [
                ("A) Verific de două ori.", 0), 
                ("B) Mă uit rapid peste el.", 30), 
                ("C) Nu, de obicei e corect din prima.", 60), 
                ("D) Nu. Dacă e o greșeală, o va găsi altcineva.", 100)
            ]
        ),
        (
            "Ți s-a întâmplat să uiți o sarcină importantă primită de la șef sau un deadline?",
            "Reliability, Memory, Neglect", 
            2, 
            [
                ("A) Nu, îmi notez tot.", 0), 
                ("B) O dată, a fost o excepție.", 30), 
                ("C) Uneori, dacă sunt aglomerat.", 70), 
                ("D) Da, am nevoie ca cineva să îmi amintească constant.", 100)
            ]
        ),
        (
            "Cum arată mașina sau spațiul tău de lucru în acest moment?",
            "Environment, Chaos, Mess", 
            2, 
            [
                ("A) Curat și organizat.", 0), 
                ("B) Puțin dezordine, dar funcțional.", 30), 
                ("C) Destul de plin de gunoaie/hârtii.", 70), 
                ("D) Un dezastru total. Nu găsesc nimic.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Risc Accident / Apatie) ---
        (
            "Dacă un echipament are o defecțiune minoră, dar încă funcționează, îl raportezi?",
            "Maintenance, Proactive, Safety Risk", 
            3, 
            [
                ("A) Da, imediat. Poate deveni periculos.", 0), 
                ("B) Notez undeva.", 30), 
                ("C) Îl folosesc așa până crapă de tot.", 70), 
                ("D) Nu e treaba mea. Să vadă mecanicul.", 100)
            ]
        ),
        (
            "Ai provocat vreodată o pagubă materială (accident auto, echipament stricat) din cauza neatenției?",
            "Accidents, Damage History", 
            3, 
            [
                ("A) Nu, sunt foarte prudent.", 0), 
                ("B) Doar zgârieturi minore.", 30), 
                ("C) Da, câteva incidente.", 70), 
                ("D) Da, am un istoric de accidente din neatenție.", 100)
            ]
        ),
        (
            "Ce simți când ți se spune 'Fii mai atent!'?",
            "Reaction to Feedback, Ego", 
            3, 
            [
                ("A) Mă concentrez mai tare.", 0), 
                ("B) Îmi cer scuze.", 20), 
                ("C) Mă irită, nu sunt robot.", 70), 
                ("D) Mă enervez. Toți greșesc, ce au cu mine?", 100)
            ]
        ),
        (
            "Ești dispus să tai colțurile ('cut corners') sau să sari peste pașii de siguranță pentru a termina treaba mai repede?",
            "Shortcuts, Risk, Efficiency vs Safety", 
            3, 
            [
                ("A) Niciodată. Siguranța e prima.", 0), 
                ("B) Doar dacă nu e niciun risc real.", 30), 
                ("C) Da, procedurile sunt prea lungi.", 70), 
                ("D) Da, mereu. Contează viteza, nu birocrația.", 100)
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