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
        # --- ID 31: CURIOZITATE INTELECTUALĂ ---
        31: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează deschiderea către idei noi, teorii abstracte și dorința de cunoaștere de dragul cunoașterii. Măsoară "foamea intelectuală".

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Pragmatism / Conservatorism Intelectual. Subiectul se concentrează strict pe informații utile, imediate și concrete. Evită dezbaterile filozofice sau teoretice.
Scor Ridicat (70-100): Indică Curiozitate Intelectuală. Subiectul citește mult, explorează subiecte diverse și se bucură de discuții abstracte și complexe.

NOTE TEHNICE:
Sursă: NEO-PI-R O5 (Ideas) / HEXACO O.
Corelații: Corelează pozitiv cu IQ-ul (ID 40) și Deschidere la Schimbare (ID 50).""",

        # --- ID 32: FANTEZIE ---
        32: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează vivacitatea imaginației și bogăția vieții interioare.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Realism. Subiectul este ancorat în "aici și acum", preferă faptele concrete și rareori visează cu ochii deschiși.
Scor Ridicat (70-100): Indică Imaginație Activă. Subiectul are o lume interioară complexă, folosește fantezia ca refugiu sau sursă de creativitate.

NOTE TEHNICE:
Sursă: NEO-PI-R O1 (Fantasy) / HEXACO O.
Corelații: Scorurile foarte mari pot indica risc de Disociere (ID 85) sau lipsă de focus (ID 46).""",

        # --- ID 33: VALORI / NECONVENȚIONALITATE ---
        33: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează disponibilitatea de a reexamina valorile sociale, politice și religioase. Măsoară dogmatismul versus liberalismul.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Dogmatism / Conformism. Subiectul acceptă autoritatea și tradiția fără a le pune la îndoială.
Scor Ridicat (70-100): Indică Liberalism / Nonconformism. Subiectul este deschis către valori atipice, contestă normele și este tolerant față de diversitate.

NOTE TEHNICE:
Sursă: NEO-PI-R O6 (Values).
Corelații: Opusul Tradiționalismului (ID 87).""",

        # --- ID 34: DESCHIDERE LA ACȚIUNI ---
        34: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru noutate și varietate în activitățile zilnice, opusă preferinței pentru rutină și familiaritate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nevoia de Rutină. Subiectul se simte confortabil în mediul cunoscut, merge în aceleași locuri și evită schimbările neplanificate.
Scor Ridicat (70-100): Indică Nevoia de Varietate. Subiectul se plictisește repede, caută mereu experiențe noi, mâncăruri noi și locuri noi.

NOTE TEHNICE:
Sursă: NEO-PI-R O4 (Actions).
Corelații: Risc crescut de Flight Risk (ID 97) dacă jobul este repetitiv.""",

        # --- ID 35: EMOȚII POZITIVE ---
        35: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a experimenta stări de bucurie, entuziasm, optimism și vitalitate.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Melancolie / Seriozitate. Subiectul este rareori exuberant, poate părea trist sau rezervat. (Nu înseamnă neapărat depresie clinică, ci lipsa entuziasmului).
Scor Ridicat (70-100): Indică Optimism / Exuberanță. Subiectul râde ușor, este plin de viață și radiază energie pozitivă.

NOTE TEHNICE:
Sursă: NEO-PI-R E6 (Positive Emotions).
Corelații: Scorurile extrem de scăzute sunt un factor de risc pentru Anhedonie (ID 74).""",

        # --- ID 36: VULNERABILITATE LA STRES ---
        36: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de a face față situațiilor de criză și presiune. Nu măsoară grija cronică (Anxietatea), ci reacția acută la stresori (Panic vs Calm).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Reziliență. Subiectul rămâne calm și funcțional sub presiune, "nervi de oțel".
Scor Ridicat (70-100): Indică Fragilitate. Subiectul devine copleșit, confuz sau panicat în situații de urgență și are nevoie de suport.

NOTE TEHNICE:
Sursă: NEO-PI-R N6 (Vulnerability).
Corelații: Critic pentru joburi high-stress (Poliție, Medicină). Trigger pentru Burnout (ID 77).""",

        # --- ID 37: OSTILITATE (FURIE) ---
        37: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a experimenta furia și stări conexe (frustrare, amărăciune). Măsoară disponibilitatea spre reacții agresive.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Fire Pașnică. Subiectul se înfurie foarte greu.
