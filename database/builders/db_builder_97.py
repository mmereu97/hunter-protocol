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
AXIS_ID = 97
AXIS_NAME = "Flight Risk (Risc Demisie)"
# Pol 0: Loial / Stabil
# Pol 100: Mercenar / Instabil

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

    # Punctaj: 100 = FLIGHT RISK (MONSTRU ACTIVAT)
    questions_data = [
        # --- VALUL 1: SCREENING (Motivație Financiară / Căutare Job) ---
        (
            "Dacă mâine o altă companie îți oferă un salariu cu 10-15% mai mare pentru același rol, ce faci?",
            "Salary Sensitivity, Loyalty", 
            1, 
            [
                ("A) Refuz. Îmi place unde sunt și colegii contează.", 0), 
                ("B) Mă gândesc, dar probabil rămân.", 30), 
                ("C) Merg la interviu să văd despre ce e vorba.", 70), 
                ("D) Accept imediat. Lucrez pentru bani, nu pentru glorie.", 100)
            ]
        ),
        (
            "Cât de des verifici site-urile de joburi sau răspunzi recrutorilor pe LinkedIn?",
            "Job Hunting, Satisfaction", 
            1, 
            [
                ("A) Niciodată, nu sunt interesat.", 0), 
                ("B) Rar, doar dacă apare ceva wow.", 30), 
                ("C) Lunar, să fiu la curent cu piața.", 70), 
                ("D) Săptămânal sau zilnic. Sunt mereu în căutare.", 100)
            ]
        ),
        (
            "Ce te ține cel mai mult la un loc de muncă?",
            "Retention Factors, Values vs Money", 
            1, 
            [
                ("A) Colegii, mediul și misiunea firmei.", 0), 
                ("B) Stabilitatea și echilibrul viață-muncă.", 30), 
                ("C) Oportunitățile de avansare.", 60), 
                ("D) Salariul și bonusurile. Restul sunt povești.", 100)
            ]
        ),

        # --- VALUL 2: CONFIRMARE (Istoric / Plictiseală) ---
        (
            "Care este durata medie pe care ai petrecut-o la joburile anterioare?",
            "Job History, Stability", 
            2, 
            [
                ("A) Peste 5 ani.", 0), 
                ("B) 3-5 ani.", 20), 
                ("C) 1-2 ani.", 60), 
                ("D) Sub 1 an. Mă plictisesc repede sau găsesc ceva mai bun.", 100)
            ]
        ),
        (
            "Cum te simți când firma trece printr-o perioadă grea (ex: tăieri de buget, criză)?",
            "Resilience, Loyalty in Crisis", 
            2, 
            [
                ("A) Sunt motivat să ajut firma să își revină.", 0), 
                ("B) Îngrijorat, dar aștept.", 30), 
                ("C) Îmi actualizez CV-ul preventiv.", 70), 
                ("D) Plec primul. Nu stau pe o corabie care se scufundă.", 100)
            ]
        ),
        (
            "Cât de important este pentru tine 'brandul' de angajator sau prestigiul firmei?",
            "Prestige, Resume Building", 
            2, 
            [
                ("A) Contează să mă simt eu bine, nu numele.", 0), 
                ("B) E un factor secundar.", 30), 
                ("C) Contează destul de mult.", 60), 
                ("D) Foarte mult. Folosesc firma ca trambulină pentru CV.", 100)
            ]
        ),

        # --- VALUL 3: DEEP DIVE (Mercenarism Pur / Lipsă Ataşament) ---
        (
            "Dacă șeful tău actual ar pleca la o firmă concurentă și te-ar chema, te-ai duce?",
            "Loyalty to Person vs Company", 
            3, 
            [
                ("A) Depinde de condiții, dar sunt loial firmei.", 0), 
                ("B) M-aș gândi.", 30), 
                ("C) Probabil da.", 70), 
                ("D) Imediat. Sunt loial oamenilor/banilor, nu companiilor.", 100)
            ]
        ),
        (
            "Consideri că loialitatea față de angajator este un concept învechit?",
            "Work Philosophy, Gig Economy", 
            3, 
            [
                ("A) Nu, loialitatea se răsplătește pe termen lung.", 0), 
                ("B) Este reciprocă: cât dau ei, dau și eu.", 30), 
                ("C) Da, azi trebuie să fii agil.", 70), 
                ("D) Absolut. Suntem mercenari, vindem timp pe bani.", 100)
            ]
        ),
        (
            "Ai pleca într-o altă țară sau oraș pentru un job mult mai bine plătit, lăsând totul în urmă rapid?",
            "Mobility, Detachment", 
            3, 
            [
                ("A) Nu, rădăcinile mele sunt aici.", 0), 
                ("B) Doar dacă pot lua familia.", 30), 
                ("C) Da, pentru o perioadă.", 70), 
                ("D) Da, mâine. Banii sunt prioritatea.", 100)
            ]
        ),
        (
            "Când te angajezi, te gândești deja la următorul pas în carieră (în afara acelei companii)?",
            "Future Planning, Job Hopping", 
            3, 
            [
                ("A) Nu, sper să cresc intern.", 0), 
                ("B) Nu de la început.", 20), 
                ("C) Da, e bine să ai un plan B.", 60), 
                ("D) Da, văd jobul actual doar ca pe o etapă scurtă.", 100)
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