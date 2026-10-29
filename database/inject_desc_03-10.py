import sqlite3
import os
import sys

# --- CALE DINAMICĂ (INFALIBILĂ) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from config import Config
DB_PATH = Config.DB_NAME

def inject_batch_descriptions():
    if not os.path.exists(DB_PATH):
        print(f"❌ EROARE: Baza de date nu există la: {DB_PATH}")
        return

    # DICTIONAR CU DATELE (ID: Text)
    descriptions = {
        # --- ID 3: EVITAREA LĂCOMIEI ---
        3: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează importanța pe care subiectul o acordă posesiunilor materiale, luxului și bogăției ca indicatori ai statutului social. Măsoară motivația extrinsecă financiară versus mulțumirea cu un stil de viață simplu.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Materialism și Lăcomie. Subiectul este motivat puternic de bani, branduri de lux și afișarea statutului. Poate fi dispus să sacrifice relații sau etică pentru câștig financiar. Risc de "Flight Risk" dacă primește o ofertă mai bună financiar.
Scor Ridicat (70-100): Indică Detașare Materială. Subiectul nu este impresionat de lux sau bogăție și nu consideră banii un scop în sine. Poate lipsi ambiția financiară agresivă necesară în roluri de vânzări "hunter".

NOTE TEHNICE:
Sursă: HEXACO H (Greed Avoidance).
Corelații: Scor mic aici + Scor mic la Corectitudine (ID 2) = Profil de Risc Maxim pentru Fraudă.""",

        # --- ID 4: MODESTIE ---
        4: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează percepția subiectului asupra propriei importanțe în raport cu ceilalți. Măsoară nivelul de aroganță, sentimentul de îndreptățire (entitlement) și tendința de a se considera superior sau "special".

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Aroganță și Narcisism. Subiectul se consideră superior oamenilor obișnuiți, crede că regulile nu i se aplică și pretinde tratament preferențial. Poate fi un lider carismatic dar toxic.
Scor Ridicat (70-100): Indică Umilință. Subiectul se vede ca un egal al celorlalți, nu caută lumina reflectoarelor și nu pretinde privilegii. Este un jucător de echipă, dar poate avea dificultăți în a se autopromova.

NOTE TEHNICE:
Sursă: HEXACO H (Modesty).
Corelații: Acesta este ingredientul principal în detectarea Narcisismului (ID 52) și a comportamentului "Uncoachable" (ID 93).""",

        # --- ID 5: FRICĂ FIZICĂ ---
        5: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a simți frică în fața durerii fizice, a rănirii sau a morții. Măsoară instinctul de conservare versus curajul fizic (sau imprudența).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Temeritate (Curaj Fizic). Subiectul nu se teme de situații periculoase, sporturi extreme sau confruntări fizice. Risc de accidente prin neglijență sau asumarea unor riscuri inutile.
Scor Ridicat (70-100): Indică Prudență Extremă / Frică. Subiectul evită orice risc fizic, este hipersensibil la durere și preferă siguranța absolută. Poate ezita în situații de criză.

NOTE TEHNICE:
Sursă: HEXACO E (Fearfulness).
Corelații: Scorurile foarte mici pot indica tendințe Psihopate (lipsa fricii) sau comportament Antisocial.""",

        # --- ID 6: ANXIETATE ---
        6: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a se îngrijora excesiv cu privire la viitor și la probleme minore. Măsoară nivelul de stres cronic, ruminarea mentală și reacția somatică la incertitudine.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Calm și Stabilitate. Subiectul nu se stresează ușor, doarme bine și nu anticipează dezastre.
Scor Ridicat (70-100): Indică Anxietate Generalizată. Subiectul trăiește într-o stare de alertă constantă, "își face scenarii", are dificultăți de relaxare și somatizează stresul. Necesită mediu de lucru stabil.

NOTE TEHNICE:
Sursă: HEXACO E (Anxiety) / OCEAN N (Anxiety).
Corelații: Componentă cheie în detectarea Sindromului Impostorului și a Somatizării.""",

        # --- ID 7: DEPENDENȚĂ EMOȚIONALĂ ---
        7: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nevoia de sprijin emoțional, reasigurare și validare din partea celorlalți. Măsoară autonomia emoțională versus neajutorarea în fața problemelor.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Independență Extremă. Subiectul își rezolvă singur problemele, nu cere ajutor și poate părea distant sau "lup singuratic".
Scor Ridicat (70-100): Indică Dependență. Subiectul are nevoie constantă de sfaturi, confirmări și suport ("Clingy"). Se simte pierdut fără un grup sau un mentor. Risc de "Social Loafing" (se ascunde în grup).

NOTE TEHNICE:
Sursă: HEXACO E (Dependence).
Corelații: Scorurile mari corelează cu Atașamentul Anxios (ID 70).""",

        # --- ID 8: SENTIMENTALISM ---
        8: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează forța legăturilor emoționale și sensibilitatea la despărțiri, nostalgie sau suferința altora.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Detașare Emoțională ("Dur"). Subiectul nu plânge, nu pune preț pe nostalgie și ia decizii la rece, fără a fi influențat de sentimente. Risc de răceală în relații.
Scor Ridicat (70-100): Indică Profunzime Emoțională. Subiectul creează legături puternice, este empatic și sentimental. Poate fi vulnerabil la manipulare emoțională.

NOTE TEHNICE:
Sursă: HEXACO E (Sentimentality).
Corelații: Scorurile extrem de mici (sub 10) sunt un marker pentru trăsături Callous-Unemotional (Psihopatie/Alexitimie).""",

        # --- ID 9: DEPRESIE ---
        9: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează dispoziția generală (mood), nivelul de energie vitală și speranța. Nu este un diagnostic clinic, ci o măsură a tendinței spre melancolie și pesimism.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Optimism și Vitalitate. Subiectul este energic, vesel și rezilient.
Scor Ridicat (70-100): Indică Risc Depresiv. Subiectul se simte descurajat, trist, lipsit de energie și pesimist în legătură cu viitorul. Performanța poate fluctua.

NOTE TEHNICE:
Sursă: OCEAN N (Depression) / NEO-PI-R N3.
Corelații: Trigger principal pentru Demoralizare (ID 68) și Victimizare (ID 98).""",

        # --- ID 10: TIMIDITATE SOCIALĂ ---
        10: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează disconfortul resimțit în situații sociale, teama de a fi judecat și jena. Diferă de introversie (care e lipsă de interes); aici e vorba de frică de evaluare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Îndrăzneală Socială ("Tupeu"). Subiectul nu are trac, vorbește ușor în public și nu se rușinează. Ideal pentru vânzări/leadership.
Scor Ridicat (70-100): Indică Anxietate Socială. Subiectul se simte stânjenit în centrul atenției, evită situațiile noi și se teme de ridicol.

NOTE TEHNICE:
Sursă: HEXACO X (Social Boldness - inversat) / OCEAN N (Self-Consciousness).
Corelații: Scorurile mari declanșează alerta pentru Anxietate Socială (ID 107)."""
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        count = 0
        for axis_id, text in descriptions.items():
            c.execute("UPDATE axes SET description = ? WHERE id = ?", (text, axis_id))
            if c.rowcount > 0:
                count += 1
            else:
                print(f"⚠️ Axa ID {axis_id} nu a fost găsită!")

        conn.commit()
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 3-10).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()