Scor Ridicat (70-100): Indică Temperament Vulcanic. Subiectul are un "fitil scurt", se irită rapid și poate avea izbucniri de furie.

NOTE TEHNICE:
Sursă: NEO-PI-R N2 (Angry Hostility).
Corelații: Trigger principal pentru Agresivitate (ID 89) și risc de violență.""",

        # --- ID 38: RECEPTIVITATE EMOȚIONALĂ ---
        38: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează importanța acordată propriilor stări emoționale. Măsoară gradul în care emoțiile sunt valorizate ca sursă de informație și experiență de viață.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Insensibilitate la Emoții. Subiectul ignoră sentimentele (ale sale și ale altora), punând accent strict pe fapte.
Scor Ridicat (70-100): Indică Profunzime a Trăirii. Subiectul simte emoțiile intens și nuanțat.

NOTE TEHNICE:
Sursă: NEO-PI-R O3 (Feelings).
Corelații: Scorurile mici corelează cu Alexitimia (ID 75).""",

        # --- ID 39: CONCILIERE ---
        39: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează reacția la conflictul interpersonal: tendința de a ceda în fața altora versus tendința de a fi combativ.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Competitivitate / Agresivitate. Subiectul vrea să câștige argumentele, este încăpățânat și poate fi intimidant.
Scor Ridicat (70-100): Indică Supunere / Conciliere. Subiectul evită conflictul cu orice preț, cedează pentru a păstra armonia.

NOTE TEHNICE:
Sursă: NEO-PI-R A4 (Compliance).
Corelații: Scorurile foarte mari indică risc de "Yes-Man" (ID 102).""",

        # --- ID 40: RAȚIONAMENT (IQ) ---
        40: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează capacitatea de gândire abstractă, viteza de învățare și rezolvarea problemelor (Metacogniție).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Gândire Concretă. Subiectul preferă instrucțiuni pas-cu-pas, are dificultăți cu conceptele teoretice și învață prin repetiție.
Scor Ridicat (70-100): Indică Gândire Abstractă. Subiectul învață rapid, vede tipare complexe și rezolvă probleme noi intuitiv.

NOTE TEHNICE:
Sursă: 16PF Factor B (Reasoning).
Corelații: Critic pentru roluri complexe/analitice.""",

        # --- ID 41: DIPLOMAȚIE / SECRETOMANIE ---
        41: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează gradul de deschidere și transparență în comunicare versus calcul social și reținere ("shrewdness").

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Naivitate / Transparență. Subiectul spune tot ce gândește, este o "carte deschisă" și poate fi lipsit de tact.
Scor Ridicat (70-100): Indică Diplomație / Secretomanie. Subiectul își calculează cuvintele, este rezervat în privința informațiilor personale și gestionează atent impresiile.

NOTE TEHNICE:
Sursă: 16PF Factor N (Privateness).
Corelații: Scorurile mari corelează cu Machiavelismul (ID 51).""",

        # --- ID 42: DOMINANȚĂ AGRESIVĂ ---
        42: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința de a exercita control asupra altora și de a fi autoritar.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Submisivitate / Umilință. Subiectul evită să conducă, se lasă influențat.
Scor Ridicat (70-100): Indică Dominanță. Subiectul este asertiv, competitiv și tinde să preia controlul în grupuri. În exces, devine agresiv.

NOTE TEHNICE:
Sursă: 16PF Factor E (Dominance).
Corelații: Trigger pentru "Uncoachable" (ID 93).""",

        # --- ID 43: RESPECTARE REGULI ---
        43: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează atitudinea față de normele sociale, autoritate și reguli impuse extern (Superego Strength).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Nonconformism / Oportunism. Subiectul ignoră regulile dacă îl încurcă, disprețuiește birocrația.
Scor Ridicat (70-100): Indică Conformism / Disciplină. Subiectul respectă litera legii și regulamentele interne cu strictețe.

