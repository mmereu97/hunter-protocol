import sqlite3
import os
import sys

# Hack import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import log, log_error

def populate_axes():
    db_path = Config.DB_NAME
    if not os.path.exists(db_path):
        log_error(f"Baza de date {db_path} nu există! Rulează init_db.py întâi.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    log("sys", "RESETARE & RE-ALINIERE AXE (Corecție ID-uri)...")

    # 1. CURĂȚĂM TABELA VECHE PENTRU A EVITA DUPLICATE SAU CONFUZII
    cursor.execute("DELETE FROM axes")
    
    # ==============================================================================
    # LISTA MASTER CORECTATĂ (ALINIATĂ CU NOTIȚELE TALE)
    # ==============================================================================
    axes_data = [
        # --- GRUPA 1: HEXACO H & E ---
        (1, "Sinceritate/Franchețe", "Strategic / Machiavelic", "Onest / Integru", "Core", "OCEAN A, HEXACO E, NEO-PI-R A2"),
        (2, "Corectitudine", "Oportunist / Fraudulos", "Principial / Corect", "Core", "HEXACO E"),
        (3, "Evitarea Lăcomiei", "Materialist / Lux", "Modest / Neinteresat", "Core", "HEXACO E"),
        (4, "Modestie", "Arogant / Superior", "Umil / Egal", "Core", "OCEAN A, HEXACO E, NEO-PI-R A5"),
        (5, "Frică Fizică", "Curajos / Temerar", "Prudent / Temător", "Core", "HEXACO E"),
        (6, "Anxietate", "Calm / Relaxat", "Îngrijorat / Tensionat", "Core", "OCEAN A, HEXACO E, NEO-PI-R N1"),
        (7, "Dependență Emoțională", "Independent / Solo", "Nevoie de Suport / Tribal", "Core", "HEXACO E"),
        (8, "Sentimentalism", "Rece / Rațional", "Empatic / Sentimental", "Core", "HEXACO E"),

        # --- GRUPA 2: NEVROTISM & EXTRAVERSIE (Mix OCEAN/HEXACO) ---
        (9, "Depresie", "Optimist / Vesel", "Trist / Descurajat", "Core", "OCEAN N, NEO-PI-R N3"), 
        (10, "Timiditate Socială (Jena)", "Tupeist / Direct", "Timid / Rușinos", "Core", "OCEAN N, NEO-PI-R N4"),
        (11, "Impulsivitate", "Controlat / Deliberat", "Impulsiv / Reactiv", "Core", "OCEAN N, NEO-PI-R N5"),
        (12, "Răbdare", "Irascibil / Fitil Scurt", "Răbdător / Stoic", "Core", "HEXACO A"), 
        (13, "Stimă de Sine Socială", "Nesigur", "Încrezător / Popular", "Core", "HEXACO X"), # CORECTAT cf. notițelor
        (14, "Asertivitate / Dominanță", "Submisiv / Pasiv", "Dominant / Lider", "Core", "OCEAN E, HEXACO X, NEO-PI-R E3, 16PF H"),
        (15, "Sociabilitate", "Pustnic / Introvertit", "Gregar / Extrovertit", "Core", "OCEAN E, HEXACO X, NEO-PI-R E2"),
        (16, "Vivacitate / Activitate", "Lent / Pasiv", "Energic / Dinamic", "Core", "OCEAN E, HEXACO X, NEO-PI-R E4, 16PF F"),
        (17, "Căutarea Senzațiilor", "Prudent / Casnic", "Aventurier / Adrenalină", "Core", "OCEAN E NEO-PI-R E5"),
        (18, "Căldură Umană", "Distant / Rece", "Cald / Prietenos", "Core", "OCEAN E1, 16PF A"),

        # --- GRUPA 3: AGREABILITATE ---
        (19, "Iertare", "Răzbunător / Ranchiunos", "Iertător / Împăciuitor", "Core", "HEXACO A"),
        (20, "Blândețe", "Dur / Critic", "Blând / Binevoitor", "Core", "OCEAN A, HEXACO A, NEO-PI-R A6"),
        (21, "Flexibilitate", "Încăpățânat / Rigid", "Flexibil / Adaptabil", "Core", "HEXACO A"),
        (22, "Altruism", "Egoist", "Altruist / Generos", "Core", "OCEAN A, HEXACO SPECIAL, NEO-PI-R A3"),
        (23, "Încredere în Oameni", "Cinic / Suspicios", "Încrezător / Naiv", "Core", "OCEAN A, NEO-PI-R A1"),

        # --- GRUPA 4: CONȘTIINCIOZITATE (Muncă) ---
        (24, "Organizare / Ordine", "Haotic", "Structurat / Ordonat", "Core", "OCEAN C, HEXACO C, NEO-PI-R C2"),
        (25, "Auto-disciplină", "Procrastinator", "Disciplinat / Voință", "Core", "OCEAN C, HEXACO C, NEO-PI-R C5"),
        (26, "Competență / Perfecționism", "Pragmatic / Aproximativ", "Meticulos / Expert", "Core", "OCEAN C, HEXACO C, NEO-PI-R C1, 16PF Q3"),
        (27, "Prudență / Deliberare", "Spontan / Riscant", "Calculat / Precaut", "Core", "OCEAN C, HEXACO C, NEO-PI-R C6"),
        (28, "Dorința de Realizare", "Leneș / Neambițios", "Ambițios / Carierist", "Core", "OCEAN C, NEO-PI-R C4"), # CORECTAT cf. notițelor
        (29, "Simțul Datoriei", "Rebel / Nonconformist", "Loial / Responsabil", "Core", "OCEAN C, NEO-PI-R C3"),

        # --- GRUPA 5: DESCHIDERE ---
        (30, "Apreciere Estetică", "Utilitar", "Artistic / Sensibil", "Core", "OCEAN O, HEXACO O, NEO-PI-R O2"),
        (31, "Curiozitate Intelectuală (Idei)", "Tradiționalist", "Intelectual / Filozof", "Core", "OCEAN O, HEXACO O, NEO-PI-R O5"),
        (32, "Fantezie / Creativitate", "Realist", "Visător / Imaginativ", "Core", "OCEAN O, HEXACO O, NEO-PI-R O1"),
        (33, "Valori / Neconvenționalitate", "Conformist / Dogmatic", "Liberal / Deschis", "Core", "OCEAN O, HEXACO O, NEO-PI-R O6"),
        (34, "Deschidere la Acțiuni", "Rutină / Obicei", "Nou / Experimentare", "Core", "OCEAN O, NEO-PI-R O4"),
        (35, "Emoții Pozitive (Optimism)", "Pesimist / Melancolic", "Optimist / Vesel", "EQ", "OCEAN E, NEO-PI-R E6"), 
        
        # --- COMPLETĂRI CRITICE (36-50) ---
        (36, "Vulnerabilitate la Stres", "Rezilient / Tare", "Fragil / Copleșit", "Core", "OCEAN N, NEO-PI-R N6, 16PF C"),
        (37, "Ostilitate (Furie)", "Calm / Pașnic", "Furios / Agresiv", "Core", "OCEAN N, NEO-PI-R N2"),
        (38, "Receptivitate Emoțională", "Ignoră Emoțiile", "Trăiește Intens", "Core", "OCEAN O, NEO-PI-R O3"),
        (39, "Supunere / Conciliere", "Combativ", "Împăciuitor / Cedează", "Core", "OCEAN A, NEO-PI-R A4"),
        (40, "Gândire Abstractă/Raționament (IQ)", "Gândire Concretă", "Gândire Abstractă", "Cognitiv", "16PF B"),
        (41, "Diplomație / Secretomanie", "Deschis / Naiv", "Calculat / Secretos", "Style", "16PF N"),
        (42, "Dominanță", "Pasiv", "Autoritar / Șef", "Style", "16PF E"),
        (43, "Respectare Reguli", "Anarhist", "Procedural / Conformist", "Style", "16PF G"),
        (44, "Sensibilitate Artistică", "Dur / Realist", "Rafinat / Sensibil", "Style", "16PF I"),
        (45, "Vigilență / Suspiciune", "Încrezător", "Suspicios / Paranoic", "Style", "16PF L"),
        (46, "Visare / Distragere", "Prezent / Atent", "Distrat / Cu capul în nori", "Style", "16PF M"),
        (47, "Îngrijorare (Apprehension)", "Încrezător", "Temător / Vinovat", "Style", "16PF O"),
        (48, "Auto-suficiență", "Muncă în Echipă", "Lup Singuratic", "Style", "16PF Q2"),
        (49, "Tensiune Nervoasă", "Relaxat", "Tensionat / Nerăbdător", "Style", "16PF Q4"),
        (50, "Deschidere la Schimbare", "Conservator", "Radical / Inovator", "Style", "16PF Q1"),

        # --- MONȘTRI PRINCIPALI & INTERESE (51-69) ---
        (51, "Machiavelism", "N/A", "DETECTAT", "Monster", "Dark Triad"),
        (52, "Narcisism", "N/A", "DETECTAT", "Monster", "Dark Triad"),
        (53, "Psihopatie", "N/A", "DETECTAT", "Monster", "Dark Triad"),
        (54, "Interes Realist (Tehnic)", "Mental / Abstract", "Practic / Manual", "Career", "Holland R"), 
        (55, "Interes Întreprinzător", "Executant", "Vânzări / Business", "Career", "Holland E"),
        (56, "Management Emoțional", "Reactiv", "Reglat / Controlat", "EQ", "TEIQue"),
        (57, "Percepție Emoțională", "Orb Emoțional", "Empat / Intuitiv", "EQ", "TEIQue"), 
        (58, "Somatizare", "Sănătos", "Ipohondru / Dureri", "Clinic", "MMPI"),
        (59, "Gândire Bizară", "Rațional", "Psihotic / Delirant", "Clinic", "MMPI"),
        (60, "Comportament Antisocial", "Legal / Moral", "Antisocial / Criminal", "Monster", "MMPI RC4"), 
        (61, "Interes Investigativ (Știință)", "Intuitiv", "Analitic / Curios", "Career", "Holland I"),
        (62, "Interes Artistic", "Convențional", "Creativ / Expresiv", "Career", "Holland A"),
        (63, "Interes Social (Ajutor)", "Lucru cu obiecte", "Lucru cu oameni", "Career", "Holland S"),
        (64, "Interes Convențional (Date)", "Improvizație", "Date / Cifre / Birocrație", "Career", "Holland C"),
        (65, "Locus of Control", "Extern (Soarta)", "Intern (Eu decid)", "Values", "Rotter"), 
        (66, "Auto-reglare (Control)", "Impulsiv", "Controlat", "EQ", "TEIQue"),
        (67, "Exprimare Emoțională", "Închis", "Expresiv", "EQ", "TEIQue"),
        (68, "Demoralizare", "Speranță", "Disperare / Renunțare", "Clinic", "MMPI"),
        (69, "Cinism (Mizantropie)", "Încredere", "Oamenii sunt Răi", "Clinic", "MMPI"),

        # --- PATOLOGIE & DATING (70-78) ---
        (70, "Atașament Anxios", "Sigur", "Anxios / Nevoie Confirmare", "Dating", "ECR"),
        (71, "Atașament Evitant", "Conectat", "Distant / Evitant", "Dating", "ECR"),
        (72, "Grit (Perseverență)", "Renunță ușor", "Tenace / Încăpățânat", "Values", "Duckworth"),
        (73, "Recunoștință", "Nemulțumit", "Recunoscător", "Values", "VIA"),
        (74, "Anhedonie", "Bucuros de viață", "Gol interior / Lipsă plăcere", "Clinic", "DSM-5"),
        (75, "Alexitimie", "Conectat emoțional", "Deconectat / Robot", "Clinic", "TAS-20"),
        (76, "Dezinhibiție", "Prudent", "Riscant / Nesăbuit", "Clinic", "PID-5"),
        (77, "Burnout (Epuizare)", "Energic / Motivat", "Epuizat / Cinic", "Clinic", "MBI"),
        (78, "Depersonalizare (Job)", "Prezent", "Detașat / Ireal", "Clinic", "MBI"),

        # --- BIO, VALORI & MONȘTRI SECUNDARI (79-102) ---
        (79, "Cronotip", "Matinal / Ciocârlie", "Vespertin / Bufniță", "Bio", "MEQ"),
        (80, "Sensibilitate Senzorială", "Tanc / Insensibil", "HSP / Hipersensibil", "Bio", "HSP Scale"),
        (81, "Libido", "Scăzut / Asexual", "Ridicat / Intens", "Dating", "General"),
        (82, "Stil Învățare", "Teoretic / Carte", "Practic / Experiment", "Bio", "Kolb"),
        (83, "Toleranță la Risc (Financiar)", "Aversiune Risc", "Jucător / Riscant", "Bio", "DOSPERT"),
        (84, "Sadism Cotidian", "N/A", "DETECTAT", "Monster", "CAST"),
        (85, "Disociere", "Ancorat", "Visător / Absent", "Clinic", "DES-II"),
        (86, "Motivație Financiară", "Misionar / Sens", "Mercenar / Bani", "Values", "Schwartz"),
        (87, "Tradiționalism", "Liberal / Modern", "Tradiționalist / Familie", "Values", "Schwartz"),
        (88, "Romantism", "Pragmatic / Cynic", "Idealist / Romantic", "Dating", "RBS"),
        
        # --- MONȘTRI COMPORTAMENTALI (CWB) ---
        (89, "Agresivitate", "Calm", "PERICULOS / VIOLENT", "Monster", "CWB-C"),
        (90, "Integritate (Risc Fraudă)", "Integru", "RISC FRAUDĂ", "Monster", "PSI"),
        (91, "Hărțuire (Boundaries)", "Respectuos", "PRĂDĂTOR", "Monster", "LPI"),
        (92, "Neglijență", "Responsabil", "PERICOL ACCIDENT", "Monster", "Hogan"),
        (93, "Uncoachable", "Deschis", "AROGANT / REFRACTAR", "Monster", "CPI"),
        (94, "Sabotor", "Colegial", "TOXIC / SUBMINARE", "Monster", "Dark Tetrad"),
        (95, "Loafing (Chiul)", "Implicat", "PARAZIT SOCIAL", "Monster", "Org Psych"),
        (96, "Malicious (Răutate)", "Binevoitor", "RĂZBUNĂTOR", "Monster", "CAST"),
        (97, "Flight Risk", "Loial / Stabil", "MERCENAR / PLECARE", "Monster", "Mobley"),
        (98, "Victimizare / Martir", "Asumat", "MARTIR / DĂ VINA", "Monster", "Rotter"),
        (99, "Dezirabilitate Socială", "Autentic", "MINCIUNĂ / FALSITATE", "Control", "Marlowe-Crowne"),
        (100, "Micromanagement", "Delegă / Încredere", "Control Freak", "Monster", "Hogan"),
        (101, "Sindrom Impostor", "Încrezător", "Fals / Frică", "Monster", "CIPS"),
        (102, "Yes-Man (Submisiv)", "Asertiv", "Supus / Pleaser", "Monster", "BDI")
    ]

    try:
        # AICI FOLOSIM FORMATUL CU 6 COLOANE (ID, NAME, LEFT, RIGHT, CAT, SOURCE)
        # Atenție: În init_db.py am creat 'axes' cu coloanele respective.
        # Acest script le va suprascrie complet.
        
        cursor.executemany("""
            INSERT INTO axes (id, name, left_pole, right_pole, category, source_system)
            VALUES (?, ?, ?, ?, ?, ?)
        """, axes_data)
        
        conn.commit()
        log("db_conn", f"Sincronizare completă: {len(axes_data)} axe aliniate cu Master List.")
        
    except sqlite3.Error as error:
        log_error("Eroare SQL la realiniere", error)
    finally:
        conn.close()

    # NOTĂ IMPORTANTĂ:
    # Deoarece am schimbat ID-urile, întrebările vechi (ID 1, 2, 3) ar putea fi acum pe axe greșite 
    # dacă ID-urile lor s-au mutat.
    # Dar: ID 1, 2, 3 au rămas Sinceritate, Corectitudine, Lăcomie. Deci suntem SAFE.
    # Totuși, orice regulă din Synergy (Tab 3) care folosea ID-uri vechi (ex: 60) trebuie ștearsă/refăcută.
    # Voi rula și un clean pe Synergy.
    
    _clean_broken_rules(db_path)

def _clean_broken_rules(db_path):
    # Funcție de curățare preventivă
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM synergy_rules") # Resetăm regulile ca să nu avem id-uri fantomă
    conn.commit()
    conn.close()
    log("sys", "Regulile Synergy au fost resetate pentru siguranță (trebuie rulate din nou scripturile de populare).")

if __name__ == "__main__":
    populate_axes()