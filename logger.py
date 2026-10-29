import datetime

# ==========================================
# ⚙️ CONFIGURARE LOGURI (TABLEAU DE BORD)
# ==========================================
# Modifică aici True/False pentru a aprinde/stinge "reflectoarele" pe diverse module.

LOG_CONFIG = {
    # --- SISTEM & DATE ---
    "sys":      True,   # 🖥️ Pornire aplicație, încărcare module, erori critice.
    "db_conn":  True,   # 🔌 Conectare/Deconectare Bază de date.
    "db_query": False,  # 💾 (ZGOMOTOS) Afișează fiecare query SQL executat (bun pt debug intens).
    "time_mac": True,   # ⏳ Operațiuni Time Machine (încărcare snapshot, verificare hash).

    # --- INTELEGENȚĂ ARTIFICIALĂ (CO-PILOT) ---
    "ai_req":   True,   # 📤 Prompt-ul trimis către Gemini (ce îi cerem).
    "ai_resp":  False,  # 📥 Răspunsul brut de la Gemini (poate fi foarte lung).
    "ai_cost":  True,   # 💰 Tokeni consumați (dacă e cazul) sau timp de execuție.

    # --- LOGICĂ PSIHOMETRICĂ ---
    "score":    True,   # 📈 Calcule matematice (medii, deviații standard).
    "monster":  True,   # 👹 Când se declanșează un Trigger (rețeta a fost validată).
    "wave":     True,   # 🌊 Tranziția între Valul 1 -> Valul 2 -> Valul 3.
    
    # --- INTERFAȚĂ & ARCHITECT ---
    "ui":       False,  # 🖱️ Click-uri pe butoane, schimbare tab-uri.
    "arch":     True,   # 📐 Operațiuni de creare axe noi sau editare întrebări.
    
    # --- DEBUGGING HOLISTIC (TAB 1) ---
    "holistic_debug": False,  # 🔍 Afișează detalii despre întrebări per axă (schema DB, teste, cache vs DB)
    
    # --- DEBUGGING STRATEGII (HUNTER PROTOCOL V3) ---
    "strategy_debug": True,  # 🎯 Afișează încărcarea strategiei, parametrii, planificare întrebări
}

# ==========================================
# 🎨 PALETA DE CULORI (ANSI ESCAPE CODES)
# ==========================================
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GREY    = "\033[90m"

# Mapare Categorie -> Culoare & Emoji
LOG_STYLES = {
    "sys":      (Colors.WHITE,   "🚀"),
    "db_conn":  (Colors.GREEN,   "🔌"),
    "db_query": (Colors.GREY,    "💾"),
    "time_mac": (Colors.CYAN,    "⏳"),
    
    "ai_req":   (Colors.MAGENTA, "📤"),
    "ai_resp":  (Colors.MAGENTA, "📥"),
    "ai_cost":  (Colors.YELLOW,  "⚡"),
    
    "score":    (Colors.BLUE,    "📈"),
    "monster":  (Colors.RED,     "👹"),
    "wave":     (Colors.CYAN,    "🌊"),
    
    "ui":       (Colors.GREY,    "🖱️"),
    "arch":     (Colors.YELLOW,  "📐"),
    
    "holistic_debug": (Colors.CYAN, "🔍"),
    
    "strategy_debug": (Colors.YELLOW, "🎯"),
    
    "error":    (Colors.RED,     "❌")
}

def log(category, message, details=""):
    """
    Funcția principală de logare.
    Utilizare: log("sys", "Aplicația a pornit")
    """
    # 1. Verificăm dacă categoria e activă în Config
    if category != "error" and not LOG_CONFIG.get(category, False):
        return

    # 2. Obținem stilul
    color, emoji = LOG_STYLES.get(category, (Colors.WHITE, "❓"))
    
    # 3. Timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # 4. Formatare
    # [ORA] EMOJI [CAT] Mesaj ... Detalii
    formatted_msg = f"{Colors.GREY}[{timestamp}]{Colors.RESET} {emoji} {color}{Colors.BOLD}[{category.upper()}]{Colors.RESET} {message}"
    
    if details:
        formatted_msg += f"\n      {Colors.GREY}└─> {details}{Colors.RESET}"

    print(formatted_msg)

# Alias pentru erori (mereu vizibile)
def log_error(message, error_obj=None):
    details = str(error_obj) if error_obj else ""
    log("error", message, details)
