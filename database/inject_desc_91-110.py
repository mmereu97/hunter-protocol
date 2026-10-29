import sqlite3
import os
import sys

# --- CALE DINAMICĂ ---
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
        # --- ID 91: HĂRȚUIRE ---
        91: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează lipsa limitelor sociale și tendința spre comportament invaziv sau prădător. Măsoară respectul pentru spațiul personal și consimțământ.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Respect și Profesionalism. Subiectul înțelege limitele sociale și le respectă strict.
Scor Ridicat (70-100): Indică "Prădător Social". Subiectul nu acceptă refuzul, face comentarii nepotrivite, invadează spațiul intim și poate fi hărțuitor sexual sau moral.

NOTE TEHNICE:
Sursă: LPI (Lack of Psychological Boundaries).
Corelații: Se activează când Libidoul (ID 81 - latent), Impulsivitatea (ID 11) și Dominanța (ID 14) sunt mari.""",

        # --- ID 92: NEGLIJENȚĂ ---
        92: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează riscul de accidente și erori cauzate de lipsa de atenție, dezordine și nerespectarea procedurilor de siguranță.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Responsabilitate. Subiectul verifică echipamentele, respectă normele SSM și este metodic.
Scor Ridicat (70-100): Indică Pericol de Accident. Subiectul este haotic, uituc, "lasă că merge și așa", ignoră protocoalele de siguranță.

NOTE TEHNICE:
Sursă: Hogan Safety Report.
Corelații: Opusul Conștiinciozității (ID 24 + 29).""",

        # --- ID 93: UNCOACHABLE ---
        93: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează rezistența la feedback și incapacitatea de a învăța din greșeli din cauza aroganței intelectuale.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică "Coachable" / Umilință. Subiectul cere feedback și vrea să învețe.
Scor Ridicat (70-100): Indică Refractaritate / Aroganță. Subiectul crede că le știe pe toate, reacționează defensiv la critică și dă vina pe alții.

NOTE TEHNICE:
Sursă: CPI (Arrogance scale).
Corelații: Combină Narcisismul (ID 52) cu o Deschidere mică (ID 50).""",

        # --- ID 94: SABOTOR ---
        94: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a submina colegii sau organizația prin manipulare, bârfe strategice și jocuri de culise.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Colegialitate. Subiectul este transparent și joacă fair-play.
Scor Ridicat (70-100): Indică Toxicitate. Subiectul folosește informația ca armă, creează intrigi și se bucură de eșecul rivalilor.

NOTE TEHNICE:
Sursă: Dark Tetrad (Everyday Sadism/Machiavellianism).
Corelații: O formă activă de Machiavelism (ID 51) în mediu profesional.""",

        # --- ID 95: LOAFING (CHIUL) ---
        95: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează "Social Loafing" - tendința de a depune mai puțin efort atunci când lucrează în grup, bazându-se pe munca altora.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Implicare. Subiectul trage pentru echipă.
Scor Ridicat (70-100): Indică Parazitism Social. Subiectul simulează munca, dispare în momentele critice și lasă greul pe alții.

NOTE TEHNICE:
Sursă: Organizational Psychology metrics.
Corelații: Hărnicie mică (ID 25) + Dependență mare (ID 7).""",

        # --- ID 96: MALICIOUS (RĂUTATE) ---
        96: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează "Malicious Compliance" și dorința de răzbunare pasiv-agresivă. Respectarea regulilor doar pentru a bloca procesul sau a face rău.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Bunăvoință.
Scor Ridicat (70-100): Indică Răutate Birocratică. Subiectul sabotează subtil, refuză să ajute invocând regulamente și se bucură de suferința altora.

NOTE TEHNICE:
Sursă: CAST (Sadism).
Corelații: O formă de Sadism (ID 84) mascat de birocrație.""",

        # --- ID 97: FLIGHT RISK ---
        97: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează probabilitatea ca angajatul să părăsească organizația în viitorul apropiat. Măsoară loialitatea vs. oportunismul.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Stabilitate / Loialitate. Subiectul dorește să rămână pe termen lung.
