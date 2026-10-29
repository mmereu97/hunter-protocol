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
        # --- ID 51: MACHIAVELISM ---
        51: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a manipula situațiile sociale și oamenii pentru câștig personal. Măsoară cinismul strategic, duplicitatea și credința că "scopul scuză mijloacele".

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Sinceritate / Naivitate. Subiectul este transparent, refuză jocurile politice și crede în corectitudine absolută.
Scor Ridicat (70-100): Indică Machiavelism. Subiectul este un strateg rece, calculator, dispus să mintă sau să folosească oamenii ca pe piese de șah.

NOTE TEHNICE:
Sursă: Dark Triad (SD3) / HEXACO H (Inversat).
Corelații: Trigger principal pentru "Sabotor" (ID 94) și "Risc Fraudă" (ID 90).""",

        # --- ID 52: NARCISISM ---
        52: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează grandiozitatea, nevoia de admirație și lipsa de empatie. Măsoară sentimentul de îndreptățire (entitlement) și superioritate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Modestie / Umilință. Subiectul nu caută atenție și își cunoaște limitele.
Scor Ridicat (70-100): Indică Narcisism. Subiectul are un ego fragil dar umflat, reacționează agresiv la critică și se consideră "special".

NOTE TEHNICE:
Sursă: Dark Triad (SD3) / HEXACO H (Modesty - Inversat).
Corelații: Trigger pentru "Uncoachable" (ID 93) și comportament toxic de leadership.""",

        # --- ID 53: PSIHOPATIE ---
        53: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează deficitele de empatie, afectul superficial, impulsivitatea și comportamentul antisocial. Măsoară "răceala" emoțională și lipsa remușcărilor.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Empatie / Conștiință. Subiectul simte vinovăție și îi pasă de ceilalți.
Scor Ridicat (70-100): Indică Trăsături Psihopate. Subiectul este insensibil, crud, manipulator și nu învață din pedepse. Risc major de securitate.

NOTE TEHNICE:
Sursă: Dark Triad (SD3) / MMPI.
Corelații: Asociat cu Agresivitatea (ID 89) și Malice (ID 96).""",

        # --- ID 54: PERCEPȚIE EMOȚIONALĂ ---
        54: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a identifica și decoda emoțiile proprii și ale celorlalți (din expresii faciale, ton, limbaj corporal).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică "Orbire Emoțională". Subiectul nu "citește" oamenii, nu simte atmosfera și poate părea insensibil.
Scor Ridicat (70-100): Indică Empatie Cognitivă. Subiectul intuiește imediat starea interlocutorului și detectează minciuna sau disconfortul.

NOTE TEHNICE:
Sursă: TEIQue (Emotion Perception).
Corelații: Scorurile mici sunt un indicator pentru Alexitimie (ID 75) sau spectru autist (ID 104).""",

        # --- ID 55: INTERES ÎNTREPRINZĂTOR ---
        55: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează interesul vocațional pentru activități de persuasiune, vânzări, leadership și management. Măsoară dorința de putere și statut economic.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Preferință pentru Execuție. Subiectul evită rolurile de conducere sau vânzări, preferând suportul tehnic.
Scor Ridicat (70-100): Indică Spirit Antreprenorial. Subiectul este competitiv, ambițios, bun negociator și orientat spre profit.

NOTE TEHNICE:
Sursă: Holland Codes (RIASEC - Enterprising).
Corelații: Corelează cu Motivația Financiară (ID 86).""",

        # --- ID 56: MANAGEMENT EMOȚIONAL ---
        56: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a regla propriile emoții, de a gestiona stresul și de a controla impulsurile în situații tensionate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Reactivitate / Labilitate. Subiectul este copleșit ușor de emoții, izbucnește sau se blochează sub presiune.
Scor Ridicat (70-100): Indică Autocontrol / Stoicism. Subiectul rămâne lucid în criză și își poate calma stările negative.

NOTE TEHNICE:
Sursă: TEIQue (Emotion Regulation).
Corelații: Factor protector împotriva Burnout-ului (ID 77).""",

        # --- ID 57: INFLUENȚĂ EMOȚIONALĂ ---
        57: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a influența stările emoționale și deciziile altora. Măsoară carisma, persuasiunea și impactul social.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pasivitate Socială. Subiectul nu se impune și are dificultăți în a convinge sau a motiva pe alții.
