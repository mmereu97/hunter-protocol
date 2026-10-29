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
        # --- ID 71: ATAȘAMENT EVITANT ---
        71: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează disconfortul față de intimitatea emoțională și tendința de a menține distanța în relații. Măsoară preferința pentru auto-suficiență extremă ca mecanism de apărare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Atașament Sigur / Conectat. Subiectul se simte confortabil să depindă de alții și să fie sprijin pentru ei.
Scor Ridicat (70-100): Indică Atașament Evitant ("Dismissive"). Subiectul percepe apropierea ca pe o amenințare la adresa independenței, își reprimă nevoile emoționale și poate părea rece sau distant.

NOTE TEHNICE:
Sursă: ECR (Experiences in Close Relationships).
Corelații: Asociat cu Alexitimia (ID 75) și trăsături Schizoide.""",

        # --- ID 72: GRIT (PERSEVERENȚĂ) ---
        72: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează combinația dintre pasiune și perseverență pe termen lung. Măsoară capacitatea de a menține efortul și interesul pentru obiective îndepărtate, în ciuda eșecurilor sau platourilor.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Inconstanță. Subiectul renunță ușor, își schimbă des interesele și caută gratificare imediată.
Scor Ridicat (70-100): Indică Tenacitate (Grit). Subiectul este neobosit, rezilient și orientat spre măiestrie pe termen lung.

NOTE TEHNICE:
Sursă: Angela Duckworth Grit Scale.
Corelații: Predictor mai bun pentru succes decât IQ-ul în anumite domenii.""",

        # --- ID 73: RECUNOȘTINȚĂ ---
        73: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a observa și aprecia aspectele pozitive ale vieții. Este un indicator cheie pentru starea de bine psihologică și satisfacția vieții.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nemulțumire / Îndreptățire (Entitlement). Subiectul se concentrează pe lipsuri, se compară negativ cu alții și poate fi invidios.
Scor Ridicat (70-100): Indică Apreciere. Subiectul găsește motive de bucurie în lucruri mărunte și este rezilient la stres.

NOTE TEHNICE:
Sursă: GQ-6 (Gratitude Questionnaire).
Corelații: Corelează negativ cu Narcisismul (ID 52) și Victimizarea (ID 98).""",

        # --- ID 74: ANHEDONIE ---
        74: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează incapacitatea de a simți plăcere din activități care în mod normal sunt agreabile (mâncare, hobby-uri, interacțiuni sociale). Este un simptom central al depresiei majore.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Vitalitate / Hedonism. Subiectul se bucură de viață.
Scor Ridicat (70-100): Indică "Gol Interior". Subiectul este aplatizat emoțional, nu simte nici tristețe, nici bucurie, ci o indiferență dureroasă.

NOTE TEHNICE:
Sursă: DSM-5 / SHAPS (Snaith-Hamilton Pleasure Scale).
Corelații: Marker clinic grav. Necesită atenție dacă scorul e > 70.""",

        # --- ID 75: ALEXITIMIE ---
        75: """DEFINIȚIE OPERAȚIONALĂ:
"Orbirea emoțională". Evaluează dificultatea de a identifica, descrie și procesa propriile emoții. Subiecții confundă adesea emoțiile cu senzațiile fizice.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Inteligență Emoțională Intrapersonală. Subiectul își înțelege nuanțele afective.
Scor Ridicat (70-100): Indică Alexitimie. Subiectul are o gândire strict concretă, lipsită de fantezie, și nu poate verbaliza ce simte.

NOTE TEHNICE:
Sursă: TAS-20 (Toronto Alexithymia Scale).
Corelații: Risc crescut de Somatizare (ID 58) și relații interpersonale sărace.""",

        # --- ID 76: DEZINHIBIȚIE ---
        76: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează lipsa controlului inhibitor asupra impulsurilor. Măsoară tendința spre gratificare imediată, comportament iresponsabil și asumarea riscurilor fără a considera consecințele viitoare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Prudență / Planificare.
Scor Ridicat (70-100): Indică Impulsivitate Patologică. Risc de adicții, cheltuieli compulsive, condus imprudent sau promiscuitate.

