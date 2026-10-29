import sqlite3
from config import Config
from logger import log, log_error

class StrategyManager:
    def __init__(self):
        self.db_path = Config.DB_NAME
        # 1. Creăm tabela dacă nu există
        self.create_table_if_not_exists()
        # 2. Actualizăm structura (Migrare automată pentru noile praguri)
        self.migrate_database_schema()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_table_if_not_exists(self):
        """Metodă integrală pentru crearea structurii de bază."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS exam_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    w1_base_qty INTEGER DEFAULT 3,
                    contradiction_threshold REAL DEFAULT 40.0,
                    yellow_extra_qty INTEGER DEFAULT 3,
                    red_extra_qty INTEGER DEFAULT 7,
                    monster_trigger_timing TEXT DEFAULT 'După Val 2 (Stabilizare)',
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def migrate_database_schema(self):
        """Metodă integrală care adaugă coloanele lipsă pentru algoritmul dual."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Listă cu noile coloane necesare
        new_columns = [
            ("dev_threshold_minor", "REAL DEFAULT 20.0"),
            ("dev_minor_qty", "INTEGER DEFAULT 3"),
            ("dev_threshold_major", "REAL DEFAULT 30.0"),
            ("dev_major_qty", "INTEGER DEFAULT 7"),
            ("monster_injection_qty", "INTEGER DEFAULT 3")  # NOU: întrebări per monstru
        ]
        
        for col_name, col_type in new_columns:
            try:
                # Încercăm să adăugăm coloana. Dacă există deja, SQLite va arunca o eroare pe care o ignorăm.
                c.execute(f"ALTER TABLE exam_strategies ADD COLUMN {col_name} {col_type}")
                log("sys", f"Baza de date actualizată: Adăugată coloana {col_name}")
            except sqlite3.OperationalError:
                # Coloana există deja, mergem mai departe
                pass
        
        conn.commit()
        conn.close()

    def get_all_strategies(self):
        """Returnează toate strategiile pentru listă."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # SELECT explicit pentru a garanta ordinea coloanelor
            c.execute("""
                SELECT id, name, description, w1_base_qty, 
                       yellow_extra_qty, red_extra_qty, monster_trigger_timing, is_active,
                       dev_threshold_minor, dev_threshold_major, 
                       dev_minor_qty, dev_major_qty,
                       COALESCE(monster_injection_qty, 3) as monster_injection_qty
                FROM exam_strategies 
                ORDER BY id DESC
            """)
            return c.fetchall()
        finally:
            conn.close()

    def save_strategy(self, name, desc, w1, yellow_j, red_j, dev_min_t, dev_min_q, dev_maj_t, dev_maj_q, timing, monster_qty=3, strat_id=None):
        """Metodă integrală de salvare sincronizată cu interfața duală."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            if strat_id:
                # Modul UPDATE
                c.execute("""
                    UPDATE exam_strategies 
                    SET name=?, description=?, w1_base_qty=?, 
                        yellow_extra_qty=?, red_extra_qty=?, 
                        dev_threshold_minor=?, dev_minor_qty=?,
                        dev_threshold_major=?, dev_major_qty=?,
                        monster_trigger_timing=?, monster_injection_qty=?
                    WHERE id=?
                """, (name, desc, w1, yellow_j, red_j, dev_min_t, dev_min_q, dev_maj_t, dev_maj_q, timing, monster_qty, strat_id))
            else:
                # Modul INSERT
                c.execute("""
                    INSERT INTO exam_strategies 
                    (name, description, w1_base_qty, yellow_extra_qty, red_extra_qty, 
                     dev_threshold_minor, dev_minor_qty, dev_threshold_major, dev_major_qty, monster_trigger_timing, monster_injection_qty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, desc, w1, yellow_j, red_j, dev_min_t, dev_min_q, dev_maj_t, dev_maj_q, timing, monster_qty))
            
            conn.commit()
            return True
        except Exception as e:
            log_error("Eroare la scrierea strategiei în bază", e)
            return False
        finally:
            conn.close()

    def delete_strategy(self, strat_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM exam_strategies WHERE id=?", (strat_id,))
        conn.commit()
        conn.close()