Scor Ridicat (70-100): Indică Mercenar / Risc Demisie. Subiectul caută activ alte joburi, este motivat strict financiar și nu are atașament față de firmă.

NOTE TEHNICE:
Sursă: Mobley Turnover Model.
Corelații: Declansat de Motivație Financiară mare (ID 86) și Loialitate mică (ID 29).""",

        # --- ID 98: VICTIMIZARE ---
        98: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează mentalitatea de victimă: tendința de a atribui eșecurile unor forțe externe, persecuției sau ghinionului, refuzând responsabilitatea.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Asumare (Accountability).
Scor Ridicat (70-100): Indică Mentalitate de Martir. Subiectul se plânge constant, crede că universul conspiră împotriva lui și refuză soluțiile.

NOTE TEHNICE:
Sursă: Rotter (External Locus) + Neuroticism.
Corelații: Locus of Control Extern (ID 65).""",

        # --- ID 99: DEZIRABILITATE SOCIALĂ ---
        99: """DEFINIȚIE OPERAȚIONALĂ:
(LIE SCALE) Evaluează tendința de a falsifica răspunsurile pentru a crea o imagine favorabilă. Măsoară onestitatea testării în sine.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Autenticitate. Subiectul își recunoaște micile defecte umane.
Scor Ridicat (70-100): Indică MINCIUNĂ / Invaliditate. Subiectul neagă defecte universale (ex: "Nu am întârziat niciodată"). Testul trebuie considerat invalid.

NOTE TEHNICE:
Sursă: Marlowe-Crowne Social Desirability Scale.
Corelații: Această axă invalidează restul profilului dacă scorul e > 70.""",

        # --- ID 100: MICROMANAGEMENT ---
        100: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează stilul de leadership sufocant, caracterizat prin control excesiv, lipsa delegării și neîncredere în echipă.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Lider care Delegă. Subiectul se concentrează pe rezultate și are încredere în oameni.
Scor Ridicat (70-100): Indică Control Freak. Subiectul verifică fiecare detaliu, reface munca altora și blochează fluxul de lucru.

NOTE TEHNICE:
Sursă: Hogan HDS (Diligent).
Corelații: Perfecționism (ID 26) + Neîncredere (ID 23).""",

        # --- ID 101: SINDROM IMPOSTOR ---
        101: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează discrepanța dintre competența reală și percepția de sine. Teama de a fi "demascat" ca fraudă.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Încredere în Sine.
Scor Ridicat (70-100): Indică Sindrom Impostor. Subiectul își subestimează realizările, atribuie succesul norocului și trăiește cu frica eșecului.

NOTE TEHNICE:
Sursă: Clance Impostor Phenomenon Scale (CIPS).
Corelații: Competență mare (ID 26) dar Anxietate mare (ID 6).""",

        # --- ID 102: YES-MAN ---
        102: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează lipsa de asertivitate și tendința de a fi de acord cu autoritatea indiferent de opinia personală.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Gândire Critică / Asertivitate.
Scor Ridicat (70-100): Indică Submisivitate Extremă. Subiectul nu contrazice șeful, ascunde problemele pentru a nu supăra și nu are inițiativă.

NOTE TEHNICE:
Sursă: Hogan HDS (Dutiful).
Corelații: Conciliere mare (ID 39) + Asertivitate mică (ID 14).""",

        # --- ID 103: ADHD (DISFUNCȚIE EXECUTIVĂ) ---
        103: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează simptomele de deficit de atenție: dificultăți de concentrare, dezorganizare, uitare și impulsivitate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Funcție Executivă Bună.
Scor Ridicat (70-100): Indică Risc ADHD. Probleme majore de time-management, focus și finalizare a sarcinilor.

NOTE TEHNICE:
Sursă: ASRS-v1.1 (Adult ADHD Self-Report Scale).
Corelații: Focus mic (ID 110) + Organizare mică (ID 24).""",

        # --- ID 104: AUTISM (SPECTRU ASD) ---
        104: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează trăsăturile de spectru autist: dificultăți de comunicare socială, interese obsesive, rigiditate și sensibilitate senzorială.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Intuiție Socială.