NOTE TEHNICE:
Sursă: DSM-5 PID-5 (Disinhibition).
Corelații: Opusul Conștiinciozității (ID 7 + ID 25).""",

        # --- ID 77: BURNOUT ---
        77: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează sindromul de epuizare profesională caracterizat prin: epuizare emoțională, depersonalizare (cinism) și scăderea realizării personale.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Engagement / Energie.
Scor Ridicat (70-100): Indică Colaps Profesional. Subiectul este "stors", detestă locul de muncă și funcționează pe avarie.

NOTE TEHNICE:
Sursă: MBI (Maslach Burnout Inventory).
Corelații: Corelează cu Vulnerabilitatea la Stres (ID 36) și Cinismul (ID 69).""",

        # --- ID 78: DEPERSONALIZARE ---
        78: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează experiențele disociative în care subiectul se simte detașat de propriul corp sau de procesele mentale (ca un observator extern).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Ancorare (Grounding).
Scor Ridicat (70-100): Indică Disociere Clinică. Senzația de irealitate, automatism, "robotizare". Poate fi un mecanism de apărare la traume sau stres extrem.

NOTE TEHNICE:
Sursă: CDS (Cambridge Depersonalization Scale).
Corelații: Apare des în Burnout avansat sau PTSD.""",

        # --- ID 79: CRONOTIP ---
        79: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează ritmul circadian natural al individului. Nu este o trăsătură de personalitate, ci o preferință biologică de activitate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Tip Matinal ("Ciocârlie"). Performanță maximă dimineața, dificultăți seara.
Scor Ridicat (70-100): Indică Tip Vespertin ("Bufniță"). Dificultăți majore la trezire, energie maximă seara/noaptea.

NOTE TEHNICE:
Sursă: MEQ (Morningness-Eveningness Questionnaire).
Corelații: Important pentru planificarea turelor de lucru.""",

        # --- ID 80: SENSIBILITATE SENZORIALĂ (HSP) ---
        80: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează profunzimea procesării senzoriale. Măsoară reactivitatea la stimuli externi (zgomot, lumină, texturi) și interni.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Reziliență Senzorială ("Tanc"). Nu este deranjat de medii haotice.
Scor Ridicat (70-100): Indică Hipersensibilitate (HSP). Subiectul se suprasolicită ușor în medii aglomerate, observă detalii subtile, are nevoie de retragere.

NOTE TEHNICE:
Sursă: Elaine Aron HSP Scale.
Corelații: Corelează cu Deschiderea (Estetică) și Nevrotismul.""",

        # --- ID 81: LIBIDO ---
        81: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nivelul general al impulsului sexual și importanța acestuia în viața subiectului.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Drive Scăzut / Asexualitate.
Scor Ridicat (70-100): Indică Drive Înalt / Pasiune.

NOTE TEHNICE:
Sursă: Inventare biologice/psihologice generale.
Corelații: În combinație cu Impulsivitate mare (ID 11) și Conștiinciozitate mică, poate indica risc de Hărțuire (ID 91).""",

        # --- ID 82: STIL DE ÎNVĂȚARE ---
        82: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru modul de asimilare a informațiilor noi: abstractizare versus experimentare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Stil Teoretic / Reflexiv. Învață citind, analizând concepte.
Scor Ridicat (70-100): Indică Stil Practic / Activ. Învață făcând ("hands-on"), prin încercare și eroare.

NOTE TEHNICE:
Sursă: Kolb Learning Style Inventory.
Corelații: Relevant pentru training și onboarding.""",

        # --- ID 83: TOLERANȚĂ LA RISC ---
        83: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează disponibilitatea de a lua decizii în condiții de incertitudine, în special financiare sau strategice.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Aversiune la Risc. Preferă siguranța, câștigurile mici dar garantate.
Scor Ridicat (70-100): Indică Căutarea Riscului (Risk Seeking). Dispus să parieze totul pentru un câștig mare.

NOTE TEHNICE:
Sursă: DOSPERT (Domain-Specific Risk-Taking).
Corelații: Critic pentru roluri de investiții, antreprenoriat sau trading.""",

        # --- ID 84: SADISM COTIDIAN ---
        84: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează plăcerea derivată din suferința fizică sau psihologică a altora. Face parte din "Tetrada Întunecată".

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Empatie / Aversiune față de cruzime.
Scor Ridicat (70-100): Indică Sadism. Subiectul se amuză de durerea altora, trollează, umilește intenționat sau manifestă cruzime.

