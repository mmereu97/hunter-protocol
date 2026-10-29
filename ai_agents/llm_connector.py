import google.generativeai as genai
import os
import sys

# Ne asigurăm că adăugăm calea rădăcină a proiectului pentru a putea importa Config
director_radacina = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(director_radacina)

from config import Config

class AIConnector:
    def __init__(self):
        # Validăm configurația pentru a ne asigura că avem cheia API
        Config.validate()
        
        if Config.GOOGLE_API_KEY:
            # Configurăm librăria Google Generative AI cu cheia din .env
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            
            # Specificăm modelul cerut: gemini-pro-latest
            self.model_ai = genai.GenerativeModel('gemini-pro-latest')
            print("✅ AI CONNECTOR: Modelul 'gemini-pro-latest' a fost inițializat cu succes.")
        else:
            self.model_ai = None
            print("❌ AI ERROR: Nu a fost găsită nicio cheie API în fișierul de configurare.")

    def load_prompt_template(self, nume_fisier_prompt):
        """
        Citește conținutul unui fișier text din directorul de prompturi definit în Config.
        """
        cale_catre_fisier = os.path.join(Config.PROMPTS_DIR, nume_fisier_prompt)
        
        try:
            with open(cale_catre_fisier, "r", encoding="utf-8") as fisier_deschis:
                return fisier_deschis.read()
        except FileNotFoundError:
            return f"Eroare: Fișierul de prompt '{nume_fisier_prompt}' nu a fost găsit la calea {cale_catre_fisier}."
        except Exception as eroare_citire:
            return f"Eroare la citirea promptului: {str(eroare_citire)}"

    def generate_text(self, prompt_sistem, context_utilizator):
        """
        Trimite o cerere către modelul Gemini și returnează răspunsul generat.
        prompt_sistem: Instrucțiunile de rol pentru AI.
        context_utilizator: Datele pacienților și întrebările specifice.
        """
        if not self.model_ai:
            return "Eroare: Motorul AI nu este conectat sau lipsește cheia API."

        # Construim promptul complet combinând rolul cu datele de intrare
        prompt_complet_final = f"{prompt_sistem}\n\nCONTEXT DATE:\n{context_utilizator}"
        
        try:
            # Apelăm metoda de generare a conținutului
            raspuns_generat = self.model_ai.generate_content(prompt_complet_final)
            
            # Verificăm dacă răspunsul conține text valid
            if raspuns_generat and raspuns_generat.text:
                return raspuns_generat.text
            else:
                return "AI-ul a returnat un răspuns gol sau a blocat conținutul din motive de siguranță."
                
        except Exception as eroare_generare:
            return f"Eroare la generarea textului prin AI: {str(eroare_generare)}"