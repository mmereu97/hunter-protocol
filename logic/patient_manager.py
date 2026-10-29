import sqlite3
import hashlib
import json
from config import Config
from logger import log, log_error

class PatientManager:
    def __init__(self):
        self.db_path = Config.DB_NAME
        # Creăm tabela de rapoarte automat la inițializare pentru a evita erorile de tip "no such table"
        self.create_reports_table()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _hash_cnp(self, cnp):
        """Anonimizare simplă prin hashing SHA-256."""
        return hashlib.sha256(cnp.encode()).hexdigest()[:16]

    def add_patient(self, full_name, cnp, age, gender, occupation, notes):
        """Adaugă un pacient nou în baza de date cu CNP hash-uit."""
        cnp_final = self._hash_cnp(cnp) 
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO patients (cnp_hash, full_name, age, gender, occupation, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cnp_final, full_name, age, gender, occupation, notes))
            conn.commit()
            log("sys", f"Pacient nou adăugat: {full_name}")
            return True
        except sqlite3.IntegrityError:
            log_error("Duplicate Patient", "CNP-ul există deja în sistem.")
            return False
        except Exception as e:
            log_error("Add Patient Error", e)
            return False
        finally:
            conn.close()

    def get_all_patients(self):
        """Returnează lista tuturor pacienților pentru popularea listei principale."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT id, full_name, age, occupation, cnp_hash FROM patients ORDER BY id DESC")
            return c.fetchall()
        finally:
            conn.close()

    def get_patient_details(self, patient_id):
        """Returnează toate detaliile unui pacient specific pe baza ID-ului."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
            return c.fetchone()
        finally:
            conn.close()

    def get_holistic_profile(self, patient_id):
        """
        Interoghează cache-ul holistic pentru un pacient.
        Include verificarea dacă axa este țintă pentru regulile de sinergie (is_monster_target).
        
        IMPORTANT: 
        - questions_total = Câte întrebări sunt disponibile în questions_bank pentru acea axă
        - questions_used = Câte întrebări DISTINCTE a răspuns pacientul VREODATĂ (din TOATE sesiunile)
        """
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # MIGRARE: Asigurăm că avem coloana questions_used
            c.execute("PRAGMA table_info(holistic_knowledge)")
            columns = [col[1] for col in c.fetchall()]
            newly_added = False
            
            if "questions_used" not in columns:
                c.execute("ALTER TABLE holistic_knowledge ADD COLUMN questions_used INTEGER DEFAULT 0")
                conn.commit()
                print("✅ DB Migration: Adăugat questions_used în holistic_knowledge")
                newly_added = True
            
            # Verificăm dacă trebuie să populăm
            c.execute("SELECT COUNT(*) FROM holistic_knowledge WHERE questions_used > 0")
            has_data = c.fetchone()[0] > 0
            
            # FORȚEZ RECALCULARE: Pentru a corecta cache-ul vechi greșit
            # TODO: După ce toți utilizatorii au actualizat, această secțiune poate fi comentată
            force_recalc = True  # Setează False după prima rulare cu succes
            
            if newly_added or not has_data or force_recalc:
                # POPULARE: Recalculez pentru TOATE înregistrările existente
                print("🔄 Recalculare FORȚATĂ a questions_used pentru TOATE înregistrările...")
                c.execute("SELECT patient_id, axis_id FROM holistic_knowledge")
                records = c.fetchall()
                
                updated_count = 0
                for pat_id, ax_id in records:
                    # CUMUL: Câte întrebări din această axă a răspuns pacientul în toate sesiunile
                    # session_responses DEJA ARE axis_id direct!
                    c.execute("""
                        SELECT COUNT(*)
                        FROM session_responses resp
                        JOIN sessions s ON resp.session_id = s.id
                        WHERE s.patient_id = ? AND resp.axis_id = ?
                    """, (pat_id, ax_id))
                    
                    count = c.fetchone()[0] or 0
                    # Actualizez ÎNTOTDEAUNA, chiar dacă e 0
                    c.execute("UPDATE holistic_knowledge SET questions_used = ? WHERE patient_id = ? AND axis_id = ?", 
                             (count, pat_id, ax_id))
                    updated_count += 1
                
                conn.commit()
                print(f"✅ Recalculat questions_used pentru {updated_count} înregistrări")
            
            query = """
                SELECT 
                    a.id as axis_id,
                    a.name, 
                    h.latest_score, 
                    h.confidence, 
                    h.last_updated_at, 
                    a.category,
                    a.left_pole,
                    a.right_pole,
                    a.norm_mean,
                    a.norm_std_dev,
                    (SELECT COUNT(*) FROM synergy_rules WHERE monster_axis_id = a.id) as is_monster_target,
                    (SELECT COUNT(*) FROM questions_bank WHERE axis_id = a.id AND is_active = 1) as total_questions,
                    COALESCE(h.questions_used, 0) as used_questions
                FROM holistic_knowledge h
                JOIN axes a ON h.axis_id = a.id
                WHERE h.patient_id = ?
                ORDER BY 
                    (SELECT COUNT(*) FROM synergy_rules WHERE monster_axis_id = a.id) ASC,  -- Normale (0) primele, Monștrii (>0) la final
                    a.name ASC  -- Alfabetic pe nume
            """
            c.execute(query, (patient_id,))
            return c.fetchall()
        finally:
            conn.close()
            
    def delete_patient(self, patient_id):
        """Șterge un pacient și toate datele asociate (sesiuni, rezultate, cunoștințe)."""
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM session_results WHERE session_id IN (SELECT id FROM sessions WHERE patient_id=?)", (patient_id,))
            conn.execute("DELETE FROM session_responses WHERE session_id IN (SELECT id FROM sessions WHERE patient_id=?)", (patient_id,))
            conn.execute("DELETE FROM sessions WHERE patient_id=?", (patient_id,))
            conn.execute("DELETE FROM holistic_knowledge WHERE patient_id=?", (patient_id,))
            conn.execute("DELETE FROM ai_reports WHERE patient_id=?", (patient_id,))
            conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
            conn.commit()
            log("sys", f"Pacient {patient_id} șters complet.")
        finally:
            conn.close()

    def create_reports_table(self):
        """Creează tabela pentru stocarea rapoartelor AI dacă aceasta nu există deja."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    persona TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(patient_id) REFERENCES patients(id),
                    UNIQUE(patient_id, persona)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def save_ai_report(self, patient_id, persona, content):
        """
        Salvează sau actualizează un raport AI în baza de date.
        Folosește INSERT OR REPLACE pentru a menține doar cel mai recent raport per persona per pacient.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ai_reports (patient_id, persona, content, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (patient_id, persona, content))
            conn.commit()
            return True
        except Exception as e:
            print(f"Eroare salvare raport AI: {e}")
            return False
        finally:
            conn.close()

    def get_latest_report(self, patient_id, persona):
        """
        Recuperează ultimul raport salvat pentru un pacient și o anumită personalitate (HR, Psych, Academic).
        Această metodă primește acum corect 2 argumente pentru a evita TypeError.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content FROM ai_reports 
                WHERE patient_id = ? AND persona = ?
                ORDER BY created_at DESC LIMIT 1
            """, (patient_id, persona))
            rezultat = cursor.fetchone()
            return rezultat[0] if rezultat else None
        except Exception as e:
            print(f"Eroare recuperare raport: {e}")
            return None
        finally:
            conn.close()

    def get_full_patient_data_for_export(self, patient_id):
        """Extrage toate datele asociate unui pacient pentru exportul complet în format JSON."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # 1. Datele din profilul personal
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            patient_row = cursor.fetchone()
            
            # 2. Datele din bazinul de cunoștințe holistice
            cursor.execute("SELECT * FROM holistic_knowledge WHERE patient_id = ?", (patient_id,))
            holistic_rows = cursor.fetchall()
            
            # 3. Listarea sesiunilor efectuate
            cursor.execute("SELECT * FROM sessions WHERE patient_id = ?", (patient_id,))
            session_rows = cursor.fetchall()
            
            # 4. Toate rapoartele AI arhivate
            cursor.execute("SELECT persona, content, created_at FROM ai_reports WHERE patient_id = ?", (patient_id,))
            report_rows = cursor.fetchall()
            
            return {
                "profile": patient_row,
                "holistic": holistic_rows,
                "sessions": session_rows,
                "ai_reports": report_rows
            }
        finally:
            conn.close()