NOTE TEHNICE:
Sursă: CAST (Comprehensive Assessment of Sadistic Tendencies).
Corelații: Trigger principal pentru comportamentul "Malicious" (ID 96).""",

        # --- ID 85: DISOCIERE ---
        85: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de deconectare mentală de la realitate. Include visarea excesivă, absorbția în fantezie și episoadele de "pilot automat".

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Prezență / Mindfulness.
Scor Ridicat (70-100): Indică Disociere / Absorbție. Subiectul "pleacă" mental, pierde noțiunea timpului, poate avea dificultăți de concentrare pe sarcini plictisitoare.

NOTE TEHNICE:
Sursă: DES-II (Dissociative Experiences Scale).
Corelații: Asociat cu Fantezia (ID 32) și Visarea (ID 46).""",

        # --- ID 86: MOTIVAȚIE FINANCIARĂ ---
        86: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează importanța banilor și a acumulării materiale ca factor motivator principal în carieră și viață.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Motivație Intrinsecă / Misionară. Subiectul caută sens, impact sau plăcere, banii fiind secundari.
Scor Ridicat (70-100): Indică Motivație Extrinsecă / Mercenară. Subiectul este motivat strict de câștigul financiar și statut.

NOTE TEHNICE:
Sursă: Schwartz Values (Power/Achievement).
Corelații: Cel mai puternic predictor pentru "Flight Risk" (ID 97).""",

        # --- ID 87: TRADIȚIONALISM ---
        87: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează respectul pentru obiceiuri, religie, familie și structurile sociale consacrate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Liberalism / Progresism. Subiectul provoacă status quo-ul și valorile vechi.
Scor Ridicat (70-100): Indică Conservatorism. Subiectul crede că "vechile metode sunt cele mai bune", respectă ierarhia și normele.

NOTE TEHNICE:
Sursă: Schwartz Values (Tradition/Conformity).
Corelații: Opusul Deschiderii la Schimbare (ID 50).""",

        # --- ID 88: ROMANTISM ---
        88: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează viziunea asupra relațiilor: idealismul romantic versus pragmatismul relațional.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pragmatism / Cinism. Relațiile sunt parteneriate funcționale.
Scor Ridicat (70-100): Indică Idealism / Visare. Credința în suflete pereche, destin și gesturi grandioase.

NOTE TEHNICE:
Sursă: Romantic Beliefs Scale.
Corelații: Relevant pentru compatibilitatea de cuplu (Dating).""",

        # --- ID 89: AGRESIVITATE ---
        89: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează predispoziția către comportamente ostile, violență verbală sau fizică și furie externalizată.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pacifism / Control.
Scor Ridicat (70-100): Indică Risc de Violență. Subiectul are un istoric de conflicte, amenințări sau acte agresive.

NOTE TEHNICE:
Sursă: CWB-C (Counterproductive Work Behavior - Abuse).
Corelații: Se activează când Ostilitatea (ID 37) este mare și Răbdarea (ID 12) este mică.""",

        # --- ID 90: INTEGRITATE (RISC FRAUDĂ) ---
        90: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează riscul de comportament neetic la locul de muncă: furt, delapidare, mită sau încălcarea regulilor pentru câștig personal.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Integritate Înaltă.
Scor Ridicat (70-100): Indică Risc de Fraudă. Subiectul raționalizează comportamentul neetic ("toți o fac", "mi se cuvine").

NOTE TEHNICE:
Sursă: PSI (Personnel Selection Inventory).
Corelații: Se activează când Corectitudinea (ID 2) este mică și Machiavelismul (ID 51) sau Lăcomia (ID 3 - inversată) sunt mari."""
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
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 71-90).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()