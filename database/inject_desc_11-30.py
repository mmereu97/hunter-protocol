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
        # --- ID 11: IMPULSIVITATE ---
        11: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de control inhibitor asupra dorințelor și reacțiilor imediate. Măsoară tendința de a acționa sub imperiul momentului versus deliberarea consecințelor.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Autocontrol Puternic. Subiectul rezistă tentațiilor, își controlează reacțiile verbale și amână gratificarea.
Scor Ridicat (70-100): Indică Impulsivitate. Subiectul are dificultăți în a se abține ("gura o ia înaintea minții"), cheltuie bani nesăbuit sau reacționează vulcanic la stres.

NOTE TEHNICE:
Sursă: NEO-PI-R N5 (Impulsiveness).
Corelații: Factor de risc major pentru Hărțuire (ID 91), Agresivitate (ID 89) și Dezinhibiție (ID 76).""",

        # --- ID 12: RĂBDARE ---
        12: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează pragul de toleranță la frustrare și iritabilitate. Măsoară capacitatea de a rămâne calm în fața incompetenței altora, a întârzierilor sau a obstacolelor minore.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Irascibilitate ("Fitil Scurt"). Subiectul se enervează rapid, devine sarcastic sau agresiv verbal când lucrurile nu merg bine.
Scor Ridicat (70-100): Indică Stoicism. Subiectul își păstrează calmul în situații stresante și nu reacționează emoțional la provocări minore.

NOTE TEHNICE:
Sursă: HEXACO A (Patience).
Corelații: Scorurile mici sunt predictor pentru Agresivitate și conflicte de muncă.""",

        # --- ID 13: STIMĂ DE SINE SOCIALĂ ---
        13: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează percepția subiectului asupra propriei valori în contexte sociale. Măsoară încrederea că este plăcut, interesant și capabil să contribuie la grup.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nesiguranță Socială. Subiectul se simte "invizibil" sau inadecvat, evită să își spună opinia de teama judecății.
Scor Ridicat (70-100): Indică Carismă și Încredere. Subiectul se simte confortabil în centrul atenției și consideră că are calități de lider.

NOTE TEHNICE:
Sursă: HEXACO X (Social Self-Esteem).
Corelații: Scorurile mici sunt asociate cu Anxietatea Socială (ID 107) și Sindromul Impostorului (ID 101).""",

        # --- ID 14: ASERTIVITATE / DOMINANȚĂ ---
        14: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a prelua conducerea, de a-și impune punctul de vedere și de a influența comportamentul altora.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Submisivitate. Subiectul evită conflictul, cedează ușor și preferă să execute decât să decidă. Risc de a fi un "Yes-Man".
Scor Ridicat (70-100): Indică Dominanță. Subiectul este un lider natural, vorbește ferm și își apără interesele. În exces, poate deveni autoritar.

NOTE TEHNICE:
Sursă: NEO-PI-R E3 (Assertiveness) / HEXACO X.
Corelații: Scorurile extreme (>90) pot indica risc de Narcisism sau comportament "Uncoachable".""",

        # --- ID 15: SOCIABILITATE ---
        15: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru interacțiunea socială ca sursă de energie ("Bateria Socială"). Distinge între introvertiți (care obosesc social) și extrovertiți (care se încarcă social).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Introverțiune. Subiectul preferă munca individuală și grupurile mici. Are nevoie de timp singur pentru a se reface.
Scor Ridicat (70-100): Indică Extroversiune. Subiectul caută compania oamenilor, urăște singurătatea și este foarte comunicativ.

NOTE TEHNICE:
Sursă: NEO-PI-R E2 (Gregariousness) / HEXACO X.
Corelații: Critic pentru potrivirea pe post (Vânzări vs. Programare).""",

        # --- ID 16: VIVACITATE (ENERGIE) ---
        16: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează ritmul de viață, nivelul de energie fizică și entuziasmul general.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Ritm Lent / Pasivitate. Subiectul preferă o viață liniștită, se mișcă și vorbește calm, poate părea lipsit de urgență.
Scor Ridicat (70-100): Indică Dinamism. Subiectul este mereu ocupat, vorbește repede, are multă energie și rezistență la efort prelungit.

NOTE TEHNICE:
Sursă: NEO-PI-R E4 (Activity) / HEXACO X (Liveliness).
Corelații: Scorurile foarte mici pot indica risc de Depresie (ID 9) sau Burnout (ID 77).""",

        # --- ID 17: CĂUTAREA SENZAȚIILOR ---
        17: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nevoia de stimulare externă, noutate și risc pentru a simți plăcere (sistemul dopaminergic).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Prudență / Evitarea Riscului. Subiectul preferă rutina, siguranța și mediile familiare.