Scor Ridicat (70-100): Indică Leadership Emoțional. Subiectul este un negociator natural și poate schimba atmosfera într-un grup.

NOTE TEHNICE:
Sursă: TEIQue (Emotion Management / Influence).
Corelații: Esențial pentru roluri de management.""",

        # --- ID 58: SOMATIZARE ---
        58: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a exprima distresul psihologic prin simptome fizice (dureri, oboseală, probleme digestive) fără cauză medicală.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Reziliență Somatică. Corpul subiectului nu reacționează dramatic la stres.
Scor Ridicat (70-100): Indică Risc de Ipohondrie / Somatizare. Subiectul acuză frecvent stări de rău fizic cauzate de stres, afectând prezența la muncă.

NOTE TEHNICE:
Sursă: MMPI-2-RF (RC1 - Somatic Complaints).
Corelații: Corelează puternic cu Anxietatea (ID 6) și Neurotismul.""",

        # --- ID 59: GÂNDIRE BIZARĂ ---
        59: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează prezența gândirii neobișnuite, a credințelor excentrice, paranoia sau experiențe perceptuale aberante (halucinații, iluzii).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Gândire Rațională / Ancorată.
Scor Ridicat (70-100): Indică Risc Psihotic / Schizotipie. Subiectul poate avea credințe magice, teorii ale conspirației sau detașare de realitate.

NOTE TEHNICE:
Sursă: MMPI-2-RF (RC8 - Aberrant Experiences) / DSM-5.
Corelații: Trigger pentru Disociere (ID 85) și inaptitudine pentru roluri de siguranță.""",

        # --- ID 60: COMPORTAMENT ANTISOCIAL ---
        60: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează istoricul de conflicte cu autoritatea, încălcarea regulilor, impulsivitate criminală și respingerea normelor sociale.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Conformism / Cetățean Model. Subiectul respectă legea și autoritatea.
Scor Ridicat (70-100): Indică Tendințe Antisociale. Istoric de probleme disciplinare, sfidare, risc de acte ilegale.

NOTE TEHNICE:
Sursă: MMPI-2-RF (RC4 - Antisocial Behavior).
Corelații: Diferit de Psihopatie (care e trăsătură), acesta măsoară comportamentul istoric.""",

        # --- ID 61: INTERES INVESTIGATIV ---
        61: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează interesul pentru activități intelectuale, științifice, analiză de date și rezolvarea problemelor abstracte.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pragmatism Intuitiv. Subiectul preferă acțiunea imediată, nu teoria.
Scor Ridicat (70-100): Indică Minte Analitică. Subiectul iubește cercetarea, logica și aprofundarea informațiilor.

NOTE TEHNICE:
Sursă: Holland Codes (RIASEC - Investigative).
Corelații: Corelează cu IQ-ul (ID 40) și Curiozitatea (ID 31).""",

        # --- ID 62: INTERES ARTISTIC ---
        62: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează atracția către creativitate, auto-exprimare, design, scris și medii de lucru nestructurate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Convenționalism. Subiectul preferă regulile clare și structura.
Scor Ridicat (70-100): Indică Creativitate. Subiectul are nevoie de libertate de exprimare și inovație.

NOTE TEHNICE:
Sursă: Holland Codes (RIASEC - Artistic).
Corelații: Corelează cu Estetica (ID 30) și Neconvenționalitatea (ID 33).""",

        # --- ID 63: INTERES SOCIAL (RIASEC) ---
        63: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează vocația pentru lucrul cu oamenii: a ajuta, a vindeca, a preda sau a consilia.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Orientare spre Obiecte/Date. Subiectul preferă să lucreze singur sau cu mașinării.
Scor Ridicat (70-100): Indică Vocație Umanistă. Subiectul este motivat de impactul pozitiv asupra altora.

