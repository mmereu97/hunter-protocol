#!/usr/bin/env python3
"""
STANDALONE EXAM - FULL ENGINE
Testare Independentă cu suport complet pentru Wave 1/2/3
Rulează cu exam_package.db exportat din aplicația principală
"""
import sys
import os
import sqlite3
import json
import random
from datetime import datetime
from collections import defaultdict
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class StandaloneExam(QWidget):
    def __init__(self, db_path="exam_package.db"):
        super().__init__()
        print(f"\n{'='*60}")
        print(f"[INIT] Standalone Exam FULL ENGINE starting...")
        print(f"[INIT] DB Path: {db_path}")
        
        self.db_path = db_path
        self.session_id = None
        self.queue = []  # Coada de întrebări
        self.current_q_index = 0
        self.asked_hashes = set()  # Întrebări deja puse
        self.answers_log = {}  # {axis_id: [scores]}
        self.wave_1_done = False
        self.wave_2_done = False
        self.triggered_monsters = set()
        self.wave_counter = {1: 0, 2: 0, 3: 0}  # Contorul de întrebări per val
        self.current_wave = 1  # Valul curent
        
        # Tracking valuri
        self.current_wave = 1
        self.wave_1_count = 0
        self.wave_2_count = 0
        self.wave_3_count = 0
        self.total_questions = 0
        
        # Parametri strategie (se încarcă din DB)
        self.w1_qty = 3
        self.yellow_qty = 2
        self.red_qty = 3
        self.dev_minor = 1.0
        self.dev_major = 1.5
        
        self.setWindowTitle("Hunter Protocol - Testare Standalone FULL")
        self.setMinimumSize(900, 750)
        self.resize(1000, 850)
        self.setStyleSheet("background-color: #0b0b0b; color: #e0e0e0;")
        
        print("[INIT] Initializing UI...")
        self.init_ui()
        print("[INIT] Loading metadata...")
        self.load_metadata()
        print("[INIT] Checking for interrupted session...")
        self.check_for_resume()
        print("[INIT] Ready!")
        print(f"{'='*60}\n")
    
    def init_ui(self):
        print("[INIT_UI] Creating layout...")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Header
        self.lbl_title = QLabel("🎯 TESTARE PSIHOMETRICĂ")
        self.lbl_title.setFont(QFont("Arial", 20, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #00ff69;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        # Info Protocol
        self.lbl_protocol = QLabel()
        self.lbl_protocol.setStyleSheet("color: #82b1ff; font-size: 14px; padding: 10px;")
        self.lbl_protocol.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_protocol)
        
        btn_start = QPushButton("🚀 ÎNCEPE TESTUL")
        btn_start.setStyleSheet("""
            QPushButton {
                background: #004d40; color: #00ff69; 
                padding: 15px; font-size: 16px; font-weight: bold;
                border: 2px solid #00ff69; border-radius: 5px;
            }
            QPushButton:hover { background: #00695c; }
        """)
        btn_start.clicked.connect(self.start_test)
        layout.addWidget(btn_start)
        
        # Zona întrebări (ascunsă inițial)
        self.question_widget = QWidget()
        self.question_layout = QVBoxLayout(self.question_widget)
        
        self.lbl_progress = QLabel()
        self.lbl_progress.setStyleSheet("color: #888; font-size: 12px;")
        self.question_layout.addWidget(self.lbl_progress)
        
        self.lbl_question = QLabel()
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setMinimumHeight(70)
        self.lbl_question.setStyleSheet("""
            QLabel {
                color: white; 
                font-size: 16px; 
                font-weight: bold;
                padding: 20px; 
                background: #1a1a1a; 
                border: 2px solid #00e5ff;
                border-radius: 8px;
                margin-bottom: 15px;
            }
        """)
        self.question_layout.addWidget(self.lbl_question)
        
        self.btn_group = QButtonGroup()
        self.radio_buttons = []
        for i in range(4):
            rb = QRadioButton()
            rb.setCursor(Qt.PointingHandCursor)
            rb.setMinimumHeight(45)
            rb.setStyleSheet("""
                QRadioButton {
                    color: #e0e0e0; 
                    font-size: 14px;
                    font-weight: bold;
                    padding: 12px 12px 12px 40px;
                    spacing: 12px;
                    background: #1a1a1a;
                    border: 2px solid #333;
                    border-radius: 8px;
                    margin: 4px 0px;
                }
                QRadioButton:hover {
                    background: #252525;
                    border: 2px solid #00ff69;
                }
                QRadioButton:checked {
                    background: #1a3a1a;
                    border: 2px solid #00ff69;
                    color: #00ff69;
                }
                QRadioButton::indicator {
                    width: 24px;
                    height: 24px;
                    border: 3px solid #666;
                    border-radius: 14px;
                    background: #0b0b0b;
                    margin-left: 10px;
                }
                QRadioButton::indicator:checked {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #00ff69, stop:0.5 #00ff69, stop:1 #0b0b0b);
                    border: 3px solid #00ff69;
                }
                QRadioButton::indicator:hover {
                    border: 3px solid #00ff69;
                }
            """)
            self.btn_group.addButton(rb, i)
            self.radio_buttons.append(rb)
            self.question_layout.addWidget(rb)
        
        btn_next = QPushButton("➡️ URMĂTOAREA ÎNTREBARE")
        btn_next.setMinimumHeight(45)
        btn_next.setStyleSheet("""
            QPushButton {
                background: #1a237e; 
                color: #82b1ff;
                padding: 12px; 
                font-size: 15px; 
                font-weight: bold;
                border: 2px solid #82b1ff; 
                border-radius: 8px;
                margin-top: 15px;
            }
            QPushButton:hover { 
                background: #283593; 
                color: white;
            }
            QPushButton:pressed {
                background: #0d47a1;
            }
        """)
        btn_next.clicked.connect(self.next_question)
        self.question_layout.addWidget(btn_next)
        
        self.question_widget.hide()
        layout.addWidget(self.question_widget)
    
    def load_metadata(self):
        print("[LOAD_METADATA] Opening DB connection...")
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            print("[LOAD_METADATA] Querying meta table...")
            c.execute("SELECT protocol_name, strategy_name FROM meta")
            proto, strat = c.fetchone()
            print(f"[LOAD_METADATA] Protocol: {proto}")
            print(f"[LOAD_METADATA] Strategy: {strat}")
            self.lbl_protocol.setText(f"📝 Protocol: {proto} | 🧩 Strategie: {strat}")
            
            # Numele pacientului turnat în pachet (pachete noi). Pachetele vechi nu îl au.
            meta_cols = [r[1] for r in c.execute("PRAGMA table_info(meta)").fetchall()]
            if "patient_name" in meta_cols:
                row_name = c.execute("SELECT patient_name FROM meta").fetchone()
                self.candidate_name = row_name[0] if row_name and row_name[0] else "Candidat"
            else:
                self.candidate_name = "Candidat"
            print(f"[LOAD_METADATA] Candidat: {self.candidate_name}")
            
            # Încărcăm parametrii strategiei
            c.execute("SELECT w1_base_qty, yellow_extra_qty, red_extra_qty, dev_threshold_minor, dev_threshold_major FROM exam_strategies LIMIT 1")
            row = c.fetchone()
            if row:
                self.w1_qty, self.yellow_qty, self.red_qty, self.dev_minor, self.dev_major = row
                print(f"[LOAD_METADATA] Strategy params: W1={self.w1_qty}, Y={self.yellow_qty}, R={self.red_qty}, dev_minor={self.dev_minor}, dev_major={self.dev_major}")
            else:
                print("[LOAD_METADATA] WARNING: No strategy found, using defaults")
            
            conn.close()
            print("[LOAD_METADATA] Success!")
        except Exception as e:
            print(f"[LOAD_METADATA] ERROR: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Eroare", f"DB invalid: {e}")
            sys.exit(1)
    
    def _ensure_state_table(self, c):
        c.execute("""CREATE TABLE IF NOT EXISTS exam_state (
            session_id INTEGER PRIMARY KEY,
            state_json TEXT,
            updated_at TEXT
        )""")

    def save_state(self):
        """Salvează starea completă a examenului în pachet (rezistent la pană de curent)."""
        if self.session_id is None:
            return
        state = {
            "queue": self.queue,
            "current_q_index": self.current_q_index,
            "asked_hashes": list(self.asked_hashes),
            "answers_log": {str(k): v for k, v in self.answers_log.items()},
            "wave_1_done": self.wave_1_done,
            "wave_2_done": self.wave_2_done,
            "current_wave": self.current_wave,
            "triggered_monsters": list(self.triggered_monsters),
            "wave_counter": {str(k): v for k, v in self.wave_counter.items()},
            "wave_1_count": self.wave_1_count,
            "wave_2_count": self.wave_2_count,
            "wave_3_count": self.wave_3_count,
            "total_questions": self.total_questions,
        }
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            self._ensure_state_table(c)
            c.execute("INSERT OR REPLACE INTO exam_state (session_id, state_json, updated_at) VALUES (?,?,?)",
                      (self.session_id, json.dumps(state), datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SAVE_STATE] WARNING: {e}")

    def check_for_resume(self):
        """La pornire: dacă există un test întrerupt, oferă reluarea de unde a rămas."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            tbl = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_state'").fetchone()
            if not tbl:
                conn.close()
                return
            row = c.execute("""SELECT es.session_id, es.state_json
                               FROM exam_state es
                               JOIN sessions s ON es.session_id = s.id
                               WHERE s.status='In Progress'
                               ORDER BY es.updated_at DESC LIMIT 1""").fetchone()
            conn.close()
            if not row:
                return
            resp = QMessageBox.question(self, "Test întrerupt",
                "Ați întrerupt un test neterminat.\n\nDoriți să continuați de unde ați rămas?",
                QMessageBox.Yes | QMessageBox.No)
            if resp == QMessageBox.Yes:
                self.resume_test(row[0], row[1])
            else:
                self._discard_session(row[0])
        except Exception as e:
            print(f"[RESUME] Check failed: {e}")

    def resume_test(self, session_id, state_json):
        """Reîncarcă starea salvată și continuă de la întrebarea curentă."""
        state = json.loads(state_json)
        self.session_id = session_id
        self.queue = [tuple(q) for q in state["queue"]]
        self.asked_hashes = set(state["asked_hashes"])
        self.wave_1_done = state["wave_1_done"]
        self.wave_2_done = state["wave_2_done"]
        self.current_wave = state["current_wave"]
        self.triggered_monsters = set(state["triggered_monsters"])
        self.wave_counter = {int(k): v for k, v in state["wave_counter"].items()}
        self.wave_1_count = state.get("wave_1_count", 0)
        self.wave_2_count = state.get("wave_2_count", 0)
        self.wave_3_count = state.get("wave_3_count", 0)
        self.total_questions = state.get("total_questions", len(self.queue))

        # Sursa de adevăr pentru răspunsuri = session_responses (rezistent la lag de stare)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT axis_id, score_snapshot FROM session_responses WHERE session_id=? ORDER BY id", (session_id,))
        rows = c.fetchall()
        conn.close()
        self.answers_log = {int(k): [] for k in state["answers_log"].keys()}
        for axis_id, score in rows:
            self.answers_log.setdefault(axis_id, []).append(score)
        self.current_q_index = len(rows)  # câte întrebări a răspuns efectiv
        print(f"[RESUME] Reluare sesiune {session_id}: {self.current_q_index} răspunsuri date, continui de acolo")

        # Ascundem intro și arătăm întrebările
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and "ÎNCEPE" in widget.text():
                widget.hide()
                break
        self.question_widget.show()
        self.load_question()

    def _discard_session(self, session_id):
        """Șterge o sesiune întreruptă (la alegerea „Începe de la zero")."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM session_responses WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM session_audit WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM exam_state WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            conn.commit()
            conn.close()
            print(f"[RESUME] Sesiune întreruptă {session_id} ștearsă")
        except Exception as e:
            print(f"[RESUME] Discard failed: {e}")

    def start_test(self):
        print("\n[START_TEST] Called")
        name = getattr(self, "candidate_name", "Candidat")
        print(f"[START_TEST] Name: {name}")
        
        # Creăm sesiunea
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # ȘTERGEM sesiunile anterioare pentru același candidat
        print(f"[START_TEST] Checking for previous sessions by '{name}'...")
        c.execute("SELECT id FROM sessions WHERE candidate_name=?", (name,))
        old_sessions = [row[0] for row in c.fetchall()]
        
        if old_sessions:
            print(f"[START_TEST] Found {len(old_sessions)} previous session(s): {old_sessions}")
            print(f"[START_TEST] Deleting old sessions to keep only the latest...")
            
            for old_sid in old_sessions:
                # Ștergem răspunsurile
                c.execute("DELETE FROM session_responses WHERE session_id=?", (old_sid,))
                deleted_responses = c.rowcount
                print(f"[START_TEST]   Session {old_sid}: Deleted {deleted_responses} responses")
                
                # Ștergem audit trail
                c.execute("DELETE FROM session_audit WHERE session_id=?", (old_sid,))
                deleted_audit = c.rowcount
                print(f"[START_TEST]   Session {old_sid}: Deleted {deleted_audit} audit entries")
                
                # Ștergem sesiunea
                c.execute("DELETE FROM sessions WHERE id=?", (old_sid,))
                print(f"[START_TEST]   Session {old_sid}: Deleted")
            
            conn.commit()
            print(f"[START_TEST] Cleanup complete - all previous sessions removed")
        else:
            print(f"[START_TEST] No previous sessions found for '{name}'")
        
        c.execute("SELECT template_id, strategy_id FROM meta")
        tid, sid = c.fetchone()
        print(f"[START_TEST] Template ID: {tid}, Strategy ID: {sid}")
        
        c.execute("INSERT INTO sessions (candidate_name, template_id, strategy_id, date_taken, status) VALUES (?,?,?,?,?)",
                 (name, tid, sid, datetime.now().isoformat(), "In Progress"))
        self.session_id = c.lastrowid
        print(f"[START_TEST] Created NEW session ID: {self.session_id}")
        
        # Încărcăm coada WAVE 1
        c.execute("SELECT id FROM axes ORDER BY id")
        axes = [r[0] for r in c.fetchall()]
        print(f"[START_TEST] Found {len(axes)} axes: {axes}")
        
        for aid in axes:
            c.execute("SELECT version_hash, axis_id, text_content FROM questions_bank WHERE axis_id=? AND wave_target=1 ORDER BY id LIMIT ?", (aid, self.w1_qty))
            questions = c.fetchall()
            print(f"[START_TEST] Axis {aid}: {len(questions)} W1 questions")
            for q in questions:
                self.queue.append(q)
                self.asked_hashes.add(q[0])
            self.answers_log[aid] = []
        
        # AMESTECĂM întrebările
        random.shuffle(self.queue)
        print(f"[START_TEST] Queue shuffled")
        
        self.wave_1_count = len(self.queue)
        self.total_questions = self.wave_1_count
        print(f"[START_TEST] Wave 1 queue size: {self.wave_1_count}")
        
        # Logăm decizia
        c.execute("INSERT INTO session_audit (session_id, axis_id, wave_target, decision_type, explanation) VALUES (?,?,?,?,?)",
                 (self.session_id, 0, 1, "START", f"Sesiune începută - Wave 1 cu {self.w1_qty} întrebări/axă"))
        
        conn.commit()
        conn.close()
        
        # Ascundem intro
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and "ÎNCEPE" in widget.text():
                widget.hide()
                print("[START_TEST] Hidden start button")
                break
        
        # Arătăm întrebările
        self.question_widget.show()
        print("[START_TEST] Showing question widget")
        self.load_question()
    
    def load_question(self):
        print(f"\n[LOAD_QUESTION] Index: {self.current_q_index}/{len(self.queue)}")
        
        if self.current_q_index >= len(self.queue):
            print("[LOAD_QUESTION] Queue exhausted - checking for next wave")
            self.check_and_inject_next_wave()
            return
        
        # Salvăm starea curentă (rezistență la întrerupere / pană de curent)
        self.save_state()
        
        q_hash, axis_id, q_text = self.queue[self.current_q_index]
        print(f"[LOAD_QUESTION] Question: {q_hash}, Axis: {axis_id}")
        print(f"[LOAD_QUESTION] Text: {q_text[:50]}...")
        
        # Numele valurilor
        wave_names = {
            1: "Screening (Evaluare Standard)",
            2: "Clarificare (Investigație Rigoare)", 
            3: "Deep Dive (Analiză Monștri și Riscuri)"
        }
        
        # Incrementăm contorul pentru valul curent
        self.wave_counter[self.current_wave] += 1
        current_position_in_wave = self.wave_counter[self.current_wave]
        
        # Calculăm câte întrebări mai sunt în coadă (estimare simplificată)
        # Total = poziție curentă + întrebări rămase
        remaining_questions = len(self.queue) - self.current_q_index - 1
        total_in_wave = current_position_in_wave + remaining_questions
        
        # Afișare identică cu programul principal
        wave_name = wave_names.get(self.current_wave, "Analiză")
        wave_display = f"VAL {self.current_wave} din 3 ({wave_name})"
        progress_display = f"Întrebarea {current_position_in_wave} din {total_in_wave}"
        
        self.lbl_progress.setText(f"{wave_display} | {progress_display}")
        self.lbl_question.setText(q_text)
        
        # Încărcăm opțiunile
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash=? ORDER BY option_index", (q_hash,))
        options = c.fetchall()
        conn.close()
        
        print(f"[LOAD_QUESTION] Found {len(options)} options")
        
        import re
        
        # Curățăm opțiunile și le amestecăm
        cleaned_options = []
        for opt_idx, opt_text, score in options:
            clean = re.sub(r'^[A-D]\)\s*', '', opt_text)
            cleaned_options.append((opt_idx, clean, score))
        
        # AMESTECĂM opțiunile
        random.shuffle(cleaned_options)
        print(f"[LOAD_QUESTION] Options shuffled")
        
        # Resetăm toate butoanele înainte
        self.btn_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
            rb.hide()
        self.btn_group.setExclusive(True)
        
        # Afișăm opțiunile FĂRĂ litere A/B/C/D
        for i, (opt_idx, clean_text, score) in enumerate(cleaned_options):
            print(f"[LOAD_QUESTION] Option {i}: score={score}, text={clean_text[:30]}...")
            
            self.radio_buttons[i].setText(clean_text)  # Fără prefix A) B) etc.
            self.radio_buttons[i].setProperty("score", score)
            self.radio_buttons[i].setProperty("axis_id", axis_id)
            self.radio_buttons[i].setProperty("q_hash", q_hash)
            self.radio_buttons[i].setProperty("opt_idx", opt_idx)
            self.radio_buttons[i].show()
            self.radio_buttons[i].setEnabled(True)
    
    def next_question(self):
        print("\n[NEXT_QUESTION] Called")
        selected = self.btn_group.checkedButton()
        
        if not selected:
            print("[NEXT_QUESTION] NO SELECTION - showing warning")
            QMessageBox.warning(self, "Atenție", "Selectează un răspuns!")
            return
        
        # Salvăm răspunsul
        score = selected.property("score")
        axis_id = selected.property("axis_id")
        q_hash = selected.property("q_hash")
        opt_idx_raw = selected.property("opt_idx")
        
        # Convertim literele A/B/C/D la 0/1/2/3 dacă e necesar
        if isinstance(opt_idx_raw, str):
            letter_to_num = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            answer_idx = letter_to_num.get(opt_idx_raw, 0)
        else:
            answer_idx = opt_idx_raw
        
        print(f"[NEXT_QUESTION] Selected: idx={opt_idx_raw} -> {answer_idx}, score={score}, axis={axis_id}")
        
        # Salvăm în DB
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO session_responses (session_id, question_hash, axis_id, answer_chosen, score_snapshot) VALUES (?,?,?,?,?)",
                 (self.session_id, q_hash, axis_id, answer_idx, score))
        conn.commit()
        conn.close()
        
        # Adăugăm în log
        self.answers_log[axis_id].append(score)
        print(f"[NEXT_QUESTION] Axis {axis_id} scores: {self.answers_log[axis_id]}")
        
        self.current_q_index += 1
        self.load_question()
    
    def check_and_inject_next_wave(self):
        print("\n[CHECK_WAVE] Checking for next wave injection...")
        
        if not self.wave_1_done:
            print("[CHECK_WAVE] Wave 1 complete - analyzing for Wave 2")
            self.wave_1_done = True
            self.current_wave = 2
            
            old_queue_size = len(self.queue)
            self.inject_wave_2()
            self.wave_2_count = len(self.queue) - old_queue_size
            self.total_questions = len(self.queue)
            
            print(f"[CHECK_WAVE] Wave 2 added {self.wave_2_count} questions")
            
            if len(self.queue) > self.current_q_index:
                self.load_question()
                return
        
        if not self.wave_2_done:
            print("[CHECK_WAVE] Wave 2 complete - analyzing for Wave 3 (monsters)")
            self.wave_2_done = True
            self.current_wave = 3
            
            old_queue_size = len(self.queue)
            self.inject_wave_3()
            self.wave_3_count = len(self.queue) - old_queue_size
            self.total_questions = len(self.queue)
            
            print(f"[CHECK_WAVE] Wave 3 added {self.wave_3_count} questions")
            
            if len(self.queue) > self.current_q_index:
                self.load_question()
                return
        
        # Totul complet
        print("[CHECK_WAVE] All waves complete - finishing test")
        self.finish_test()
    
    def inject_wave_2(self):
        """Analizează contradicții și devieri, injectează Wave 2."""
        print("\n[WAVE2] Starting Wave 2 analysis...")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Obținem normele pentru fiecare axă
        c.execute("SELECT id, norm_mean, norm_std_dev FROM axes")
        norms = {row[0]: (row[1] or 50, row[2] or 15) for row in c.fetchall()}
        
        for axis_id, scores in self.answers_log.items():
            if len(scores) == 0:
                continue
            
            print(f"[WAVE2] Analyzing axis {axis_id}: scores={scores}")
            
            # 1. Detectăm contradicții (secvențe 0-100-0 sau 100-0-100)
            contradictions = 0
            for i in range(len(scores) - 1):
                diff = abs(scores[i] - scores[i+1])
                if diff >= 80:
                    contradictions += 1
            
            print(f"[WAVE2] Axis {axis_id}: {contradictions} contradictions")
            
            # 2. Calculăm devierea față de normă (în PUNCTE, nu sigma!)
            avg_score = sum(scores) / len(scores)
            norm_mean, norm_sd = norms.get(axis_id, (50, 15))
            deviation_points = abs(avg_score - norm_mean)
            deviation_sigma = deviation_points / norm_sd if norm_sd > 0 else 0
            
            print(f"[WAVE2] Axis {axis_id}: avg={avg_score:.1f}, norm={norm_mean}, diff={deviation_points:.1f} pts ({deviation_sigma:.2f}σ)")
            
            # 3. Decidem câte întrebări să adăugăm
            extra_qty = 0
            reason = ""
            
            print(f"[WAVE2] Axis {axis_id}: Checking thresholds - contradictions={contradictions}, deviation_points={deviation_points:.1f}, dev_minor={self.dev_minor}, dev_major={self.dev_major}")
            
            if contradictions >= 2:
                extra_qty = self.yellow_qty
                reason = f"CONTRADICȚII: {contradictions} oscilații majore"
            elif deviation_points >= self.dev_major:
                extra_qty = self.red_qty
                reason = f"DEVIAȚIE MAJORĂ: {deviation_points:.1f} puncte (normă: {norm_mean})"
            elif deviation_points >= self.dev_minor:
                extra_qty = self.yellow_qty
                reason = f"DEVIAȚIE MINORĂ: {deviation_points:.1f} puncte"
            
            if extra_qty > 0:
                print(f"[WAVE2] Axis {axis_id}: Injecting {extra_qty} questions - {reason}")
                
                # Logăm decizia
                c.execute("INSERT INTO session_audit (session_id, axis_id, wave_target, decision_type, explanation) VALUES (?,?,?,?,?)",
                         (self.session_id, axis_id, 2, "WAVE2_INJECT", reason))
                
                # Marcăm poziția de start pentru amestec
                start_idx = len(self.queue)
                
                # Adăugăm întrebări Wave 2
                c.execute("""SELECT version_hash, axis_id, text_content 
                            FROM questions_bank 
                            WHERE axis_id=? AND wave_target=2 AND version_hash NOT IN ({})
                            ORDER BY id LIMIT ?""".format(','.join('?' * len(self.asked_hashes))),
                         (axis_id, *self.asked_hashes, extra_qty))
                
                added = 0
                for q in c.fetchall():
                    self.queue.append(q)
                    self.asked_hashes.add(q[0])
                    added += 1
                    print(f"[WAVE2] Added question: {q[0]}")
                
                # Amestecăm întrebările nou adăugate
                if added > 0:
                    wave2_subset = self.queue[start_idx:]
                    random.shuffle(wave2_subset)
                    self.queue[start_idx:] = wave2_subset
                    print(f"[WAVE2] Shuffled {added} new questions")
        
        conn.commit()
        conn.close()
        print(f"[WAVE2] Complete - new queue size: {len(self.queue)}")
    
    def inject_wave_3(self):
        """Verifică condițiile de sinergie și injectează monștri."""
        print("\n[WAVE3] Starting Wave 3 analysis (monsters)...")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculăm scorurile finale pentru fiecare axă
        axis_scores = {}
        for axis_id, scores in self.answers_log.items():
            if len(scores) > 0:
                axis_scores[axis_id] = sum(scores) / len(scores)
        
        print(f"[WAVE3] Axis scores: {axis_scores}")
        
        # Încărcăm regulile de sinergie
        c.execute("SELECT monster_axis_id, trigger_axis_id, operator, threshold FROM synergy_rules")
        rules = c.fetchall()
        
        print(f"[WAVE3] Found {len(rules)} synergy rules")
        
        # Grupăm regulile pe monștri
        monster_rules = defaultdict(list)
        for monster_id, trigger_id, op, thresh in rules:
            monster_rules[monster_id].append((trigger_id, op, thresh))
        
        # Verificăm fiecare monstru
        for monster_id, conditions in monster_rules.items():
            if monster_id in self.triggered_monsters:
                continue
            
            print(f"[WAVE3] Checking monster {monster_id}: {len(conditions)} conditions")
            all_satisfied = True
            
            for trigger_id, operator, threshold in conditions:
                if trigger_id not in axis_scores:
                    all_satisfied = False
                    break
                
                score = axis_scores[trigger_id]
                satisfied = False
                
                if operator == '>': satisfied = score > threshold
                elif operator == '<': satisfied = score < threshold
                elif operator == '>=': satisfied = score >= threshold
                elif operator == '<=': satisfied = score <= threshold
                
                print(f"[WAVE3]   Trigger {trigger_id}: {score} {operator} {threshold} = {satisfied}")
                
                if not satisfied:
                    all_satisfied = False
                    break
            
            if all_satisfied:
                print(f"[WAVE3] 🚨 MONSTER TRIGGERED: {monster_id}")
                self.triggered_monsters.add(monster_id)
                
                # Logăm
                c.execute("INSERT INTO session_audit (session_id, axis_id, wave_target, decision_type, explanation) VALUES (?,?,?,?,?)",
                         (self.session_id, monster_id, 3, "MONSTER_TRIGGER", f"Condițiile de sinergie îndeplinite"))
                
                # Marcăm poziția de start pentru amestec
                start_idx = len(self.queue)
                
                # Adăugăm întrebări pentru monstru
                c.execute("""SELECT version_hash, axis_id, text_content 
                            FROM questions_bank 
                            WHERE axis_id=? AND wave_target=3 AND version_hash NOT IN ({})
                            ORDER BY id LIMIT ?""".format(','.join('?' * len(self.asked_hashes))),
                         (monster_id, *self.asked_hashes, self.w1_qty))
                
                added = 0
                for q in c.fetchall():
                    self.queue.append(q)
                    self.asked_hashes.add(q[0])
                    added += 1
                    print(f"[WAVE3] Added monster question: {q[0]}")
                
                # Amestecăm întrebările nou adăugate
                if added > 0:
                    wave3_subset = self.queue[start_idx:]
                    random.shuffle(wave3_subset)
                    self.queue[start_idx:] = wave3_subset
                    print(f"[WAVE3] Shuffled {added} new questions")
        
        conn.commit()
        conn.close()
        print(f"[WAVE3] Complete - {len(self.triggered_monsters)} monsters triggered")
    
    def finish_test(self):
        print("\n[FINISH_TEST] Called")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Marcăm sesiunea ca completată (necesar pentru import în aplicație)
        c.execute("UPDATE sessions SET status='Completed' WHERE id=?", (self.session_id,))
        conn.commit()
        conn.close()
        print(f"[FINISH_TEST] Session {self.session_id} marked as completed")

        # Mesaj NEUTRU pentru cel testat — fără scoruri, fără interpretare.
        file_name = os.path.basename(self.db_path)
        msg = QMessageBox(self)
        msg.setWindowTitle("Test finalizat")
        msg.setText(
            "Ați finalizat testul. Vă mulțumim!\n\n"
            f"Trimiteți fișierul „{file_name}” persoanei care v-a dat testul, "
            "pentru evaluare."
        )
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0b0b0b;
                color: #e0e0e0;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                min-width: 360px;
            }
            QMessageBox QPushButton {
                background-color: #1a237e;
                color: #82b1ff;
                border: 2px solid #82b1ff;
                padding: 10px 20px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #283593;
            }
        """)
        msg.exec()

        print("[FINISH_TEST] Closing application")
        self.close()

if __name__ == "__main__":
    # Calea către folderul programului: lângă .exe (când e împachetat) sau lângă script.
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Implicit caută exam_package.db lângă program; acceptă și o cale dată ca argument.
    pkg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "exam_package.db")

    app = QApplication(sys.argv)

    if not os.path.exists(pkg_path):
        QMessageBox.critical(None, "Pachet lipsă",
            f"Nu am găsit fișierul de testare:\n{pkg_path}\n\n"
            "Pune exam_package.db în același folder cu programul.")
        sys.exit(1)

    window = StandaloneExam(db_path=pkg_path)
    window.show()
    sys.exit(app.exec())