Scor Ridicat (70-100): Indică "Sensation Seeking". Subiectul caută adrenalină, sporturi extreme, viteză și se plictisește repede de rutină.

NOTE TEHNICE:
Sursă: NEO-PI-R E5 (Excitement-Seeking).
Corelații: Risc crescut de Dezinhibiție (ID 76) și comportamente periculoase.""",

        # --- ID 18: CĂLDURĂ UMANĂ ---
        18: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează stilul de interacțiune interpersonală: distanță formală versus apropiere afectivă.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Răceală / Rezervare. Subiectul este formal, distant și evită intimitatea emoțională. Poate fi perceput ca inabordabil.
Scor Ridicat (70-100): Indică Căldură / Prietenie. Subiectul este zâmbitor, creează ușor legături și este perceput ca fiind plăcut și accesibil.

NOTE TEHNICE:
Sursă: NEO-PI-R E1 (Warmth).
Corelații: Scorurile foarte mici sunt asociate cu Alexitimia (ID 75) și Atașamentul Evitant.""",

        # --- ID 19: IERTARE ---
        19: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a păstra resentimente și dorința de răzbunare după o ofensă.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Ranchiună. Subiectul "ține scorul", nu uită nedreptățile și poate căuta răzbunare pasivă sau activă.
Scor Ridicat (70-100): Indică Iertare. Subiectul trece repede peste conflicte, nu poartă pică și restabilește încrederea ușor.

NOTE TEHNICE:
Sursă: HEXACO A (Forgiveness).
Corelații: Factorul principal în determinarea riscului "Malicious" (ID 96).""",

        # --- ID 20: BLÂNDEȚE ---
        20: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează empatia și tendința de a judeca oamenii cu clemență versus severitate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Duritate / Criticism. Subiectul aplică regulile strict, este sceptic față de scuze și poate părea insensibil la suferința altora.
Scor Ridicat (70-100): Indică Empatie / Milă. Subiectul este protectiv, simte durerea altora și tinde să fie indulgent.

NOTE TEHNICE:
Sursă: HEXACO A (Gentleness) / NEO-PI-R A6 (Tender-Mindedness).
Corelații: Scorurile foarte mici (<20) sunt un marker pentru trăsături Psihopate (ID 53).""",

        # --- ID 21: FLEXIBILITATE ---
        21: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează disponibilitatea de a face compromisuri și de a accepta ideile altora în detrimentul propriilor idei.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Rigiditate / Încăpățânare. Subiectul insistă ca lucrurile să fie făcute în felul său, este argumentativ și dificil în negocieri.
Scor Ridicat (70-100): Indică Adaptabilitate. Subiectul cooperează ușor, acceptă schimbarea planurilor și caută armonia.

NOTE TEHNICE:
Sursă: HEXACO A (Flexibility).
Corelații: Scorurile foarte mici indică risc de OCPD (ID 105) sau comportament "Uncoachable".""",

        # --- ID 22: ALTRUISM ---
        22: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a ajuta necondiționat, chiar cu un cost personal.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Egoism / Centrare pe sine. Subiectul ajută doar dacă are un beneficiu direct (tranzacțional).
Scor Ridicat (70-100): Indică Generozitate. Subiectul oferă ajutor spontan, face voluntariat și pune nevoile altora pe primul loc.

NOTE TEHNICE:
Sursă: HEXACO (Interstitial) / NEO-PI-R A3.
Corelații: Opusul Machiavelismului.""",

        # --- ID 23: ÎNCREDERE ÎN OAMENI ---
        23: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează convingerea de bază despre natura umană (dacă oamenii sunt buni sau răi).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Cinism / Suspiciune. Subiectul se așteaptă să fie înșelat, caută motive ascunse și este vigilent.
Scor Ridicat (70-100): Indică Încredere / Naivitate. Subiectul acordă prezumția de nevinovăție și crede în bunătatea oamenilor.