NOTE TEHNICE:
Sursă: Holland Codes (RIASEC - Social).
Corelații: Corelează cu Altruismul (ID 22) și Căldura Umană (ID 18).""",

        # --- ID 64: INTERES CONVENȚIONAL ---
        64: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru organizare, manipularea datelor, contabilitate, arhivare și respectarea procedurilor stricte.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nevoie de Libertate. Subiectul urăște birocrația și detaliile administrative.
Scor Ridicat (70-100): Indică Rigoare Administrativă. Subiectul excelează în medii structurate, cu reguli clare.

NOTE TEHNICE:
Sursă: Holland Codes (RIASEC - Conventional).
Corelații: Corelează cu Organizarea (ID 24) și Respectarea Regulilor (ID 43).""",

        # --- ID 65: LOCUS OF CONTROL ---
        65: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează atribuirea cauzalității evenimentelor din viață. Cine este responsabil: Eu (Intern) sau Soarta/Alții (Extern)?

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Locus Extern / Fatalism. Subiectul crede că norocul sau sistemul îi dictează viața. Risc de pasivitate și victimizare.
Scor Ridicat (70-100): Indică Locus Intern / Agentic. Subiectul își asumă responsabilitatea pentru succese și eșecuri. Proactiv.

NOTE TEHNICE:
Sursă: Rotter's Locus of Control.
Corelații: Scorurile mici declanșează Monstrul "Victimizare" (ID 98).""",

        # --- ID 66: AUTO-REGLARE (CONTROL) ---
        66: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a controla impulsurile și de a menține disciplina în fața tentațiilor. Similar cu Hărnicia, dar focusat pe inhibiție.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Impulsivitate Hedonistă. Subiectul cedează ușor plăcerilor de moment.
Scor Ridicat (70-100): Indică Disciplină de Fier. Subiectul poate amâna gratificarea pentru obiective pe termen lung.

NOTE TEHNICE:
Sursă: TEIQue (Self-Control) / Big Five.
Corelații: Opusul Impulsivității (ID 11).""",

        # --- ID 67: EXPRIMARE EMOȚIONALĂ ---
        67: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează cât de deschis își comunică subiectul stările interioare. Măsoară vizibilitatea emoțiilor.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Introversie Emoțională / Poker Face. Subiectul este greu de citit, pare rece sau misterios.
Scor Ridicat (70-100): Indică Expresivitate. Subiectul este o "carte deschisă", gesticulează și verbalizează ce simte.

NOTE TEHNICE:
Sursă: TEIQue (Emotional Expression).
Corelații: Diferit de a simți (ID 38), aici e vorba de a arăta.""",

        # --- ID 68: DEMORALIZARE ---
        68: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează sentimentul cronic de neputință, lipsă de speranță și disperare. Este componenta afectivă a depresiei clinice.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Speranță și Moral Ridicat.
Scor Ridicat (70-100): Indică Demoralizare Clinică. Subiectul se simte învins de viață, copleșit și incapabil să mai lupte.

NOTE TEHNICE:
Sursă: MMPI-2-RF (RCd - Demoralization).
Corelații: Indicator major de risc suicidar (dacă e extrem) sau incapacitate de muncă.""",

        # --- ID 69: CINISM (MIZANTROPIE) ---
        69: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează neîncrederea generalizată în motivele celorlalți. Credința că oamenii sunt egoiști, falși și periculoși.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Idealism / Încredere.
Scor Ridicat (70-100): Indică Cinism Mizantropic. Subiectul este ostil, suspicios și disprețuitor față de umanitate. Distruge coeziunea echipei.

NOTE TEHNICE:
Sursă: MMPI-2-RF (RC3 - Cynicism).
Corelații: Formă extremă a lipsei de încredere (ID 23).""",

        # --- ID 70: ATAȘAMENT ANXIOS ---
        70: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nesiguranța în relații, teama de abandon și nevoia excesivă de reasigurare și validare din partea celorlalți.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Atașament Sigur. Subiectul este încrezător în relații.
Scor Ridicat (70-100): Indică Anxietate Relațională. Subiectul devine "clingy", posesiv, interpretează greșit tăcerea și necesită atenție constantă.

NOTE TEHNICE:
Sursă: ECR (Experiences in Close Relationships).
Corelații: Corelează cu Dependența Emoțională (ID 7) și Borderline (ID 106)."""
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
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 51-70).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()