import json
from ai_agents.llm_connector import AIConnector
from logic.knowledge_manager import KnowledgeManager
from logger import log, log_error

class ArchitectAgent:
    def __init__(self):
        self.ai = AIConnector()
        self.db = KnowledgeManager()

    def generate_template_structure(self, user_intent):
        # 1. Luăm toate axele cu detalii complete
        all_axes = self.db.get_all_axes()
        # Formatăm contextul incluzând SURSA SISTEM
        axes_context = [
            {
                "id": a[0], 
                "name": a[1], 
                "category": a[2], 
                "source": a[5] # Coloana source_system din DB
            } for a in all_axes
        ]
        
        try:
            system_prompt = self.ai.load_prompt_template("architect_wizard.txt")
        except Exception as e:
            log_error("Architect prompt missing", e)
            return None

        log("ai_req", f"Architect Wizard solicitat pentru: '{user_intent}'")
        
        full_context = f"User Intent: {user_intent}\n\nAvailable Axes:\n{json.dumps(axes_context)}"
        raw_response = self.ai.generate_text(system_prompt, full_context)
        
        try:
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            return data
        except json.JSONDecodeError as e:
            log_error("AI returned invalid JSON", raw_response)
            return None


    def generate_single_question(self, axis_data, existing_qs):
        """Metodă integrală care generează o întrebare nouă, analizând contextul actual."""
        try:
            system_prompt = self.ai.load_prompt_template("question_generator.txt")
        except:
            return None

        # Formatăm întrebările existente pentru a fi ușor de citit de AI
        qs_context = ""
        for i, q in enumerate(existing_qs, 1):
            qs_context += f"{i}. {q['text']} (Tags: {q['tags']})\n"
            for opt in q['options']:
                qs_context += f"   - {opt[1]} ({opt[2]} pts)\n"

        context = (
            f"Nume Axa: {axis_data['name']}\n"
            f"Descriere: {axis_data['description']}\n"
            f"Poli: 0={axis_data['left']} | 100={axis_data['right']}\n"
            f"Sursă: {axis_data['source']}\n\n"
            f"ÎNTREBĂRI EXISTENTE:\n{qs_context if qs_context else 'Nicio întrebare existentă.'}"
        )

        raw_response = self.ai.generate_text(system_prompt, context)
        
        try:
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except:
            return None