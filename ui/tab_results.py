import sqlite3
import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QScrollArea, QFrame, QPushButton, QSplitter, QTextEdit, QFileDialog, QMessageBox, QRadioButton, QApplication, QButtonGroup
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from config import Config
from logger import log
from ai_agents.profiler_agent import ProfilerAgent
from ui.tab_patients import ReportWindow # Importăm fereastra stilizată creată anterior

# ==========================================
# 🎨 STIL CYBERPUNK (RESULTS)
# ==========================================
RESULTS_STYLE = """
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    QComboBox {
        background-color: #1a1a1a;
        color: #00e5ff;
        border: 1px solid #444;
        padding: 5px;
        font-weight: bold;
    }
    QComboBox QAbstractItemView {
        background-color: #1a1a1a;
        color: white;
        selection-background-color: #00e5ff;
    }
    QScrollArea { border: none; background-color: #0b0b0b; }
    QScrollBar:vertical { background: #111; width: 8px; }
    QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
    
    QPushButton {
        background-color: #1f1f1f;
        color: #aaa;
        border: 1px solid #333;
        padding: 10px;
        text-align: left;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #2a2a2a;
        color: white;
        border: 1px solid #00e5ff;
    }
    QPushButton:pressed { background-color: #004d40; }

    /* ZONA DE TRANSCRIPT */
    QTextEdit#Transcript {
        background-color: #0f0f0f;
        color: #00ff00; /* Text stil terminal vechi */
        font-family: 'Consolas', monospace;
        font-size: 13px;
        border: 1px solid #333;
        padding: 10px;
    }
    
    /* RADIO BUTTONS */
    QRadioButton { color: #888; spacing: 5px; }
    QRadioButton::indicator { width: 14px; height: 14px; border: 1px solid #555; border-radius: 7px; background: #111; }
    QRadioButton::indicator:checked { background: #00e5ff; border: 1px solid #00e5ff; }
    QRadioButton:checked { color: #00e5ff; font-weight: bold; }
"""

# ==========================================
# 🎨 WIDGET CUSTOM: RIGLA OGLINDĂ
# ==========================================
class PsychometricRuler(QWidget):
    def __init__(self, axis_name, left_pole, right_pole, score, confidence, norm_mean=50, norm_std_dev=15, questions_used=0, questions_total=0):
        super().__init__()
        self.setFixedHeight(45) 
        
        self.axis_name = axis_name
        self.left_pole = left_pole
        self.right_pole = right_pole
        self.raw_score = score
        self.confidence = confidence 
        self.questions_used = questions_used
        self.questions_total = questions_total 
        
        self.val_left = 100 - score
        self.val_right = score
        self.norm_mean = norm_mean
        self.norm_sd = norm_std_dev
        
        self.dim_color = QColor("#444444") 
        self.bg_track_color = QColor("#222222")
        self.norm_zone_color = QColor(0, 229, 255, 30) 

        dev = abs(score - norm_mean)
        if dev > (2 * norm_std_dev): self.active_color = QColor("#ff0055") 
        elif dev > norm_std_dev: self.active_color = QColor("#ffcc00") 
        else: self.active_color = QColor("#00ff69") 

        if confidence >= 80: self.acc_color = QColor("#00ff69")
        elif confidence >= 50: self.acc_color = QColor("#ffcc00")
        else: self.acc_color = QColor("#ff0055")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height(); cy = h / 2
        
        w_name = 180; w_side = 180; w_badge = 120; margin = 10
        
        rect_name = QRect(margin, 0, w_name, h)
        rect_left = QRect(w_name + margin, 0, w_side, h)
        x_ruler_start = w_name + w_side + (margin*2)
        x_ruler_end = w - w_side - w_badge - (margin*2)
        ruler_width = x_ruler_end - x_ruler_start
        if ruler_width < 30: ruler_width = 30
        rect_right = QRect(x_ruler_end + margin, 0, w_side, h)
        rect_badge = QRect(w - w_badge - margin, 8, w_badge, h - 16)

        is_left = self.raw_score <= 50
        font_main = QFont("Segoe UI", 10, QFont.Bold)
        font_dim = QFont("Segoe UI", 9, QFont.Normal)
        
        p.setPen(QColor("white")); p.setFont(font_main)
        p.drawText(rect_name, Qt.AlignVCenter | Qt.AlignLeft, self.axis_name)
        
        str_left = f"{self.left_pole}  {self.val_left}%"
        p.setPen(self.active_color if is_left else self.dim_color)
        p.setFont(font_main if is_left else font_dim)
        p.drawText(rect_left, Qt.AlignVCenter | Qt.AlignRight, str_left)
        
        str_right = f"{self.val_right}%  {self.right_pole}"
        p.setPen(self.active_color if not is_left else self.dim_color)
        p.setFont(font_main if not is_left else font_dim)
        p.drawText(rect_right, Qt.AlignVCenter | Qt.AlignLeft, str_right)
        
        track_y = int(cy)
        p.setPen(QPen(self.bg_track_color, 2))
        p.drawLine(x_ruler_start, track_y, x_ruler_end, track_y)
        p.setPen(QPen(QColor("#333"), 1))
        for i in range(11):
            tx = x_ruler_start + (i * ruler_width / 10)
            p.drawLine(int(tx), track_y - 3, int(tx), track_y + 3)
            
        mx = x_ruler_start + (ruler_width / 2)
        p.setPen(QPen(QColor("#555"), 2))
        p.drawLine(int(mx), track_y - 5, int(mx), track_y + 5)
        
        ns = max(0, self.norm_mean - self.norm_sd)
        ne = min(100, self.norm_mean + self.norm_sd)
        nx = x_ruler_start + (ns / 100 * ruler_width)
        nw = (ne - ns) / 100 * ruler_width
        p.setPen(Qt.NoPen); p.setBrush(self.norm_zone_color)
        p.drawRect(int(nx), track_y - 4, int(nw), 9)
        
        bx = x_ruler_start + (self.raw_score / 100 * ruler_width)
        p.setBrush(QColor(self.active_color.red(), self.active_color.green(), self.active_color.blue(), 60))
        p.drawEllipse(int(bx - 10), int(track_y - 10), 20, 20)
        p.setBrush(self.active_color)
        p.drawEllipse(int(bx - 6), int(track_y - 6), 12, 12)
        
        p.setBrush(QColor(self.acc_color.red(), self.acc_color.green(), self.acc_color.blue(), 30))
        p.setPen(QPen(self.acc_color, 1))
        p.drawRoundedRect(rect_badge, 4, 4)
        p.setFont(QFont("Consolas", 10, QFont.Bold)); p.setPen(self.acc_color)
        text_badge = f"{self.confidence}% [{self.questions_used}/{self.questions_total}]"
        p.drawText(rect_badge, Qt.AlignCenter, text_badge)

class MonsterRow(QWidget):
    """Rând de detecție pentru un monstru declanșat (sinergie pe scoruri finale)."""
    def __init__(self, monster_name, conditions_text):
        super().__init__()
        self.setFixedHeight(45)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        lbl_name = QLabel(f"👹 {monster_name}")
        lbl_name.setStyleSheet("color: #ff0055; font-weight: bold; font-size: 11pt;")
        lbl_name.setFixedWidth(220)

        lbl_cond = QLabel(conditions_text)
        lbl_cond.setStyleSheet("color: #ff8899; font-size: 9pt;")

        lbl_badge = QLabel("RISC DETECTAT")
        lbl_badge.setAlignment(Qt.AlignCenter)
        lbl_badge.setFixedWidth(140)
        lbl_badge.setStyleSheet(
            "color: #ff0055; font-weight: bold; "
            "border: 1px solid #ff0055; border-radius: 4px; padding: 4px 8px;"
        )

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_cond, 1)
        layout.addWidget(lbl_badge)


class ResultsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = Config.DB_NAME
        self._ensure_audit_table()
        self.setStyleSheet(RESULTS_STYLE)
        self.current_transcript = "" 
        self.current_session_info = "" 
        self.current_session_id = None
        self.setup_ui()

    def _ensure_audit_table(self):
        """Garantează tabelul session_audit (schemă canonică) ca toate operațiile
        — ștergere, transcript, import — să îl găsească."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""CREATE TABLE IF NOT EXISTS session_audit (
                id INTEGER PRIMARY KEY,
                session_id INTEGER, axis_id INTEGER, wave INTEGER,
                decision_type TEXT, explanation TEXT,
                question_text TEXT, question_hash TEXT
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[TAB6] WARNING: nu am putut asigura session_audit: {e}")

    def set_active_patient(self, patient_id, from_sync=False):
        """Metodă integrală care forțează Tabul 6 să comute pe un anumit pacient."""
        print(f"[TAB6] set_active_patient({patient_id}, from_sync={from_sync})")
        
        # 1. Împrospătăm lista de pacienți din dropdown pentru a fi siguri că avem date noi
        self.refresh_patients()
        
        # 2. Căutăm în dropdown poziția (indexul) ID-ului primit
        index_in_combo = self.cmb_patient_select.findData(patient_id)
        
        if index_in_combo >= 0:
            # Blocăm semnalele temporar pentru a face o singură încărcare curată
            self.cmb_patient_select.blockSignals(True)
            self.cmb_patient_select.setCurrentIndex(index_in_combo)
            self.cmb_patient_select.blockSignals(False)
            
            # 3. Forțăm încărcarea sesiunilor pentru acest pacient
            log("ui", f"Tab Rezultate: Încărcare automată istoric pentru subiectul ID {patient_id}")
            
            # Doar dacă vine din SYNC blochează propagarea (evită loop infinit)
            if from_sync:
                self._in_sync_update = True
                self.load_sessions_for_patient()
                self._in_sync_update = False
            else:
                # Dacă USER selectează direct → permite sincronizarea
                self.load_sessions_for_patient()
        else:
            log("sys", f"❌ Eroare Sincronizare: ID-ul {patient_id} nu a fost găsit în lista de rezultate.")

    def showEvent(self, event):
        """AUTO-REFRESH"""
        current_pid = self.cmb_patient_select.currentData()
        
        # RESTAURARE STARE: Dacă nu avem selecție, restaurăm din settings
        if not current_pid:
            from logic.settings_manager import SettingsManager
            settings = SettingsManager.load_settings()
            current_pid = settings.get("last_selected_patient_id")
            print(f"[TAB6 showEvent] Restoring last patient from settings: {current_pid}")
        
        self.refresh_patients()
        if current_pid:
            index = self.cmb_patient_select.findData(current_pid)
            if index >= 0:
                self.cmb_patient_select.setCurrentIndex(index)
                self.load_sessions_for_patient()
        super().showEvent(event)

    def setup_ui(self):
        # Layout-ul principal al tab-ului de rezultate
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        
        # Splitter-ul orizontal care separă Istoricul (stânga) de Vizualizarea grafică (dreapta)
        self.splitter_principal_orizontal = QSplitter(Qt.Horizontal)

        # =====================================================================
        # PANOU STÂNGA: ISTORIC SESIUNI
        # =====================================================================
        self.panou_stanga_istoric = QFrame()
        self.layout_stanga_istoric = QVBoxLayout(self.panou_stanga_istoric)
        self.layout_stanga_istoric.setContentsMargins(10, 10, 5, 10)
        
        self.label_titlu_istoric = QLabel("📜 ISTORIC SESIUNI")
        self.layout_stanga_istoric.addWidget(self.label_titlu_istoric)
        
        # Dropdown pentru selectarea pacientului
        self.cmb_patient_select = QComboBox()
        self.cmb_patient_select.currentIndexChanged.connect(self.load_sessions_for_patient)
        self.layout_stanga_istoric.addWidget(self.cmb_patient_select)
        
        # Zona de scroll pentru lista de sesiuni
        self.scroll_istoric_sesiuni = QScrollArea()
        self.scroll_istoric_sesiuni.setWidgetResizable(True)
        self.container_lista_sesiuni = QWidget()
        self.session_layout = QVBoxLayout(self.container_lista_sesiuni) # Folosim numele session_layout cerut de logica existenta
        self.session_layout.setAlignment(Qt.AlignTop)
        self.scroll_istoric_sesiuni.setWidget(self.container_lista_sesiuni)
        self.layout_stanga_istoric.addWidget(self.scroll_istoric_sesiuni)
        
        # =====================================================================
        # PANOU DREAPTA: ANALIZĂ ȘI GRAFICE (SPLITTER VERTICAL)
        # =====================================================================
        self.splitter_dreapta_vertical = QSplitter(Qt.Vertical)
        
        # --- SUB-PANOU SUS: VIZUALIZARE GRAFICĂ ȘI AI ---
        self.container_sus_grafice = QWidget()
        self.layout_sus_grafice = QVBoxLayout(self.container_sus_grafice)
        self.layout_sus_grafice.setContentsMargins(5, 10, 10, 5)
        
        self.lbl_header = QLabel("REZULTATELE ANALIZEI")
        self.lbl_header.setStyleSheet("font-size: 20px; color: #00e5ff; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 10px;")
        self.layout_sus_grafice.addWidget(self.lbl_header)

        # ---------------------------------------------------------------------
        # BLOC NOU: CONTROL AI PENTRU ANALIZA SESIUNII (Punctul 1 solicitat)
        # ---------------------------------------------------------------------
        self.panou_control_ai_sesiune = QFrame()
        self.panou_control_ai_sesiune.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a; 
                border: 1px solid #4a148c; 
                border-radius: 8px; 
                margin-top: 5px;
                margin-bottom: 5px;
            }
        """)
        self.layout_ai_orizontal = QHBoxLayout(self.panou_control_ai_sesiune)
        self.layout_ai_orizontal.setContentsMargins(10, 10, 10, 10)
        
        # Secțiune verticală pentru instrucțiune și selecție persona
        self.layout_ai_selectie_vertical = QVBoxLayout()
        self.label_ai_instructiune = QLabel("🧠 ANALIZĂ SESIUNE SPECIFICĂ (PERSONA):")
        self.label_ai_instructiune.setStyleSheet("color: #e040fb; font-weight: bold; border: none;")
        self.layout_ai_selectie_vertical.addWidget(self.label_ai_instructiune)
        
        self.cmb_ai_persona_results = QComboBox()
        self.cmb_ai_persona_results.addItems(["HR (Resurse Umane)", "Psych (Psiholog Clinician)", "Academic (Psihiatru/Cercetător)"])
        self.cmb_ai_persona_results.setStyleSheet("background-color: #000; color: #00e5ff; border: 1px solid #444;")
        self.layout_ai_selectie_vertical.addWidget(self.cmb_ai_persona_results)
        
        self.layout_ai_orizontal.addLayout(self.layout_ai_selectie_vertical, 1)

        # Butonul de generare raport AI pentru sesiunea curentă
        self.btn_ai = QPushButton("🧠 GENEREAZĂ INTERPRETARE AI")
        self.btn_ai.setStyleSheet("""
            QPushButton {
                background-color: #4a148c; 
                color: #e040fb; 
                padding: 15px; 
                font-weight: bold; 
                border: 1px solid #e040fb;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5e1fb0;
                color: white;
            }
        """)
        # Conectăm butonul la metoda de analiză individuală pe sesiune
        self.btn_ai.clicked.connect(self.run_session_ai_analysis)
        self.layout_ai_orizontal.addWidget(self.btn_ai, 1)
        
        # Adăugăm panoul AI în layout-ul de sus
        self.layout_sus_grafice.addWidget(self.panou_control_ai_sesiune)
        # ---------------------------------------------------------------------

        # Zona de Scroll pentru Riglele Psihometrice (Rulers)
        self.scroll_zona_rigle = QScrollArea()
        self.scroll_zona_rigle.setWidgetResizable(True)
        self.container_rigle = QWidget()
        self.rulers_layout = QVBoxLayout(self.container_rigle) # Folosim numele rulers_layout cerut de restul codului
        self.rulers_layout.setSpacing(5)
        self.rulers_layout.setAlignment(Qt.AlignTop)
        self.scroll_zona_rigle.setWidget(self.container_rigle)
        self.layout_sus_grafice.addWidget(self.scroll_zona_rigle)
        
        # --- SUB-PANOU JOS: TRANSCRIPT TEXT ---
        self.container_jos_transcript = QWidget()
        self.layout_jos_transcript = QVBoxLayout(self.container_jos_transcript)
        self.layout_jos_transcript.setContentsMargins(5, 5, 10, 10)
        

        # Rândul de butoane pentru controlul transcriptului (3 VARIANTE)
        self.layout_optiuni_transcript = QHBoxLayout()
        self.layout_optiuni_transcript.addWidget(QLabel("📝 TIP RAPORT:"))
        
        self.rb_session = QRadioButton("Live (Ce a văzut omul)")
        self.rb_virtual = QRadioButton("Virtual (Dosar Complet)")
        self.rb_analytical = QRadioButton("Analitic (Situație pe Axe)")
        
        self.rb_session.setChecked(True) # Default
        
        self.bg_mode = QButtonGroup()
        self.bg_mode.addButton(self.rb_session)
        self.bg_mode.addButton(self.rb_virtual)
        self.bg_mode.addButton(self.rb_analytical)
        
        # Conectăm toate butoanele la aceeași funcție de reîncărcare
        self.bg_mode.buttonClicked.connect(self.reload_transcript_view)
        
        self.layout_optiuni_transcript.addWidget(self.rb_session)
        self.layout_optiuni_transcript.addWidget(self.rb_virtual)
        self.layout_optiuni_transcript.addWidget(self.rb_analytical)
        self.layout_optiuni_transcript.addStretch()
        
        self.buton_export_transcript = QPushButton("💾 SALVEAZĂ DOSAR")
        self.buton_export_transcript.setStyleSheet("background-color: #e65100; color: white; font-weight: bold;")
        self.buton_export_transcript.clicked.connect(self.export_transcript)
        self.layout_optiuni_transcript.addWidget(self.buton_export_transcript)
        
        self.buton_import_extern = QPushButton("📥 IMPORT TESTARE")
        self.buton_import_extern.setStyleSheet("background-color: #1a237e; color: #82b1ff; font-weight: bold;")
        self.buton_import_extern.clicked.connect(self.import_external_exam)
        self.layout_optiuni_transcript.addWidget(self.buton_import_extern)
        
        self.layout_jos_transcript.addLayout(self.layout_optiuni_transcript)


        
        # Zona de text pentru afișarea transcriptului
        self.txt_transcript = QTextEdit()
        self.txt_transcript.setObjectName("Transcript")
        self.txt_transcript.setReadOnly(True)
        self.layout_jos_transcript.addWidget(self.txt_transcript)
        
        # Adăugăm containerele Sus și Jos în splitter-ul vertical de pe coloana dreaptă
        self.splitter_dreapta_vertical.addWidget(self.container_sus_grafice)
        self.splitter_dreapta_vertical.addWidget(self.container_jos_transcript)
        self.splitter_dreapta_vertical.setSizes([600, 300])

        # Asamblăm splitter-ul principal orizontal
        self.splitter_principal_orizontal.addWidget(self.panou_stanga_istoric)
        self.splitter_principal_orizontal.addWidget(self.splitter_dreapta_vertical)
        self.splitter_principal_orizontal.setSizes([250, 950])
        
        # Adăugăm splitter-ul în layout-ul principal al tab-ului
        self.layout_principal.addWidget(self.splitter_principal_orizontal)
        
        # Încărcăm lista inițială de pacienți
        self.refresh_patients()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def refresh_patients(self):
        self.cmb_patient_select.blockSignals(True)
        self.cmb_patient_select.clear()
        
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, full_name FROM patients ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        self.cmb_patient_select.addItem("- Selectează -", None)
        for pid, name in rows:
            self.cmb_patient_select.addItem(name, pid)
            
        self.cmb_patient_select.blockSignals(False)

    def load_sessions_for_patient(self):
        pid = self.cmb_patient_select.currentData()
        
        # SALVARE STARE: Memorăm ultimul pacient selectat
        if pid:
            from logic.settings_manager import SettingsManager
            SettingsManager.update_key("last_selected_patient_id", pid)
        
        # Debugging: verificăm starea flag-ului
        in_sync = getattr(self, '_in_sync_update', False)
        print(f"[TAB6 load_sessions] pid={pid}, _in_sync_update={in_sync}")
        
        # SINCRONIZARE GLOBALĂ: Notificăm când se selectează pacient (doar dacă nu suntem în sync)
        if pid and not in_sync:
            print(f"[TAB6 load_sessions] Triggering sync to other tabs...")
            main_window = self.window()
            if hasattr(main_window, 'sync_patient_selection'):
                main_window.sync_patient_selection(pid, 'tab_results')
        elif pid and in_sync:
            print(f"[TAB6 load_sessions] Skipping sync (already in sync mode)")
        
        # --- FIX: Bucla desfasurata corect ---
        while self.session_layout.count() > 0:
            item = self.session_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # -------------------------------------
            
        if not pid: return
        
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id, s.date_taken, t.name 
            FROM sessions s
            JOIN test_templates t ON s.template_id = t.id
            WHERE s.patient_id = ?
            ORDER BY s.date_taken DESC
        """, (pid,))
        sessions = c.fetchall()
        conn.close()
        
        for sid, date, tname in sessions:
            clean_date = date[:16]
            
            # Container pentru fiecare sesiune
            session_container = QWidget()
            session_h = QHBoxLayout(session_container)
            session_h.setContentsMargins(0, 0, 0, 0)
            session_h.setSpacing(5)
            
            # Butonul principal de selectare
            btn = QPushButton(f"{clean_date}\n{tname}")
            btn.clicked.connect(lambda checked=False, s=sid, n=tname, d=clean_date: self.load_session_data(s, n, d))
            session_h.addWidget(btn, 1)  # stretch=1 pentru a lua majoritatea spațiului
            
            # Butonul de ștergere
            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedWidth(40)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #5c0000;
                    color: #ff5252;
                    border: 1px solid #ff0000;
                    font-size: 16px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #8b0000;
                    color: white;
                }
            """)
            btn_delete.clicked.connect(lambda checked=False, s=sid: self.delete_session(s))
            session_h.addWidget(btn_delete)
            
            self.session_layout.addWidget(session_container)

    def load_session_data(self, session_id, test_name, date_str):
        self.current_session_id = session_id
        self.current_session_info = f"{date_str} | {test_name}"
        self.lbl_header.setText(f"📊 SESIUNEA: {test_name} ({date_str})")
        
        self.load_results_graphics(session_id)
        self.reload_transcript_view()

    def delete_session(self, session_id):
        """Șterge o sesiune și toate datele asociate, inclusiv cache-ul holistic"""
        reply = QMessageBox.question(
            self, 
            "Confirmare Ștergere",
            f"Ești sigur că vrei să ștergi această sesiune?\n\n"
            f"Atenție: Vor fi șterse:\n"
            f"• Toate răspunsurile din sesiune\n"
            f"• Rezultatele calculate\n"
            f"• Cache-ul de cunoștințe (Smart Skip)\n"
            f"• Sesiunea în sine\n\n"
            f"Această acțiune este IREVERSIBILĂ!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # 1. Identificăm pacientul
            c.execute("SELECT patient_id FROM sessions WHERE id=?", (session_id,))
            row = c.fetchone()
            if not row:
                QMessageBox.warning(self, "Eroare", "Sesiune invalidă.")
                return
            patient_id = row[0]
            
            # 2. Identificăm axele afectate (din session_results)
            c.execute("""
                SELECT DISTINCT axis_id FROM session_results 
                WHERE session_id=?
            """, (session_id,))
            affected_axes = [r[0] for r in c.fetchall()]
            
            log("sys", f"🗑️ Ștergere sesiune {session_id}. Axe afectate: {affected_axes}")
            
            # 3. Ștergem datele sesiunii
            c.execute("DELETE FROM session_results WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM session_responses WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM session_audit WHERE session_id=?", (session_id,))
            c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            
            # 4. Curățăm sau recalculăm holistic_knowledge pentru axele afectate
            for axis_id in affected_axes:
                # Verificăm dacă mai există alte sesiuni cu date pentru această axă
                c.execute("""
                    SELECT sr.session_id, s.date_taken, sr.final_score, sr.confidence
                    FROM session_results sr
                    JOIN sessions s ON sr.session_id = s.id
                    WHERE s.patient_id=? AND sr.axis_id=?
                    ORDER BY s.date_taken DESC
                    LIMIT 1
                """, (patient_id, axis_id))
                
                fallback = c.fetchone()
                
                if fallback:
                    # Există o sesiune mai veche, recalculăm din ea
                    fb_session_id, fb_date, fb_score, fb_confidence = fallback
                    
                    # RECALCULEZ: Câte întrebări din această axă rămân după ștergere
                    # session_responses DEJA ARE axis_id direct!
                    c.execute("""
                        SELECT COUNT(*)
                        FROM session_responses resp
                        JOIN sessions s ON resp.session_id = s.id
                        WHERE s.patient_id = ? AND resp.axis_id = ?
                    """, (patient_id, axis_id))
                    questions_used = c.fetchone()[0] or 0
                    
                    c.execute("""
                        UPDATE holistic_knowledge
                        SET latest_score=?, confidence=?, 
                            last_updated_at=?, source_session_id=?, questions_used=?
                        WHERE patient_id=? AND axis_id=?
                    """, (fb_score, fb_confidence, fb_date, fb_session_id, questions_used, patient_id, axis_id))
                    log("sys", f"♻️ Axa {axis_id}: Recalculat din sesiunea {fb_session_id}, {questions_used} întrebări CUMUL")
                else:
                    # Nu mai există date, ștergem din holistic
                    c.execute("""
                        DELETE FROM holistic_knowledge 
                        WHERE patient_id=? AND axis_id=?
                    """, (patient_id, axis_id))
                    log("sys", f"🧹 Axa {axis_id}: Șters complet din cache (nu mai există date)")
            
            conn.commit()
            
            QMessageBox.information(self, "Succes", 
                f"Sesiunea a fost ștearsă cu succes.\n"
                f"Cache-ul holistic a fost actualizat pentru {len(affected_axes)} axe.")
            
            # Dacă sesiunea ștearsă era cea curentă, curățăm ecranul
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.lbl_header.setText("REZULTATELE ANALIZEI")
                self.txt_transcript.clear()
                # Curățăm ruler-ele
                while self.rulers_layout.count() > 0:
                    item = self.rulers_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
            # Reîncărcăm lista de sesiuni
            self.load_sessions_for_patient()
            
            # Notificăm Tab 1 să se refresh-eze (dacă pacientul e selectat acolo)
            try:
                main_window = self.window()
                if hasattr(main_window, 'tab_widget'):
                    for i in range(main_window.tab_widget.count()):
                        tab = main_window.tab_widget.widget(i)
                        if hasattr(tab, 'refresh_list') and hasattr(tab, 'load_holistic_matrix'):
                            if hasattr(tab, 'current_patient_id') and tab.current_patient_id == patient_id:
                                print(f"[DELETE_SESSION] Refreshing Tab 1 for patient {patient_id}")
                                tab.load_holistic_matrix(patient_id)
                            break
            except Exception as e:
                log("sys", f"⚠️ Nu s-a putut reîmprospăta Tab 1: {e}")
            
        except Exception as e:
            log("sys", f"❌ Eroare ștergere sesiune: {e}")
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut șterge sesiunea:\n{e}")
        finally:
            conn.close()

    def load_results_graphics(self, session_id):
        # --- FIX: Bucla desfasurata corect ---
        while self.rulers_layout.count() > 0:
            item = self.rulers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # -------------------------------------
            
        conn = self.get_connection()
        c = conn.cursor()
        
        query = """
            SELECT 
                a.id, a.name, a.left_pole, a.right_pole, a.norm_mean, a.norm_std_dev,
                r.final_score, r.confidence
            FROM session_results r
            JOIN axes a ON r.axis_id = a.id
            WHERE r.session_id = ?
            ORDER BY a.category, a.name
        """
        c.execute(query, (session_id,))
        rows = c.fetchall()
        
        tested_scores = {}   # axis_id -> final_score (pentru reevaluarea sinergiilor)
        axis_name_map = {}   # axis_id -> nume (pentru afișarea condițiilor)
        for row in rows:
            axis_id, name, left, right, n_mean, n_sd, score, conf = row
            # Gestionare valori NULL
            if n_mean is None: n_mean = 50
            if n_sd is None: n_sd = 15
            
            tested_scores[axis_id] = score
            axis_name_map[axis_id] = name
            
            # Calculăm câte întrebări s-au folosit pentru această axă
            c.execute("SELECT COUNT(*) FROM session_responses WHERE session_id=? AND axis_id=?", (session_id, axis_id))
            questions_used = c.fetchone()[0]
            
            # Calculăm câte întrebări sunt disponibile TOTAL pentru această axă
            c.execute("SELECT COUNT(*) FROM questions_bank WHERE axis_id=? AND is_active=1", (axis_id,))
            questions_total = c.fetchone()[0]
            
            ruler = PsychometricRuler(name, left, right, score, conf, n_mean, n_sd, questions_used, questions_total)
            self.rulers_layout.addWidget(ruler)
        
        # --- Reevaluăm sinergiile pe scorurile finale: monștrii declanșați ---
        # Un monstru apare dacă TOATE axele lui trigger au fost testate ȘI îndeplinesc condițiile.
        # Monstrul însuși NU trebuie să fie în protocol.
        c.execute("SELECT monster_axis_id, trigger_axis_id, operator, threshold FROM synergy_rules")
        monster_conds = {}
        for mid, tid, op, th in c.fetchall():
            monster_conds.setdefault(mid, []).append((tid, op, th))
        
        header_added = False
        for mid, conds in monster_conds.items():
            all_sat = True
            detail = []
            for tid, op, th in conds:
                if tid not in tested_scores:
                    all_sat = False
                    break
                sc = tested_scores[tid]
                if op == '>':    ok = sc > th
                elif op == '<':  ok = sc < th
                elif op == '>=': ok = sc >= th
                elif op == '<=': ok = sc <= th
                else:            ok = False
                detail.append(f"{axis_name_map.get(tid, f'axa {tid}')} {int(sc)}{op}{int(th)}")
                if not ok:
                    all_sat = False
                    break
            if all_sat and detail:
                c.execute("SELECT name FROM axes WHERE id=?", (mid,))
                rowm = c.fetchone()
                mname = rowm[0] if rowm else f"Monstru {mid}"
                if not header_added:
                    lbl_h = QLabel("👹 MONȘTRI DETECTAȚI (sinergii pe scoruri finale)")
                    lbl_h.setStyleSheet("color:#ff0055; font-weight:bold; padding-top:10px;")
                    self.rulers_layout.addWidget(lbl_h)
                    header_added = True
                self.rulers_layout.addWidget(MonsterRow(mname, "   •   ".join(detail)))
        
        conn.close()

    def reload_transcript_view(self):
        """Metodă integrală care decide ce tip de audit afișează bazat pe cele 3 opțiuni."""
        if not self.current_session_id: 
            return
            
        self.txt_transcript.clear()
        
        if self.rb_session.isChecked():
            # LOG 1: Transcriptul real al ecranului
            self.generate_log_1_live(self.current_session_id)
        elif self.rb_virtual.isChecked():
            # LOG 2: Dosarul complet (Azi + Fantome)
            self.generate_log_2_virtual(self.current_session_id)
        else:
            # LOG 3: Analiza tehnică pe axe
            self.generate_log_3_analytical(self.current_session_id)


    def generate_strict_log(self, session_id):
        """Generează Log-ul strict cu ce a văzut subiectul pe ecran."""
        conexiune = self.get_connection()
        cursor = conexiune.cursor()
        
        # Luăm limita de screening (strategy_id este în sessions)
        cursor.execute("""
            SELECT es.w1_base_qty FROM sessions s
            JOIN exam_strategies es ON s.strategy_id = es.id
            WHERE s.id = ?
        """, (session_id,))
        result = cursor.fetchone()
        limita_w1 = result[0] if result else 3

        cursor.execute("""
            SELECT a.name, q.text_content, r.answer_chosen, r.score_snapshot, q.axis_id
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ? ORDER BY r.id ASC
        """, (session_id,))
        date_live = cursor.fetchall()

        output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "📝 LOG: SESIUNEA CURENTĂ (STRICT EXAMEN LIVE)\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        contor_axe = {}
        harta_L = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}

        for idx, (axa, intrebare, ans, scor, aid) in enumerate(date_live, 1):
            if aid not in contor_axe: contor_axe[aid] = 0
            contor_axe[aid] += 1
            
            prefix = "🔹 [SCREENING]" if contor_axe[aid] <= limita_w1 else "🚨 [CLARIFICARE]"
            secventa = f"{contor_axe[aid]}/{limita_w1}" if contor_axe[aid] <= limita_w1 else f"{contor_axe[aid]-limita_w1} (Extra)"
            
            output += f"{idx}. {prefix} [{axa}] {secventa}\n"
            output += f"   Q: {intrebare}\n"
            output += f"   RĂSPUNS: [{harta_L.get(int(ans), '?')}] -> {scor} pct.\n"
            output += "   " + "┈" * 50 + "\n"

        self.txt_transcript.setPlainText(output)
        self.current_transcript = output
        conexiune.close()

    def generate_contextual_log(self, session_id):
        """Metodă integrală: Reconstituie dosarul complet (Live + Smart Skip)."""
        conexiune = self.get_connection()
        cursor = conexiune.cursor()
        
        # 1. Preluăm datele live (azi)
        cursor.execute("""
            SELECT a.name, q.text_content, r.answer_chosen, r.score_snapshot, q.axis_id, 'LIVE' as origin
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ?
        """, (session_id,))
        date_live = cursor.fetchall()

        # 2. Preluăm 'întrebările fantomă' (Smart Skip)
        cursor.execute("""
            SELECT a.name, sa.question_text, 'N/A', 'N/A', sa.axis_id, 'GHOST' as origin, sa.explanation
            FROM session_audit sa
            JOIN axes a ON sa.axis_id = a.id
            WHERE sa.session_id = ? AND sa.decision_type = 'Smart Skip'
        """, (session_id,))
        date_ghost = cursor.fetchall()

        # 3. Combinăm și organizăm pe Axe
        toate_datele = date_live + date_ghost
        harta_axe = {}
        for r in toate_datele:
            nume_axa = r[0]
            if nume_axa not in harta_axe: harta_axe[nume_axa] = []
            harta_axe[nume_axa].append(r)

        output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "📚 LOG: CONTEXTUAL (DOSAR COMPLET / AUDIT TOTAL)\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for nume_axa, itemi in harta_axe.items():
            output += f"▶ AXA: {nume_axa.upper()}\n"
            output += "  " + "─" * 40 + "\n"
            
            # Sortăm itemii astfel încât Ghost (Screening vechi) să fie primii, apoi Live
            # (Presupunem că Ghost sunt mereu din screening-ul inițial)
            itemi_sortati = sorted(itemi, key=lambda x: x[5], reverse=True) 
            
            for i, item in enumerate(itemi_sortati, 1):
                nume, q_text, ans, scor, aid, origin = item[0], item[1], item[2], item[3], item[4], item[5]
                
                if origin == 'GHOST':
                    expl = item[6]
                    output += f"  {i}. ♻️ [FANTOMĂ - SMART SKIP]\n"
                    output += f"     Q: {q_text}\n"
                    output += f"     STATUT: {expl}\n"
                else:
                    output += f"  {i}. 🔹 [LIVE - COMPLETAT AZI]\n"
                    output += f"     Q: {q_text}\n"
                    output += f"     RĂSPUNS: {ans} -> {scor} pct.\n"
                output += "     " + "┈" * 30 + "\n"
            output += "\n"

        self.txt_transcript.setPlainText(output)
        self.current_transcript = output
        conexiune.close()


    def generate_session_transcript(self, session_id):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                r.question_hash, r.answer_chosen, q.text_content, r.score_snapshot,
                q.wave_target, a.name, a.source_system
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ?
            ORDER BY r.id
        """, (session_id,))
        
        responses = c.fetchall()
        conn.close()
        
        text = f"RAPORT SESIUNE CURENTĂ\nDOSAR: {self.current_session_info}\n"
        text += "="*60 + "\n\n"
        # Start de la 1
        text += self._format_qa_blocks(responses, start_index=1)
        
        self.txt_transcript.setText(text)
        self.current_transcript = text

    def generate_full_transcript(self, session_id):
        pid = self.cmb_patient_select.currentData()
        if not pid: return
        
        conn = self.get_connection()
        c = conn.cursor()
        
        # 1. Config Template
        c.execute("SELECT template_id FROM sessions WHERE id=?", (session_id,))
        row_temp = c.fetchone()
        if not row_temp: conn.close(); return
        tid = row_temp[0]
        
        c.execute("SELECT config_json FROM test_templates WHERE id=?", (tid,))
        row_conf = c.fetchone()
        if not row_conf: conn.close(); return
        config = json.loads(row_conf[0])
        required_axes = set(config.get("wave1", {}).get("axes", []))
        
        # 2. Date Curente
        c.execute("""
            SELECT 
                r.question_hash, r.answer_chosen, q.text_content, r.score_snapshot, 
                q.axis_id, q.wave_target, a.name, a.source_system
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ?
            ORDER BY r.id
        """, (session_id,))
        current_rows = c.fetchall()
        
        # Structura raw: (hash, ans, text, score, axis_id, wave, axis_name, source_system)
        # Avem nevoie să scoatem axis_id (index 4) pentru formatter
        clean_current = []
        for r in current_rows:
            clean_current.append((r[0], r[1], r[2], r[3], r[5], r[6], r[7]))
            
        covered_axes = {row[4] for row in current_rows}
        
        # 3. Smart Skip History
        missing_axes = required_axes - covered_axes
        history_rows = []
        
        if missing_axes:
            placeholders = ','.join('?' for _ in missing_axes)
            params = [pid] + list(missing_axes)
            c.execute(f"SELECT source_session_id, axis_id FROM holistic_knowledge WHERE patient_id = ? AND axis_id IN ({placeholders})", params)
            knowledge_rows = c.fetchall()
            
            for src_sess_id, aid in knowledge_rows:
                c.execute("""
                    SELECT 
                        r.question_hash, r.answer_chosen, q.text_content, r.score_snapshot,
                        q.wave_target, a.name, a.source_system
            FROM session_responses r
                    JOIN questions_bank q ON r.question_hash = q.version_hash
                    JOIN axes a ON q.axis_id = a.id
                    WHERE r.session_id = ? AND r.axis_id = ?
                """, (src_sess_id, aid))
                qs = c.fetchall()
                for q in qs:
                    history_rows.append(q + (f"[PRELUAT DIN ISTORIC - SESIUNEA {src_sess_id}]",))
        
        conn.close()
        
        text = f"RAPORT CONTEXTUAL (Smart Skip Integrat)\nSUBIECT: {self.cmb_patient_select.currentText()}\n"
        text += "="*60 + "\n\n"
        
        text += "--- I. DATE DIN SESIUNEA CURENTĂ ---\n\n"
        # Numerotare 1...N
        text += self._format_qa_blocks(clean_current, start_index=1)
        
        next_start = len(clean_current) + 1
        
        if history_rows:
            text += "\n--- II. DATE IMPORTATE (ISTORIC RECENT) ---\n\n"
            # Numerotare N+1...M
            text += self._format_qa_blocks(history_rows, is_history=True, start_index=next_start)
        else:
            text += "\n(Toate axele cerute au fost testate azi)\n"

        self.txt_transcript.setText(text)
        self.current_transcript = text

    def _format_qa_blocks(self, rows, is_history=False, start_index=1):
        conn = self.get_connection()
        c = conn.cursor()
        output = ""
        letter_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        
        for idx, row in enumerate(rows, start_index):
            q_hash = row[0]
            answer_idx = row[1]
            q_text = row[2]
            score = row[3]
            wave = row[4]
            axis_name = row[5]
            source_system = row[6] if len(row) > 6 else ""
            if source_system is None:
                source_system = ""
            extra_tag = row[7] if len(row) > 7 else ""
            
            # Motivație
            motivation = ""
            if is_history:
                motivation = f"   [INFO] {extra_tag} | Axa: {axis_name}"
            else:
                if wave == 1: motivation = f"   [INFO] VAL 1: Screening Standard | Axa: {axis_name}"
                elif wave == 2: motivation = f"   [⚠️ ALERT] VAL 2: Confirmare Inconsistență | Axa: {axis_name}"
                elif wave == 3: motivation = f"   [👹 ALERT] VAL 3: DEEP DIVE | Axa: {axis_name}"
            
            output += f"{motivation}\n"
            if source_system:
                output += f"   [{source_system}]\n"
            output += f"#{idx}. {q_text}\n"
            
            c.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash = ? ORDER BY option_index", (q_hash,))
            options = c.fetchall()
            
            for opt_idx, opt_text, opt_score in options:
                display_text = opt_text
                prefix_opt = f"{opt_idx}) "
                if not display_text.startswith(prefix_opt):
                     display_text = f"{prefix_opt}{display_text}"

                is_selected = False
                try:
                    if letter_map.get(int(answer_idx), '?') == opt_idx: is_selected = True
                except: pass
                
                mark = "[X]" if is_selected else "[ ]"
                output += f"   {mark} {display_text}   [{opt_score}p]\n"
            
            output += f"   >> IMPACT SCOR: {score}\n"
            output += "-" * 40 + "\n"
            
        conn.close()
        return output

    def export_transcript(self):
        if not self.current_transcript:
            QMessageBox.warning(self, "Eroare", "Niciun raport încărcat.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Salvează Raport", f"Raport_{self.cmb_patient_select.currentText()}.txt", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.current_transcript)
                QMessageBox.information(self, "Succes", "Raport salvat.")
            except Exception as e:
                QMessageBox.critical(self, "Eroare", f"Nu s-a putut salva: {e}")

    def run_session_ai_analysis(self):
        """Metoda principală care colectează datele sesiunii și apelează AI-ul."""
        if not self.current_session_id:
            QMessageBox.warning(self, "Atenție", "Vă rugăm să selectați o sesiune din istoricul din stânga.")
            return

        # 1. Extragem datele specifice DOAR pentru această sesiune
        date_sesiune = self.get_current_session_data_for_ai()
        
        if not date_sesiune:
            QMessageBox.warning(self, "Eroare", "Nu am putut recupera scorurile pentru această sesiune.")
            return

        # 2. Identificăm personalitatea selectată
        persona_selectata = self.cmb_ai_persona_results.currentText()
        cod_persona = "HR" if "HR" in persona_selectata else ("Psych" if "Psych" in persona_selectata else "Academic")

        # 3. Apelăm Agentul de Profilare (îl instanțiem pe loc sau în __init__)
        if not hasattr(self, 'profiler_agent'):
            self.profiler_agent = ProfilerAgent()

        # Afișăm un mesaj de așteptare în consolă sau status bar
        self.btn_ai.setText("⌛ SE GENEREAZĂ...")
        self.btn_ai.setEnabled(False)
        QApplication.processEvents()

        try:
            # Rulăm analiza (trimitem ca o listă cu un singur "pseudo-pacient" care conține datele sesiunii)
            raport_text_ai = self.profiler_agent.run_analysis([date_sesiune], cod_persona)
            
            # 4. Formatăm și afișăm în fereastra separată
            continut_formatat = self.format_text_pentru_raport_results(raport_text_ai)
            
            # Luăm ID-ul pacientului pentru a permite arhivarea
            id_pacient = self.cmb_patient_select.currentData()
            
            from logic.patient_manager import PatientManager
            manager_pacient = PatientManager()
            
            fereastra_raport = ReportWindow(
                f"ANALIZĂ SESIUNE: {self.current_session_info}", 
                continut_formatat, 
                id_pacient, 
                cod_persona, 
                manager_pacient, 
                self
            )
            fereastra_raport.exec()
            
        except Exception as eroare:
            QMessageBox.critical(self, "Eroare AI", f"A apărut o problemă la generare: {str(eroare)}")
        finally:
            self.btn_ai.setText("🧠 GENEREAZĂ INTERPRETARE AI")
            self.btn_ai.setEnabled(True)

    def get_current_session_data_for_ai(self):
        """Interoghează baza de date pentru a obține scorurile SNAPSHOT ale sesiunii selectate."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            query = """
                SELECT a.name, r.final_score, r.confidence
                FROM session_results r
                JOIN axes a ON r.axis_id = a.id
                WHERE r.session_id = ?
            """
            cursor.execute(query, (self.current_session_id,))
            randuri = cursor.fetchall()
            
            if not randuri:
                return None
                
            # Structurăm datele exact cum se așteaptă ProfilerAgent
            nume_pacient = self.cmb_patient_select.currentText()
            return {
                "id": self.current_session_id,
                "name": f"{nume_pacient} (Sesiunea {self.current_session_info})",
                "holistic": [{"name": r[0], "score": r[1], "confidence": r[2]} for r in randuri]
            }
        finally:
            conexiune.close()

    def format_text_pentru_raport_results(self, text_brut):
        """Formatează textul cu culori specifice Hunter pentru fereastra de raport."""
        import re
        text_html = text_brut.replace("\n", "<br>")
        # Cifrele și procentele devin albastre neon
        text_html = re.sub(r'(\d+%)', r'<b style="color: #00e5ff;">\1</b>', text_html)
        # Orice text între asteriscuri devine bold alb
        text_html = re.sub(r'\*\*(.*?)\*\*', r'<b style="color: #ffffff;">\1</b>', text_html)
        
        return f"<div style='color: #e0e0e0; line-height: 1.6; font-size: 15px;'>{text_html}</div>"

    def generate_mechanical_audit(self, session_id, mode_strict=True):
        """Metodă integrală: Generează cele două tipuri de loguri (Strict vs Contextual) fără a le amesteca."""
        import sqlite3
        conexiune = self.get_connection()
        cursor = conexiune.cursor()
        
        print(f"\n\033[95m[TAB 6 DEBUG] >>> GENERARE AUDIT PT SESIUNEA {session_id} (Mod Strict: {mode_strict})\033[0m")

        # 1. Preluăm limita de screening (w1_qty) a sesiunii (strategy_id în sessions)
        cursor.execute("""
            SELECT es.w1_base_qty FROM sessions s
            JOIN exam_strategies es ON s.strategy_id = es.id
            WHERE s.id = ?
        """, (session_id,))
        res_w1 = cursor.fetchone()
        limita_w1 = res_w1[0] if res_w1 else 3

        # 2. Luăm toate răspunsurile LIVE (Cele care au apărut pe ecran azi)
        cursor.execute("""
            SELECT a.name, q.text_content, r.answer_chosen, r.score_snapshot, q.axis_id, r.id
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ?
            ORDER BY r.id ASC
        """, (session_id,))
        date_live = cursor.fetchall()
        
        # 3. Luăm toate înregistrările de AUDIT (Injecții și Smart Skips)
        cursor.execute("""
            SELECT sa.axis_id, sa.explanation, sa.decision_type, sa.question_text, a.name
            FROM session_audit sa
            JOIN axes a ON sa.axis_id = a.id
            WHERE sa.session_id = ?
            ORDER BY sa.id ASC
        """, (session_id,))
        date_audit = cursor.fetchall()

        # Pregătim hărți de date pentru asamblare rapidă
        harta_justificari_extra = {} # De ce s-au injectat întrebări Val 2
        lista_fantomelor = []        # Întrebările sărite (Smart Skip)
        
        for a_id, expl, d_type, q_text, a_name in date_audit:
            if d_type == "Smart Skip":
                lista_fantomelor.append({
                    "axis_id": int(a_id),
                    "axis_name": a_name,
                    "text": q_text,
                    "explanation": expl
                })
            else:
                harta_justificari_extra[int(a_id)] = expl

        harta_L = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        text_final = ""

        # =====================================================================
        # CAZUL 1: LOG STRICT (DOAR CE S-A ÎNTÂMPLAT LIVE)
        # =====================================================================
        if mode_strict:
            text_final += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text_final += "📝 LOG 1: STRICT SESIUNEA CURENTĂ (CE A VĂZUT SUBIECTUL)\n"
            text_final += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            if not date_live:
                text_final += "[INFO] Nu există activitate live în această sesiune (Axe completate prin Smart Skip).\n"
            else:
                contor_per_axa_live = {}
                for idx, (axa_nume, text_q, ans_idx, scor, aid, rid) in enumerate(date_live, 1):
                    aid_int = int(aid)
                    contor_per_axa_live[aid_int] = contor_per_axa_live.get(aid_int, 0) + 1
                    prio = contor_per_axa_live[aid_int]
                    
                    is_screening = prio <= limita_w1
                    simbol = "🔹 [SCREENING]" if is_screening else "🚨 [CLARIFICARE]"
                    
                    # Calculăm X/Y pentru clarificări
                    if not is_screening:
                        total_pe_axa = sum(1 for r in date_live if int(r[4]) == aid_int)
                        total_extra = total_pe_axa - limita_w1
                        numar_extra = prio - limita_w1
                        secventa = f"{numar_extra}/{total_extra}"
                        motiv = harta_justificari_extra.get(aid_int, "Nevoie de stabilizare scor.")
                    else:
                        secventa = f"{prio}/{limita_w1}"
                        motiv = "Protocol Standard de Screening"

                    try: litera = harta_L.get(int(ans_idx), "?")
                    except: litera = "?"

                    text_final += f"{idx}. {simbol} [{axa_nume}] {secventa}\n"
                    text_final += f"   👉 MOTIVAȚIE: {motiv}\n"
                    text_final += f"   Q: {text_q}\n"
                    text_final += f"   RĂSPUNS: [{litera}] -> Scor: {scor} pct.\n"
                    text_final += "   " + "┈" * 55 + "\n"

        # =====================================================================
        # CAZUL 2: LOG CONTEXTUAL (DOSARUL COMPLET / TOT ADEVĂRUL)
        # =====================================================================
        else:
            text_final += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text_final += "📚 LOG 2: CONTEXTUAL (DOSAR COMPLET: LIVE + SMART SKIP)\n"
            text_final += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Grupăm toate datele (Live + Fantome) pe Axe
            toate_axele_implicate = sorted(list(set(
                [int(r[4]) for r in date_live] + [f['axis_id'] for f in lista_fantomelor]
            )))

            for aid in toate_axele_implicate:
                # Luăm numele axei
                cursor.execute("SELECT name FROM axes WHERE id = ?", (aid,))
                nume_axa = cursor.fetchone()[0]
                
                text_final += f"▶ AXA: {nume_axa.upper()}\n"
                text_final += "  " + "─" * 40 + "\n"
                
                # Colectăm itemii acestei axe (Live și Fantome)
                itemi_axa_live = [r for r in date_live if int(r[4]) == aid]
                itemi_axa_ghost = [f for f in lista_fantomelor if f['axis_id'] == aid]
                
                # Afișăm Fantomele (Smart Skip)
                for f in itemi_axa_ghost:
                    text_final += "  ♻️ [FANTOMĂ - SMART SKIP]\n"
                    text_final += f"     Q: {f['text']}\n"
                    text_final += f"     STATUT: {f['explanation']}\n"
                    text_final += "     " + "┈" * 30 + "\n"
                
                # Afișăm Live-ul
                contor_l2 = 0
                for r in itemi_axa_live:
                    contor_l2 += 1
                    try: litera = harta_L.get(int(r[2]), "?")
                    except: litera = "?"
                    
                    # Decidem dacă e screening sau extra în contextul acestei axe
                    # (Dacă avem deja ghosts, probabil live-ul e extra)
                    prefix_l2 = "🔹 [LIVE]"
                    text_final += f"  {prefix_l2} Item #{contor_l2}\n"
                    text_final += f"     Q: {r[1]}\n"
                    text_final += f"     RĂSPUNS: [{litera}] -> Scor: {r[3]} pct.\n"
                    text_final += "     " + "┈" * 30 + "\n"
                
                text_final += "\n"

        # Afișare în widget
        self.txt_transcript.setPlainText(text_final)
        self.current_transcript = text_final
        conexiune.close()
        print(f"\033[92m[TAB 6 DEBUG] Generare raport finalizată pentru Sesiunea {session_id}\033[0m")


    def _get_axis_norms_from_db(self, axis_id):
        """Metodă integrală care returnează media și deviația standard ale unei axe."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT norm_mean, norm_std_dev FROM axes WHERE id = ?", (axis_id,))
            row = c.fetchone()
            # Dacă axa nu are norme setate, folosim valorile standard de 50 și 15
            if row:
                medie = row[0] if row[0] is not None else 50.0
                deviatie = row[1] if row[1] is not None else 15.0
                return medie, deviatie
            return 50.0, 15.0
        finally:
            conn.close()

    def generate_log_1_live(self, session_id):
        """Metodă integrală: Transcript live cu corecție pentru prefixele dublate (A, B, C, D)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # CORECT: strategy_id este în sessions, nu în test_templates
        cursor.execute("SELECT es.w1_base_qty FROM sessions s JOIN exam_strategies es ON s.strategy_id = es.id WHERE s.id = ?", (session_id,))
        result = cursor.fetchone()
        limita_w1 = result[0] if result else 3  # Default 3 dacă nu găsește

        cursor.execute("SELECT axis_id, explanation, decision_type FROM session_audit WHERE session_id = ?", (session_id,))
        harta_audit = {int(r[0]): {"expl": r[1], "type": r[2]} for r in cursor.fetchall()}

        cursor.execute("""
            SELECT a.name, q.text_content, r.answer_chosen, r.score_snapshot, q.axis_id, r.question_hash
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN axes a ON q.axis_id = a.id
            WHERE r.session_id = ? ORDER BY r.id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        
        total_per_axa = {}
        for r in rows:
            aid = int(r[4])
            total_per_axa[aid] = total_per_axa.get(aid, 0) + 1

        output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "📝 LOG 1: TRANSCRIPT LIVE (GRILĂ CURATĂ DE RĂSPUNSURI)\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        contor_axa = {}
        harta_L = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        
        for idx, (axa, q_text, ans, scor, aid, q_hash) in enumerate(rows, 1):
            aid_int = int(aid)
            contor_axa[aid_int] = contor_axa.get(aid_int, 0) + 1
            numar_curent = contor_axa[aid_int]
            is_w1 = numar_curent <= limita_w1
            
            prefix, fractie = ("🔹 [SCREENING]", f"{numar_curent}/{limita_w1}") if is_w1 else ("🚨 [CLARIFICARE]", f"{numar_curent - limita_w1}/{total_per_axa[aid_int] - limita_w1}")
            
            output += f"{idx}. {prefix} [{axa}] {fractie}\n"
            output += f"   Q: {q_text}\n"
            
            # EXTRAGERE VARIANTE
            cursor.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash = ? ORDER BY option_index", (q_hash,))
            optiuni = cursor.fetchall()
            
            try: litera_aleasa = harta_L.get(int(ans), "?")
            except: litera_aleasa = "?"
            
            for opt_idx, opt_txt, opt_pts in optiuni:
                marcaj = "[X]" if opt_idx == litera_aleasa else "[ ]"
                
                # --- LOGICĂ REPARARE PREFIX DUBLU ---
                display_txt = opt_txt
                # Dacă textul din DB nu începe cu "A)" sau "B)" etc., îi punem noi prefixul
                if not display_txt.startswith(f"{opt_idx})"):
                    display_txt = f"{opt_idx}) {display_txt}"
                
                output += f"     {marcaj} {display_txt} ({opt_pts} pts)\n"
            
            if not is_w1 and aid_int in harta_audit:
                output += f"\n   👉 MOTIVAȚIE: {harta_audit[aid_int]['expl']}\n"
            
            output += "   " + "┈" * 60 + "\n"

        self.txt_transcript.setPlainText(output)
        self.current_transcript = output
        conn.close()

    def generate_log_2_virtual(self, session_id):
        """
        LOG 2: DOSAR VIRTUAL (Include GHOST + LIVE)
        Structură identică cu LOG 1, dar include și întrebările fantomă.
        """
        try:
            print(f"\n[DEBUG LOG 2] START pentru sesiunea {session_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Preluăm limita W1 (strategy_id în sessions)
            cursor.execute("SELECT es.w1_base_qty FROM sessions s JOIN exam_strategies es ON s.strategy_id = es.id WHERE s.id = ?", (session_id,))
            result = cursor.fetchone()
            limita_w1 = result[0] if result else 3
            print(f"[DEBUG LOG 2] limita_w1 = {limita_w1}")

            # Preluăm audit (fără GHOST)
            cursor.execute("SELECT axis_id, explanation, decision_type FROM session_audit WHERE session_id = ? AND decision_type != 'Smart Skip'", (session_id,))
            harta_audit = {int(r[0]): {"expl": r[1], "type": r[2]} for r in cursor.fetchall()}
            print(f"[DEBUG LOG 2] harta_audit = {len(harta_audit)} entries")

            # Preluăm întrebările LIVE
            cursor.execute("""
                SELECT a.name, q.text_content, r.answer_chosen, r.score_snapshot, q.axis_id, r.question_hash
                FROM session_responses r
                JOIN questions_bank q ON r.question_hash = q.version_hash
                JOIN axes a ON q.axis_id = a.id
                WHERE r.session_id = ? ORDER BY r.id ASC
            """, (session_id,))
            live_rows = cursor.fetchall()
            print(f"[DEBUG LOG 2] live_rows = {len(live_rows)} întrebări")
            
            # Preluăm întrebările GHOST
            cursor.execute("SELECT axis_id, explanation, question_text, question_hash FROM session_audit WHERE session_id = ? AND decision_type = 'Smart Skip'", (session_id,))
            ghost_rows = cursor.fetchall()
            print(f"[DEBUG LOG 2] ghost_rows = {len(ghost_rows)} întrebări")
            
            # Combinăm tot într-o listă
            toate = []
            for r in live_rows:
                toate.append({"name": r[0], "text": r[1], "ans": r[2], "score": r[3], "aid": int(r[4]), "hash": r[5], "is_ghost": False})
            
            for g in ghost_rows:
                cursor.execute("SELECT name FROM axes WHERE id=?", (g[0],))
                name_result = cursor.fetchone()
                if name_result:
                    name = name_result[0]
                    toate.append({"name": name, "text": g[2], "ans": -1, "score": g[1], "aid": int(g[0]), "hash": g[3], "is_ghost": True})
            
            print(f"[DEBUG LOG 2] total combinat = {len(toate)} întrebări")
            
            # Grupăm pe axe
            axe_dict = {}
            for it in toate:
                if it['name'] not in axe_dict:
                    axe_dict[it['name']] = []
                axe_dict[it['name']].append(it)
            
            print(f"[DEBUG LOG 2] axe_dict = {len(axe_dict)} axe")
            
            # Generăm output
            output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            output += "📚 LOG 2: DOSAR VIRTUAL (LIVE + GHOST = Adevărul Integral)\n"
            output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            global_idx = 1
            for axa_nume in sorted(axe_dict.keys()):
                items = axe_dict[axa_nume]
                total = len(items)
                
                for idx, item in enumerate(items, 1):
                    aid = item['aid']
                    is_w1 = idx <= limita_w1
                    
                    if item['is_ghost']:
                        prefix = "👻 [GHOST]"
                    elif is_w1:
                        prefix = "🔹 [SCREENING]"
                    else:
                        prefix = "🚨 [CLARIFICARE]"
                    
                    fractie = f"{idx}/{limita_w1}" if is_w1 else f"{idx - limita_w1}/{total - limita_w1}"
                    
                    output += f"{global_idx}. {prefix} [{axa_nume}] {fractie}\n"
                    output += f"   Q: {item['text']}\n\n"
                    
                    if item['is_ghost']:
                        output += f"   🔮 {item['score']}\n"
                        # Opțiuni pentru referință
                        if item['hash']:
                            cursor.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash=? ORDER BY option_index", (item['hash'],))
                            opts = cursor.fetchall()
                            if opts:
                                output += "   Opțiuni (referință):\n"
                                for opt_idx, opt_txt, opt_pts in opts:
                                    import re
                                    clean = re.sub(r'^[A-D]\)\s*', '', opt_txt)
                                    # opt_idx poate fi 0,1,2,3 SAU 'A','B','C','D'
                                    if isinstance(opt_idx, int):
                                        letter = chr(65 + opt_idx)
                                    else:
                                        letter = str(opt_idx)
                                    output += f"     [ ] {letter}) {clean} ({opt_pts} pts)\n"
                    else:
                        # LIVE - afișăm cu [X]
                        cursor.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash=? ORDER BY option_index", (item['hash'],))
                        opts = cursor.fetchall()
                        for opt_idx, opt_txt, opt_pts in opts:
                            # Convertim la int pentru comparație
                            if isinstance(opt_idx, str):
                                opt_idx_num = ord(opt_idx) - 65 if len(opt_idx) == 1 else int(opt_idx)
                                letter = opt_idx
                            else:
                                opt_idx_num = int(opt_idx)
                                letter = chr(65 + opt_idx_num)
                            
                            marcaj = "[X]" if opt_idx_num == item['ans'] else "[ ]"
                            import re
                            clean = re.sub(r'^[A-D]\)\s*', '', opt_txt)
                            output += f"     {marcaj} {letter}) {clean} ({opt_pts} pts)\n"
                    
                    if not is_w1 and not item['is_ghost'] and aid in harta_audit:
                        output += f"\n   👉 MOTIVAȚIE: {harta_audit[aid]['expl']}\n"
                    
                    output += "   " + "┈" * 60 + "\n\n"
                    global_idx += 1
            
            print(f"[DEBUG LOG 2] output length = {len(output)} chars")
            
            self.txt_transcript.setPlainText(output)
            self.current_transcript = output
            conn.close()
            print("[DEBUG LOG 2] DONE")
            
        except Exception as e:
            print(f"[DEBUG LOG 2] EROARE: {e}")
            import traceback
            traceback.print_exc()
            self.txt_transcript.setPlainText(f"EROARE LOG 2: {e}")

    def generate_log_3_analytical(self, session_id):
        """Metodă integrală: Analiza pură a deciziilor algoritmului pe axele testate."""
        conexiune = self.get_connection()
        cursor = conexiune.cursor()
        
        cursor.execute("SELECT axis_id, explanation, decision_type FROM session_audit WHERE session_id = ? AND decision_type != 'Smart Skip'", (session_id,))
        audit_data = {int(r[0]): {"expl": r[1], "type": r[2]} for r in cursor.fetchall()}

        cursor.execute("""
            SELECT a.name, r.final_score, r.confidence, a.id, a.norm_mean, a.norm_std_dev
            FROM session_results r
            JOIN axes a ON r.axis_id = a.id
            WHERE r.session_id = ?
        """, (session_id,))
        results = cursor.fetchall()

        output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "📊 LOG 3: ANALIZA CRITICĂ A DECIZIILOR DE CALCUL\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for name, score, conf, aid, n_mean, n_sd in results:
            aid_int = int(aid)
            output += f"📈 AXA: {name.upper()}\n"
            output += f"   NORMA POPULAȚIEI: {n_mean} (±{n_sd})\n"
            output += f"   REZULTAT SUBIECT: {score}% (Confidență: {conf}%)\n"
            
            if aid_int in audit_data:
                audit_info = audit_data[aid_int]
                output += f"   ⚡ ALERTA DETECTATĂ: {audit_info['type'].upper()}\n"
                output += f"   👉 DETALII: {audit_info['expl']}\n"
            else:
                output += "   ✅ STATUS: Axa stabilă. Screening în limitele rigoarei.\n"
            
            output += "   " + "─" * 45 + "\n"

        self.txt_transcript.setPlainText(output)
        self.current_transcript = output
        conexiune.close()
    def import_external_exam(self):
        """Importă rezultatele unei testări externe (standalone). Pacientul e preluat din pachet și preselectat, cu confirmare."""
        print("\n" + "="*60)
        print("[IMPORT] Starting external exam import...")
        
        # 1. Selectăm DB-ul extern
        db_path, _ = QFileDialog.getOpenFileName(
            self, "Selectează DB Completat", "", "Database (*.db)")
        
        if not db_path:
            print("[IMPORT] User cancelled file selection")
            return
        
        print(f"[IMPORT] Selected DB: {db_path}")
        
        try:
            import sqlite3
            from config import Config
            
            # Conectăm la DB-ul extern
            print("[IMPORT] Connecting to external DB...")
            conn_ext = sqlite3.connect(db_path)
            c_ext = conn_ext.cursor()
            
            # Verificăm că fișierul ales e un pachet de testare valid (are tabelul 'meta').
            # Baza aplicației nu are 'meta', deci asta blochează selecția greșită.
            has_meta = c_ext.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta'").fetchone()
            if not has_meta:
                print("[IMPORT] ERROR: fișierul nu e un pachet valid (lipsește 'meta')")
                QMessageBox.warning(self, "Fișier invalid",
                    "Fișierul ales nu pare un pachet de testare.\n\n"
                    "Alege fișierul exam_package.db primit de la persoana testată, "
                    "nu baza de date a aplicației (hunter_protocol.db).")
                conn_ext.close()
                return
            
            # Verificăm dacă există sesiune completată (CEA MAI RECENTĂ)
            print("[IMPORT] Checking for completed session...")
            c_ext.execute("SELECT id, candidate_name, date_taken FROM sessions WHERE status='Completed' ORDER BY date_taken DESC LIMIT 1")
            session_ext = c_ext.fetchone()
            
            if not session_ext:
                print("[IMPORT] ERROR: No completed session found")
                QMessageBox.warning(self, "Eroare", "Nu există sesiune completată în acest DB!")
                conn_ext.close()
                return
            
            ext_session_id, candidate_name, date_taken = session_ext
            print(f"[IMPORT] Found LATEST session ID {ext_session_id}: {candidate_name} at {date_taken}")
            
            # Conectăm la DB-ul principal
            print("[IMPORT] Connecting to main DB...")
            conn_main = sqlite3.connect(Config.DB_NAME)
            c_main = conn_main.cursor()
            
            # 2. Obținem metadatele, inclusiv pacientul turnat în pachet (dacă există)
            print("[IMPORT] Reading metadata...")
            meta_cols = [r[1] for r in c_ext.execute("PRAGMA table_info(meta)").fetchall()]
            if "patient_id" in meta_cols:
                c_ext.execute("SELECT template_id, strategy_id, patient_id, patient_name FROM meta")
                template_id, strategy_id, baked_pid, baked_pname = c_ext.fetchone()
            else:
                c_ext.execute("SELECT template_id, strategy_id FROM meta")
                template_id, strategy_id = c_ext.fetchone()
                baked_pid, baked_pname = None, None
            print(f"[IMPORT] Template ID: {template_id}, Strategy ID: {strategy_id}, Patient: {baked_pname} ({baked_pid})")

            # Preselectăm pacientul turnat în pachet (dacă există în listă)
            if baked_pid is not None:
                idx = self.cmb_patient_select.findData(baked_pid)
                if idx >= 0:
                    self.cmb_patient_select.setCurrentIndex(idx)
                    print(f"[IMPORT] Preselectat pacientul din pachet (index {idx})")

            patient_id = self.cmb_patient_select.currentData()
            if not patient_id:
                QMessageBox.warning(self, "Eroare",
                    "Pachetul nu conține un pacient cunoscut, iar în listă nu e selectat niciunul.\n"
                    "Selectează un pacient din listă și reia importul.")
                conn_ext.close()
                conn_main.close()
                return

            patient_name = self.cmb_patient_select.currentText()

            # Confirmarea ta înainte de a atașa rezultatul
            resp = QMessageBox.question(self, "Confirmă pacientul",
                f"Rezultatul va fi atașat pacientului:\n\n{patient_name}\n\nContinui importul?",
                QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                print("[IMPORT] User cancelled at patient confirmation")
                conn_ext.close()
                conn_main.close()
                return

            # 3. Creăm sesiunea în DB-ul principal PENTRU PACIENTUL CONFIRMAT
            # MIGRARE: asigurăm coloana strategy_id în sessions (la fel ca în exam_engine)
            c_main.execute("PRAGMA table_info(sessions)")
            session_cols = [col[1] for col in c_main.fetchall()]
            if "strategy_id" not in session_cols:
                c_main.execute("ALTER TABLE sessions ADD COLUMN strategy_id INTEGER")
                conn_main.commit()
                print("[IMPORT] DB Migration: Adăugat strategy_id în sessions")

            print(f"[IMPORT] Creating new session for patient {patient_id}...")
            c_main.execute("INSERT INTO sessions (patient_id, template_id, strategy_id, date_taken, status) VALUES (?,?,?,?,?)",
                          (patient_id, template_id, strategy_id, date_taken, "Completed"))
            new_session_id = c_main.lastrowid
            print(f"[IMPORT] Created session ID: {new_session_id}")
            
            # 4. Copiem răspunsurile
            print("[IMPORT] Copying responses...")
            c_ext.execute("SELECT question_hash, axis_id, answer_chosen, score_snapshot FROM session_responses WHERE session_id=?", (ext_session_id,))
            responses = c_ext.fetchall()
            print(f"[IMPORT] Found {len(responses)} responses to copy")
            
            for i, row in enumerate(responses):
                c_main.execute("INSERT INTO session_responses (session_id, question_hash, axis_id, answer_chosen, score_snapshot) VALUES (?,?,?,?,?)",
                              (new_session_id, *row))
                if (i + 1) % 10 == 0:
                    print(f"[IMPORT] Copied {i + 1}/{len(responses)} responses...")
            
            print(f"[IMPORT] All {len(responses)} responses copied")
            
            # 5. Copiem audit trail (inclusiv detecțiile de monstru), dacă există
            print("[IMPORT] Checking for audit trail...")
            try:
                # Asigurăm tabelul session_audit în baza principală (schemă canonică,
                # compatibilă cu exam_engine, import și transcript)
                c_main.execute("""CREATE TABLE IF NOT EXISTS session_audit (
                    id INTEGER PRIMARY KEY,
                    session_id INTEGER, axis_id INTEGER, wave INTEGER,
                    decision_type TEXT, explanation TEXT,
                    question_text TEXT, question_hash TEXT
                )""")
                # Citim din pachet DOAR coloanele care există acolo (wave_target, nu question_text)
                c_ext.execute("SELECT axis_id, wave_target, decision_type, explanation FROM session_audit WHERE session_id=?", (ext_session_id,))
                audit_rows = c_ext.fetchall()
                print(f"[IMPORT] Found {len(audit_rows)} audit entries")
                for axis_id_a, wave_a, dtype_a, expl_a in audit_rows:
                    c_main.execute("INSERT INTO session_audit (session_id, axis_id, wave, decision_type, explanation) VALUES (?,?,?,?,?)",
                                  (new_session_id, axis_id_a, wave_a, dtype_a, expl_a))
                print(f"[IMPORT] Copied {len(audit_rows)} audit entries")
            except Exception as audit_err:
                print(f"[IMPORT] WARNING: Could not copy audit trail: {audit_err}")
            
            # 6. Calculăm scorurile finale direct
            print("[IMPORT] Calculating final scores...")
            
            # Obținem toate axele testate
            c_main.execute("SELECT DISTINCT axis_id FROM session_responses WHERE session_id=?", (new_session_id,))
            tested_axes = [row[0] for row in c_main.fetchall()]
            print(f"[IMPORT] Found {len(tested_axes)} tested axes")
            
            for axis_id in tested_axes:
                # Calculăm media scorurilor pentru această axă
                c_main.execute("SELECT score_snapshot FROM session_responses WHERE session_id=? AND axis_id=?", (new_session_id, axis_id))
                scores = [row[0] for row in c_main.fetchall()]
                
                if not scores:
                    continue
                
                # Rotunjim scorul la întreg
                final_score = round(sum(scores) / len(scores))
                
                # Confidența = (nr_întrebări / 10) * 100, max 100%
                confidence = min(100, round((len(scores) / 10.0) * 100))
                
                print(f"[IMPORT]   Axis {axis_id}: {len(scores)} responses, score={final_score}, conf={confidence}%")
                
                # Salvăm în session_results
                c_main.execute("INSERT INTO session_results (session_id, axis_id, final_score, confidence) VALUES (?,?,?,?)",
                              (new_session_id, axis_id, final_score, confidence))
                
                # ACTUALIZĂM CACHE-UL HOLISTIC
                print(f"[IMPORT]   Updating holistic cache for axis {axis_id}...")
                
                # CALCULEZ: Câte întrebări din această axă a răspuns în toate sesiunile
                # session_responses DEJA ARE axis_id direct!
                c_main.execute("""
                    SELECT COUNT(*)
                    FROM session_responses resp
                    JOIN sessions s ON resp.session_id = s.id
                    WHERE s.patient_id = ? AND resp.axis_id = ?
                """, (patient_id, axis_id))
                questions_used = c_main.fetchone()[0] or 0
                
                c_main.execute("""
                    INSERT INTO holistic_knowledge (patient_id, axis_id, latest_score, confidence, last_updated_at, source_session_id, questions_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(patient_id, axis_id) DO UPDATE SET
                        latest_score = excluded.latest_score,
                        confidence = excluded.confidence,
                        last_updated_at = excluded.last_updated_at,
                        source_session_id = excluded.source_session_id,
                        questions_used = excluded.questions_used
                """, (patient_id, axis_id, final_score, confidence, date_taken, new_session_id, questions_used))
                print(f"[IMPORT]   Cache updated for axis {axis_id} - {questions_used} questions used")
            
            print("[IMPORT] All scores calculated and cache updated")
            
            conn_main.commit()
            print("[IMPORT] Changes committed to main DB")
            
            conn_main.close()
            conn_ext.close()
            print("[IMPORT] Database connections closed")
            
            QMessageBox.information(self, "✅ Import Complet", 
                f"Testare importată cu succes!\n\nPacient: {patient_name}\nSesiune: {new_session_id}\nRăspunsuri: {len(responses)}")
            
            # Refresh
            print("[IMPORT] Refreshing patient list...")
            self.refresh_patients()
            
            # Reîncărcăm sesiunile pentru pacientul curent
            print("[IMPORT] Reloading sessions for current patient...")
            # Găsim pacientul în dropdown și îl selectăm
            for i in range(self.cmb_patient_select.count()):
                if self.cmb_patient_select.itemData(i) == patient_id:
                    self.cmb_patient_select.setCurrentIndex(i)
                    break
            
            # Forțăm reîncărcarea sesiunilor
            self.load_sessions_for_patient()
            
            # Notificăm Tab 1 să se refresh-eze
            print("[IMPORT] Notifying Tab 1 to refresh...")
            try:
                # Găsim main window-ul și tab-ul 1
                main_window = self.window()
                if hasattr(main_window, 'tab_widget'):
                    # Căutăm PatientsTab
                    for i in range(main_window.tab_widget.count()):
                        tab = main_window.tab_widget.widget(i)
                        if hasattr(tab, 'refresh_list') and hasattr(tab, 'load_patient_data'):
                            print(f"[IMPORT] Found PatientsTab at index {i}, triggering refresh...")
                            # Dacă pacientul este deja selectat în Tab 1, reîncărcăm datele
                            if hasattr(tab, 'current_patient_id') and tab.current_patient_id == patient_id:
                                tab.load_patient_data(patient_id)
                                print("[IMPORT] Tab 1 data reloaded for current patient")
                            break
            except Exception as e:
                print(f"[IMPORT] WARNING: Could not notify Tab 1: {e}")
            
            print("[IMPORT] Import complete!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"[IMPORT] CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Eroare Import", f"Eroare la import:\n{str(e)}")