NOTE TEHNICE:
Sursă: 16PF Factor G (Rule-Consciousness).
Corelații: Scorurile mici sunt risc major pentru Comportament Antisocial (ID 60).""",

        # --- ID 44: SENSIBILITATE ARTISTICĂ ---
        44: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează dimensiunea Tough-minded vs. Tender-minded. Sensibilitatea față de estetică și intuiție versus pragmatism dur.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Duritate / Realism ("Tough-Minded"). Subiectul se bazează pe fapte, nu pe sentimente, și poate părea insensibil.
Scor Ridicat (70-100): Indică Rafinament / Sensibilitate ("Tender-Minded"). Subiectul este intuitiv, estetic și ușor de impresionat.

NOTE TEHNICE:
Sursă: 16PF Factor I (Sensitivity).
Corelații: Scorurile mari corelează cu interesele Artistice (ID 62).""",

        # --- ID 45: VIGILENȚĂ ---
        45: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nivelul de suspiciune, neîncredere și tendința de a atribui motivații ascunse celorlalți.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Încredere / Relaxare. Subiectul se simte în siguranță și acceptă oamenii așa cum sunt.
Scor Ridicat (70-100): Indică Suspiciune / Paranoia. Subiectul este mereu "în gardă", se așteaptă să fie înșelat și este gelos.

NOTE TEHNICE:
Sursă: 16PF Factor L (Vigilance).
Corelații: Trigger principal pentru Cinism (ID 69).""",

        # --- ID 46: VISARE (ABSTRACTEDNESS) ---
        46: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează orientarea atenției: spre lumea exterioară (practic) sau spre lumea interioară (idei/imaginație).

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Ancorare în Realitate. Subiectul este atent la detalii practice, observator și "cu picioarele pe pământ".
Scor Ridicat (70-100): Indică Absorbire Mentală / Visare. Subiectul este "cu capul în nori", uită detalii practice, este imaginativ dar distrat.

NOTE TEHNICE:
Sursă: 16PF Factor M (Abstractedness).
Corelații: Risc de neglijență practică sau disociere ușoară.""",

        # --- ID 47: ÎNGRIJORARE (APPREHENSION) ---
        47: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nivelul de auto-învinovățire, insecuritate și teamă difuză.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Siguranță de Sine. Subiectul este senin, încrezător și nu are remușcări.
Scor Ridicat (70-100): Indică Aprehensiune / Vinovăție. Subiectul se simte inadecvat, își face griji excesive și este sensibil la critică.

NOTE TEHNICE:
Sursă: 16PF Factor O (Apprehension).
Corelații: Asociat cu Sindromul Impostorului (ID 101).""",

        # --- ID 48: AUTO-SUFICIENȚĂ ---
        48: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează preferința pentru munca individuală și luarea deciziilor fără consultare, versus dependența de grup.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Dependență de Grup. Subiectul preferă munca în echipă, caută consensul și validarea socială ("Group-oriented").
Scor Ridicat (70-100): Indică Individualism / Auto-suficiență. Subiectul preferă să lucreze singur, are încredere în propriile decizii și poate părea izolat.

NOTE TEHNICE:
Sursă: 16PF Factor Q2 (Self-Reliance).
Corelații: Scorurile mari sunt bune pentru experți tehnici, dar riscante pentru munca în echipă.""",

        # --- ID 49: TENSIUNE NERVOASĂ ---
        49: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează nivelul de energie nervoasă liber-flotantă, nerăbdarea și frustrarea somatică.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Relaxare. Subiectul este calm, răbdător și flegmatic.
Scor Ridicat (70-100): Indică Tensiune Înaltă. Subiectul este agitat, nerăbdător, "stă pe ghimpi" și are dificultăți de relaxare.

NOTE TEHNICE:
Sursă: 16PF Factor Q4 (Tension).
Corelații: Risc pentru sănătate (stres cronic) și impulsivitate.""",

        # --- ID 50: DESCHIDERE LA SCHIMBARE ---
        50: """DEFINIȚIE OPERAȚIONALĂ:
Evaluează atitudinea față de noutate, reformă și experimentare versus conservatorism.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică Conservatorism. Subiectul respectă tradiția, metodele verificate și rezistă la schimbare.
Scor Ridicat (70-100): Indică Radicalism. Subiectul vrea să schimbe status quo-ul, experimentează metode noi și critică tradiția.

NOTE TEHNICE:
Sursă: 16PF Factor Q1 (Openness to Change).
Corelații: Scorurile mici declanșează riscul "Uncoachable" (ID 93) în medii dinamice."""
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
        print(f"✅ SUCCES: Au fost actualizate descrierile pentru {count} axe (ID 31-50).")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_batch_descriptions()