NOTE TEHNICE:
Sursă: NEO-PI-R A1 (Trust).
Corelații: Scorurile mici declanșează monstrul "Cinism/Paranoia" (ID 69).""",

        # --- ID 24: ORGANIZARE ---
        24: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nevoia de ordine fizică și mentală, structură și planificare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Dezordine / Haos. Subiectul este dezorganizat, pierde lucruri, nu folosește liste, preferă spontaneitatea.
Scor Ridicat (70-100): Indică Meticulozitate. Subiectul păstrează mediul impecabil, planifică totul în detaliu și urăște dezordinea.

NOTE TEHNICE:
Sursă: HEXACO C (Organization) / NEO-PI-R C2.
Corelații: Scorurile extrem de mari pot indica OCPD (ID 105).""",

        # --- ID 25: HĂRNICIE ---
        25: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a depune efort susținut (Grit pe termen scurt) și de a evita procrastinarea.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Procrastinare / Lene. Subiectul amână sarcinile, evită efortul și renunță ușor la dificultăți.
Scor Ridicat (70-100): Indică Disciplină. Subiectul muncește din greu, termină ce începe și are o etică a muncii puternică.

NOTE TEHNICE:
Sursă: HEXACO C (Diligence) / NEO-PI-R C5 (Self-Discipline).
Corelații: Scorurile mici declanșează riscul de "Social Loafing" (ID 95).""",

        # --- ID 26: PERFECȚIONISM ---
        26: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează atenția la detalii și standardele de calitate auto-impuse.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pragmatism / Neglijență. Subiectul tolerează erorile minore, preferă viteza în locul calității ("Merge și așa").
Scor Ridicat (70-100): Indică Perfecționism. Subiectul verifică obsesiv detaliile, vrea ca totul să fie fără greșeală, uneori sacrificând eficiența.

NOTE TEHNICE:
Sursă: HEXACO C (Perfectionism) / NEO-PI-R C1.
Corelații: Trigger principal pentru Micromanagement (ID 100).""",

        # --- ID 27: PRUDENȚĂ ---
        27: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a delibera și de a anticipa consecințele înainte de a acționa.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Impulsivitate Decizională. Subiectul ia decizii pe loc, bazate pe instinct, fără să analizeze riscurile.
Scor Ridicat (70-100): Indică Precauție. Subiectul gândește mult înainte să vorbească sau să acționeze, analizează scenarii "what if".

NOTE TEHNICE:
Sursă: HEXACO C (Prudence) / NEO-PI-R C6 (Deliberation).
Corelații: Opusul Dezinhibiției (ID 76).""",

        # --- ID 28: DORINȚA DE REALIZARE ---
        28: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nivelul de ambiție, dorința de promovare socială și profesională.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Mulțumire / Lipsă de Ambiție. Subiectul preferă un job liniștit, fără presiune, nu caută să avanseze.
Scor Ridicat (70-100): Indică Ambiție / Carierism. Subiectul este competitiv, vrea să fie cel mai bun, este motivat de succes și recunoaștere.

NOTE TEHNICE:
Sursă: NEO-PI-R C4 (Achievement Striving).
Corelații: Scorurile mari sunt necesare pentru poziții de Leadership, dar pot duce la Burnout.""",

        # --- ID 29: SIMȚUL DATORIEI ---
        29: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează aderența la principii etice, promisiuni și obligații morale.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nonconformism / Iresponsabilitate. Subiectul vede regulile ca pe sugestii, poate încălca promisiunile dacă e convenabil.
Scor Ridicat (70-100): Indică Integritate / Loialitate. Subiectul respectă cuvântul dat cu sfințenie și are un compas moral rigid.

NOTE TEHNICE:
Sursă: NEO-PI-R C3 (Dutifulness).
Corelații: Factor protector împotriva Neglijenței (ID 92) și a Riscului de Fraudă (ID 90).""",

        # --- ID 30: ESTETICĂ ---
        30: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează sensibilitatea la artă, frumos și natură. Măsoară profunzimea experienței estetice.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Utilitarism. Subiectul nu este interesat de artă, decor sau poezie, se concentrează strict pe funcționalitate.
Scor Ridicat (70-100): Indică Sensibilitate Artistică. Subiectul este mișcat profund de muzică, natură sau artă, are gusturi rafinate.

NOTE TEHNICE:
Sursă: NEO-PI-R O2 (Aesthetics) / HEXACO O.
Corelații: Corelează cu creativitatea, dar nu este esențial pentru joburi tehnice."""
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
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 11-30).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()