Scor Ridicat (70-100): Indică Trăsături ASD. Gândire literală, dificultăți în citirea limbajului non-verbal, nevoie de rutină strictă.

NOTE TEHNICE:
Sursă: AQ Test (Autism Spectrum Quotient).
Corelații: Sociabilitate mică (ID 15) + HSP mare (ID 80).""",

        # --- ID 105: OCPD (PERFECȚIONISM PATOLOGIC) ---
        105: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează Tulburarea de Personalitate Obsesiv-Compulsivă (nu OCD). Nevoia de ordine, perfecționism și control mental/interpersonal în detrimentul flexibilității.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Flexibilitate.
Scor Ridicat (70-100): Indică OCPD. Rigiditate extremă, zgârcenie, devotament excesiv pentru muncă, incapacitate de a arunca obiecte vechi.

NOTE TEHNICE:
Sursă: DSM-5 / OCPD criteria.
Corelații: Perfecționism (ID 26) + Flexibilitate mică (ID 21).""",

        # --- ID 106: BPD (BORDERLINE) ---
        106: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează instabilitatea emoțională, relațiile intense și instabile, teama de abandon și impulsivitatea.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Stabilitate Emoțională.
Scor Ridicat (70-100): Indică Trăsături Borderline. Dispoziție fluctuantă, furie intensă, idealizare/devalorizare ("Splitting").

NOTE TEHNICE:
Sursă: MSI-BPD (McLean Screening Instrument).
Corelații: Anxietate (ID 6) + Ostilitate (ID 37) + Atașament Anxios (ID 70).""",

        # --- ID 107: ANXIETATE SOCIALĂ ---
        107: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează frica marcată de situații sociale în care subiectul este expus posibilei examinări de către alții.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Dezinvoltură.
Scor Ridicat (70-100): Indică Fobie Socială. Evitarea situațiilor sociale, simptome fizice de panică la expunere, frică de umilință.

NOTE TEHNICE:
Sursă: LSAS (Liebowitz Social Anxiety Scale).
Corelații: Formă extremă a Timidității (ID 10).""",

        # --- ID 108: TULBURARE BIPOLARĂ ---
        108: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează prezența episoadelor maniacale sau hipomaniacale: energie excesivă, nevoie scăzută de somn, grandoare și fugă de idei.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Stabilitate (Eutimie).
Scor Ridicat (70-100): Indică Risc Bipolar. Fluctuații ciclice între energie extremă și depresie.

NOTE TEHNICE:
Sursă: MDQ (Mood Disorder Questionnaire).
Corelații: Vivacitate extremă (ID 16) + Impulsivitate (ID 11).""",

        # --- ID 109: MOBILITATE ---
        109: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru un stil de viață și de muncă dinamic, care implică deplasări, versus stabilitatea geografică.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Sedentarism. Subiectul preferă munca de birou, rutina și proximitatea față de casă.
Scor Ridicat (70-100): Indică Nomadism. Subiectul caută joburi de teren, delegații, relocări și se plictisește într-un singur loc.

NOTE TEHNICE:
Sursă: Hunter Protocol V1 Legacy.
Corelații: Risc de Flight Risk (ID 97) dacă este ținut în birou.""",

        # --- ID 110: STIL DE ATENȚIE (FOCUS) ---
        110: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de concentrare profundă ("Deep Work") versus stilul de lucru distributiv și fragmentat.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică "Popcorn Brain". Subiectul face multitasking, se distrage ușor, preferă stimuli rapizi. Risc de erori.
Scor Ridicat (70-100): Indică Focus Monahal. Subiectul poate lucra ore în șir fără întrerupere la sarcini complexe.

NOTE TEHNICE:
Sursă: Cal Newport / Cognitive Psychology.
Corelații: Opusul simptomelor ADHD (ID 103)."""
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
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 91-110).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()