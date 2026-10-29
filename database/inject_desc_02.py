import sqlite3
import os
import sys

# --- FIX CALE ABSOLUTĂ ---
# Aflăm folderul unde se află acest script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Construim calea către DB (care e în același folder)
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from config import Config
DB_PATH = Config.DB_NAME

def inject_axis_description(axis_id, description_text):
    """Metodă integrală pentru injectarea manuală a descrierilor tehnice."""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ EROARE: Nu am găsit baza de date la calea: {DB_PATH}")
        return

    try:
        # 1. Conectare
        conexiune = sqlite3.connect(DB_PATH)
        cursor = conexiune.cursor()

        # 2. Executare Update
        query = "UPDATE axes SET description = ? WHERE id = ?"
        cursor.execute(query, (description_text, axis_id))

        # 3. Verificare succes
        if cursor.rowcount > 0:
            conexiune.commit()
            print(f"✅ SUCCES: Nota tehnică a fost injectată pentru Axa ID {axis_id}.")
        else:
            print(f"⚠️ ATENȚIE: Nu s-a găsit nicio axă cu ID-ul {axis_id} în baza de date.")

    except sqlite3.Error as e:
        print(f"❌ EROARE SQL: {e}")
    finally:
        conexiune.close()

# --- TEXTUL PROFESIONAL PENTRU AXA 02 ---
nota_axa_02 = """DEFINIȚIE OPERAȚIONALĂ:
Evaluează tendința subiectului de a evita frauda, corupția și înșelăciunea în obținerea avantajelor materiale sau de statut. Măsoară adeziunea la principii etice stricte versus oportunism. Spre deosebire de Sinceritate (care ține de comunicare), Corectitudinea vizează acțiunile, tranzacțiile și respectarea proprietății.

INTERPRETARE SCORURI:
Scor Scăzut (0-30): Indică predispoziție spre Oportunism și Risc de Fraudă. Subiectul poate fi dispus să "taie curbele" etice, să profite de lacunele sistemului sau să își însușească bunuri/merite necuvenite dacă consideră că riscul de a fi prins este mic. Mentalitate tranzacțională de tip "care pe care".
Scor Ridicat (70-100): Indică o Etică Principială. Subiectul refuză să profite de ceilalți sau de sistem, chiar și atunci când ar fi ușor sau acceptabil social. Este corect, returnează restul primit în plus și respectă regulile jocului cu strictețe. Poate fi perceput ca rigid în negocieri "gri".

NOTE TEHNICE & CORELAȚII:
Sursă Primară: Factorul H (Honesty-Humility) din modelul HEXACO (Fațeta: Fairness).
Validitate: Este predictorul principal pentru comportamentele contraproductive la locul de muncă (CWB), în special furtul, delapidarea și mita.
Sinergii: Scorurile mici aici, combinate cu Lăcomie mare (ID 3), declanșează Monstrul "Integritate/Risc Fraudă" (ID 90)."""

if __name__ == "__main__":
    # Rulăm injectarea pentru ID 2
    inject_axis_description(2, nota_axa_02)