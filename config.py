import os
import shutil

from dotenv import load_dotenv


class Config:
    # Folderul cu codul (acesta e repository-ul de pe GitHub)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Datele personale stau ÎN AFARA codului, în folderul Data de lângă Project:
    #
    #   <rădăcină>/
    #   ├── Project/   codul (GitHub)
    #   └── Data/      baza de date, pacienți, rapoarte, setări, .env (NU urcă pe GitHub)
    #
    # Se poate muta oriunde cu variabila de mediu HUNTER_DATA_DIR.
    DATA_DIR = os.environ.get("HUNTER_DATA_DIR") or os.path.join(os.path.dirname(BASE_DIR), "Data")

    DB_NAME = os.path.join(DATA_DIR, "hunter_protocol.db")
    PATIENTS_DIR = os.path.join(DATA_DIR, "pacienti")
    SETTINGS_FILE = os.path.join(DATA_DIR, "user_settings.json")
    ENV_FILE = os.path.join(DATA_DIR, ".env")

    # Baza de cunoștințe publică (axe, întrebări, reguli), fără date personale.
    # La prima pornire devine baza de lucru din Data/.
    KNOWLEDGE_BASE = os.path.join(BASE_DIR, "database", "knowledge_base.db")

    PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

    GOOGLE_API_KEY = None

    @staticmethod
    def prepare_data_dir():
        """Creează Data/ și, la prima pornire, baza de lucru din baza de cunoștințe."""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.PATIENTS_DIR, exist_ok=True)
        if not os.path.exists(Config.DB_NAME) and os.path.exists(Config.KNOWLEDGE_BASE):
            shutil.copyfile(Config.KNOWLEDGE_BASE, Config.DB_NAME)
            print(f"🆕 Bază de date nouă creată din baza de cunoștințe: {Config.DB_NAME}")

    @staticmethod
    def validate():
        if not Config.GOOGLE_API_KEY:
            print(f"⚠️ ATENȚIE: Nu s-a găsit GOOGLE_API_KEY (pune-l în {Config.ENV_FILE})")

        # Debug: Să vedem în consolă calea exactă
        print(f"🔧 CONFIG DB PATH: {Config.DB_NAME}")


# .env din Data/ are prioritate; un .env lângă cod e acceptat ca rezervă.
load_dotenv(Config.ENV_FILE)
load_dotenv(os.path.join(Config.BASE_DIR, ".env"))
Config.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
Config.prepare_data_dir()
