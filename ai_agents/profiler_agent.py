import json
from ai_agents.llm_connector import AIConnector
from logic.settings_manager import SettingsManager

class ProfilerAgent:
    def __init__(self):
        self.ai = AIConnector()
        self.history = []
        
    def clear_history(self):
        self.history = []

    def run_analysis(self, patients_data, persona_type):
        """Analiză instantanee bazată pe butoane (fără istoric lung)"""
        prompt_file = {
            "HR": "analyze_hr.txt",
            "Psych": "analyze_psych.txt",
            "Academic": "analyze_academic.txt"
        }.get(persona_type, "analyze_hr.txt")
        
        system_prompt = self.ai.load_prompt_template(prompt_file)
        context = self._format_context(patients_data)
        
        return self.ai.generate_text(system_prompt, context)

    def chat_step(self, user_input, patients_data, persona_type):
        """Conversație liberă cu memorie"""
        settings = SettingsManager.load_settings()
        history_limit = settings.get("ai_history_limit", 10)
        
        # Alegem persona
        prompt_file = {
            "HR": "analyze_hr.txt",
            "Psych": "analyze_psych.txt",
            "Academic": "analyze_academic.txt"
        }.get(persona_type, "analyze_hr.txt")
        
        system_prompt = self.ai.load_prompt_template(prompt_file)
        system_prompt += "\nEști într-o conversație liberă cu specialistul. Răspunde direct la întrebări folosind datele de mai jos."
        
        # Menținem istoricul
        if len(self.history) > history_limit * 2:
            self.history = self.history[-(history_limit * 2):]
            
        context = self._format_context(patients_data)
        full_user_query = f"CONTEXT DATE PACIENȚI:\n{context}\n\nÎNTREBARE UTILIZATOR: {user_input}"
        
        response = self.ai.generate_text(system_prompt, full_user_query)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})
        
        return response

    def _format_context(self, patients_data):
        """Transformă lista de pacienți într-un string lizibil pentru AI"""
        output = []
        for p in patients_data:
            p_str = f"PACIENT: {p['name']} (ID: {p['id']})\n"
            p_str += "AXE SI SCORURI:\n"
            for axis in p['holistic']:
                p_str += f"- {axis['name']}: {axis['score']}% (Confidență: {axis['confidence']}%)\n"
            output.append(p_str)
        return "\n" + "="*30 + "\n".join(output)