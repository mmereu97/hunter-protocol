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
AXIS_ID = 32
AXIS_NAME = "Fantezie"
# Pol Stânga (0): Realist / Pragmatic / Ancorat
# Pol Dreapta (100): Visător / Imaginativ / Aerian

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
    # Punctaj: 0 = Realist, 100 = Visător
    
    questions_data = [
        # --- VALUL 1 (SCREENING - Obiceiuri Mentale) ---
        (
            "Cât de des te surprinzi visând cu ochii deschiși (daydreaming) în timpul unor activități de rutină?",
            "Daydreaming, Focus, Imagination", 
            1, 
            [
                ("A) Niciodată. Sunt mereu prezent la ce fac.", 0), 
                ("B) Rar, doar dacă sunt foarte plictisit.", 30), 
                ("C) Destul de des îmi fuge mintea.", 70), 
                ("D) Constant. Trăiesc într-o lume paralelă a gândurilor mele.", 100)
            ]
        ),
        (
            "Ce gen de filme sau cărți preferi?",
            "Fiction vs Reality, Preferences", 
            1, 
            [
                ("A) Documentare, biografii, știri (Realitate).", 0), 
                ("B) Filme de acțiune sau comedii realiste.", 30), 
                ("C) Thriller sau mister.", 60), 
                ("D) Fantasy, SF, lumi imaginare complexe (Ficțiune pură).", 100)
            ]
        ),
        (
            "Când ai o problemă de rezolvat, cum abordezi situația?",
            "Problem Solving, Pragmatism vs Creativity", 
            1, 
            [
                ("A) Caut cea mai rapidă și testată soluție practică.", 0), 
                ("B) Mă bazez pe experiența trecută.", 30), 
                ("C) Încerc să găsesc o abordare nouă.", 70), 
                ("D) Îmi imaginez scenarii complexe și soluții neconvenționale ('What if?').", 100)
            ]
        ),

        # --- VALUL 2 (CONFIRMARE - Imersivitate/Copilărie) ---
        (
            "Când citești o carte bună sau vezi un film, cât de tare te 'pierzi' în poveste?",
            "Immersion, Empathy, Fantasy", 
            2, 
            [
                ("A) Rămân un observator detașat.", 0), 
                ("B) Îmi place, dar rămân conștient de realitate.", 30), 
                ("C) Mă prinde povestea.", 70), 
                ("D) Total. Uit unde sunt, trăiesc povestea ca și cum aș fi acolo.", 100)
            ]
        ),
        (
            "În copilărie, aveai prieteni imaginari sau îți creai lumi fantastice complexe?",
            "Childhood, Creativity, Play", 
            2, 
            [
                ("A) Nu, mă jucam cu mingea sau jocuri concrete.", 0), 
                ("B) Mă jucam 'de-a v-ați ascunselea', jocuri normale.", 30), 
                ("C) Aveam scenarii de joacă destul de elaborate.", 70), 
                ("D) Da, aveam un întreg univers imaginar foarte detaliat.", 100)
            ]
        ),
        (
            "Îți place să îți imaginezi cum ar fi viața ta în scenarii imposibile (ex: dacă ai avea superputeri, dacă ai trăi în viitor)?",
            "Hypothetical, Imagination", 
            2, 
            [
                ("A) Nu, e o pierdere de timp.", 0), 
                ("B) Rar, poate în glumă.", 30), 
                ("C) Uneori, înainte să adorm.", 70), 
                ("D) Da, fac asta des. E refugiul meu.", 100)
            ]
        ),

        # --- VALUL 3 (DEEP DIVE - Trigger Monstru: Disociere / Gândire Bizară / Lipsă Focus) ---
        (
            "Ți se întâmplă să fii atât de absorbit de gândurile tale încât să nu auzi când cineva îți vorbește?",
            "Absent-mindedness, Dissociation", 
            3, 
            [
                ("A) Niciodată. Sunt mereu alert.", 0), 
                ("B) Foarte rar.", 20), 
                ("C) Mi se mai întâmplă.", 70), 
                ("D) Da, prietenii îmi spun des că sunt 'aerian' sau 'în lumea mea'.", 100)
            ]
        ),
        (
            "Consideri că realitatea cotidiană este adesea plictisitoare și banală în comparație cu ceea ce se întâmplă în mintea ta?",
            "Escapism, Reality vs Fantasy", 
            3, 
            [
                ("A) Nu, realitatea e singurul lucru care contează.", 0), 
                ("B) Realitatea e ok, trebuie gestionată.", 30), 
                ("C) Uneori prefer să evadez în minte.", 70), 
                ("D) Da, realitatea e gri. Lumea mea interioară e mult mai colorată.", 100)
            ]
        ),
        (
            "Ai idei artistice sau creative care îți vin spontan, chiar dacă nu ești artist?",
            "Creative Flow, Inspiration", 
            3, 
            [
                ("A) Nu, sunt o persoană tehnică/practică.", 0), 
                ("B) Am idei bune pentru muncă, dar nu 'artistice'.", 30), 
                ("C) Uneori am idei interesante.", 70), 
                ("D) Da, mintea mea generează constant idei, imagini și scenarii.", 100)
            ]
        ),
        (
            "Cât de vie este imaginația ta vizuală? (Dacă închizi ochii, poți 'vedea' un măr?)",
            "Aphantasia check, Visualization", 
            3, 
            [
                ("A) Văd doar negru sau concepte vagi (Afantazie).", 0), 
                ("B) Văd o imagine ștearsă, neclară.", 30), 
                ("C) Văd destul de clar.", 70), 
                ("D) Văd ca în realitate, colorat și 3D (Hiperfantazie).", 100)
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