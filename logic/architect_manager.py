import sqlite3
import json
from config import Config
from logger import log, log_error

class ArchitectManager:
    def __init__(self):
        self.db_path = Config.DB_NAME
        self.ensure_database_schema_updated()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def ensure_database_schema_updated(self):
        """Metodă integrală care adaugă coloana strategy_id dacă nu există."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            cursor.execute("PRAGMA table_info(test_templates)")
            coloane = [col[1] for col in cursor.fetchall()]
            if "strategy_id" not in coloane:
                cursor.execute("ALTER TABLE test_templates ADD COLUMN strategy_id INTEGER")
                conexiune.commit()
                log("sys", "Baza de date actualizată: Adăugat strategy_id în test_templates.")
        finally:
            conexiune.close()

    def get_all_templates(self):
        """Returnează lista de teste salvate."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT id, name, description, strategy_id FROM test_templates ORDER BY id DESC")
            return c.fetchall()
        finally:
            conn.close()

    def save_template(self, name, description, axis_ids, strategy_id, template_id=None):
        """Salvează configurația simplificată a unui test."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # MIGRARE: Verificăm dacă există coloana strategy_id
            c.execute("PRAGMA table_info(test_templates)")
            columns = [col[1] for col in c.fetchall()]
            if "strategy_id" not in columns:
                c.execute("ALTER TABLE test_templates ADD COLUMN strategy_id INTEGER")
                conn.commit()
                print("✅ DB Migration: Adăugat strategy_id în test_templates")
            
            # Salvăm doar lista de ID-uri de axe ca JSON
            config_json = json.dumps({"axes": axis_ids})
            
            if template_id:
                c.execute("""
                    UPDATE test_templates 
                    SET name=?, description=?, config_json=?, strategy_id=?
                    WHERE id=?
                """, (name, description, config_json, strategy_id, template_id))
            else:
                c.execute("""
                    INSERT INTO test_templates (name, description, config_json, strategy_id)
                    VALUES (?, ?, ?, ?)
                """, (name, description, config_json, strategy_id))
            
            conn.commit()
            return True
        except Exception as e:
            log_error("Eroare salvare template", e)
            return False
        finally:
            conn.close()

    def load_template_data(self, template_id):
        """Încarcă datele brute ale unui test."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT name, description, config_json, strategy_id FROM test_templates WHERE id=?", (template_id,))
            return c.fetchone()
        finally:
            conn.close()
            
    def delete_template(self, template_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM test_templates WHERE id=?", (template_id,))
        conn.commit()
        conn.close()

