import sqlite3
from config import Config
from logger import log, log_error

class SynergyManager:
    def __init__(self):
        self.db_path = Config.DB_NAME

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_monsters(self):
        """
        Returnează axele care pot fi ținta unor reguli.
        Acum includem: Monster, Clinic ȘI Control (ID 99).
        """
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # MODIFICAREA E AICI: Am adăugat 'Control' în listă
            c.execute("SELECT id, name FROM axes WHERE category IN ('Monster', 'Clinic', 'Control') ORDER BY id")
            return c.fetchall()
        finally:
            conn.close()

    def get_all_axes_for_dropdown(self):
        """Toate axele posibile care pot servi ca TRIGGER (Ingrediente)."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # Excludem monștrii din lista de ingrediente ca să nu facem bucle infinite
            # Dar permitem ca 'Control' să fie și ingredient dacă e nevoie
            c.execute("SELECT id, name FROM axes WHERE category NOT IN ('Monster', 'Clinic') ORDER BY name")
            return c.fetchall()
        finally:
            conn.close()

    def get_rules_for_monster(self, monster_id):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            query = """
                SELECT r.id, r.trigger_axis_id, a.name, r.operator, r.threshold
                FROM synergy_rules r
                JOIN axes a ON r.trigger_axis_id = a.id
                WHERE r.monster_axis_id = ?
            """
            c.execute(query, (monster_id,))
            return c.fetchall()
        finally:
            conn.close()

    def add_rule(self, monster_id, trigger_id, operator, threshold):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO synergy_rules (monster_axis_id, trigger_axis_id, operator, threshold)
                VALUES (?, ?, ?, ?)
            """, (monster_id, trigger_id, operator, threshold))
            conn.commit()
            log("monster", f"Regulă nouă adăugată pentru Monstrul {monster_id}")
            return True
        except Exception as e:
            log_error("Add Rule Error", e)
            return False
        finally:
            conn.close()

    def delete_rule(self, rule_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM synergy_rules WHERE id=?", (rule_id,))
        conn.commit()
        conn.close()
        log("monster", f"Regula {rule_id} ștearsă.")

    def get_all_rules_with_full_metadata(self):
        """Metodă integrală care extrage toate regulile de sinergie cu metadatele axelor asociate."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            # Interogare complexă pentru a aduce nume, sursă și poli pentru ambele axe
            query = """
                SELECT 
                    r.id,
                    m.name AS monster_name,
                    m.source_system AS monster_source,
                    a.name AS trigger_name,
                    a.source_system AS trigger_source,
                    a.left_pole AS trigger_left,
                    a.right_pole AS trigger_right,
                    r.operator,
                    r.threshold
                FROM synergy_rules r
                JOIN axes m ON r.monster_axis_id = m.id
                JOIN axes a ON r.trigger_axis_id = a.id
                ORDER BY m.name, r.id
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            conexiune.close()