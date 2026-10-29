import sqlite3
import hashlib
import json
from config import Config
from logger import log, log_error

class KnowledgeManager:
    def __init__(self):
        self.db_path = Config.DB_NAME
        # Verificăm la inițializare dacă schema bazei de date este actualizată
        self.ensure_database_schema_updated()

    def ensure_database_schema_updated(self):
        """Metodă integrală care verifică existența noilor coloane și le adaugă dacă lipsesc."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            cursor.execute("PRAGMA table_info(axes)")
            coloane_existente = [coloana[1] for coloana in cursor.fetchall()]
            
            if "description" not in coloane_existente:
                cursor.execute("ALTER TABLE axes ADD COLUMN description TEXT")
            
            if "hex_color" not in coloane_existente:
                cursor.execute("ALTER TABLE axes ADD COLUMN hex_color TEXT DEFAULT '#ffffff'")
                
            conexiune.commit()
        finally:
            conexiune.close()

    def get_all_axes(self):
        """Returnează lista completă cu toate detaliile, inclusiv descrierea și culoarea."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            # Adăugăm coloanele noi în SELECT
            query = "SELECT id, name, category, left_pole, right_pole, source_system, description, hex_color FROM axes ORDER BY category, name"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log_error("Eroare la citirea axelor detaliate", e)
            return []
        finally:
            conexiune.close()

    def update_axis_skin(self, axis_id, nume_nou, categorie_noua, stanga, dreapta, sursa, descriere, culoare_hex):
        """Actualizează toate metadatele axei în baza de date."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            query = """
                UPDATE axes 
                SET name=?, category=?, left_pole=?, right_pole=?, source_system=?, description=?, hex_color=?
                WHERE id=?
            """
            cursor.execute(query, (nume_nou, categorie_noua, stanga, dreapta, sursa, descriere, culoare_hex, axis_id))
            conexiune.commit()
            return True
        except Exception as e:
            log_error(f"Eșec la actualizarea completă a axei {axis_id}", e)
            return False
        finally:
            conexiune.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    # ==========================
    # ZONA ÎNTREBĂRI (TIME MACHINE CORE)
    # ==========================
    def get_questions_for_axis(self, axis_id):
        """Metodă integrală care returnează întrebările ordonate după prioritate (wave_target)."""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # IMPORTANT: Ordonăm după wave_target pentru a respecta prioritatea stabilită de butoane
            c.execute("""
                SELECT id, text_content, ai_tags, wave_target, version_hash 
                FROM questions_bank 
                WHERE axis_id=? AND is_active=1
                ORDER BY wave_target ASC
            """, (axis_id,))
            questions = []
            rows = c.fetchall()
            
            for q in rows:
                q_id, text, tags, wave, v_hash = q
                c.execute("""
                    SELECT option_index, text_content, score_value 
                    FROM question_options 
                    WHERE question_hash=? 
                    ORDER BY option_index
                """, (v_hash,))
                options = c.fetchall()
                
                questions.append({
                    "id": q_id, "text": text, "tags": tags,
                    "wave": wave, "hash": v_hash, "options": options
                })
            return questions
        finally:
            conn.close()

    def resequence_questions(self, axis_id, ordered_ids):
        """Metodă integrală care rescrie ordinea tuturor întrebărilor unei axe (1, 2, 3...)."""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # ordered_ids este o listă de ID-uri în ordinea dorită de utilizator
            for index, q_id in enumerate(ordered_ids, 1):
                c.execute("UPDATE questions_bank SET wave_target = ? WHERE id = ?", (index, q_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Eroare re-secvențiere: {e}")
            return False
        finally:
            conn.close()


    def save_question(self, axis_id, text, tags, wave, options_list, existing_id=None):
        content_dump = text + json.dumps(options_list, sort_keys=True)
        new_hash = hashlib.sha256(content_dump.encode('utf-8')).hexdigest()
        
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            if not existing_id:
                self._insert_new_version(c, axis_id, new_hash, text, tags, wave, options_list)
                log("arch", "Întrebare nouă creată.", details=f"Hash: {new_hash[:8]}")
            else:
                c.execute("SELECT version_hash FROM questions_bank WHERE id=?", (existing_id,))
                row = c.fetchone()
                old_hash = row[0] if row else ""

                if old_hash == new_hash:
                    c.execute("UPDATE questions_bank SET ai_tags=?, wave_target=? WHERE id=?", (tags, wave, existing_id))
                    log("arch", "Întrebare actualizată (Doar Metadata).")
                else:
                    c.execute("UPDATE questions_bank SET is_active=0 WHERE id=?", (existing_id,))
                    self._insert_new_version(c, axis_id, new_hash, text, tags, wave, options_list)
                    log("arch", "Versiune nouă creată (Time Machine preserved).")

            conn.commit()
            return True
        except Exception as e:
            log_error("Save Question Error", e)
            return False
        finally:
            conn.close()

    def _insert_new_version(self, cursor, axis_id, v_hash, text, tags, wave, options):
        cursor.execute("""
            INSERT INTO questions_bank (axis_id, version_hash, text_content, ai_tags, wave_target, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (axis_id, v_hash, text, tags, wave))
        
        for idx, opt_text, score in options:
            cursor.execute("""
                INSERT INTO question_options (question_hash, option_index, text_content, score_value)
                VALUES (?, ?, ?, ?)
            """, (v_hash, idx, opt_text, score))

    def delete_question(self, q_id):
        conn = self.get_connection()
        conn.execute("UPDATE questions_bank SET is_active=0 WHERE id=?", (q_id,))
        conn.commit()
        conn.close()
        log("arch", f"Întrebare ID {q_id} arhivată (Soft Delete).")