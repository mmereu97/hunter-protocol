import json
import os
from config import Config
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QLineEdit, QPushButton, QSplitter, QFrame, QTextEdit, 
    QScrollArea, QMessageBox, QComboBox, QAbstractItemView, QFileDialog,
    QApplication, 
    QDialog,        # <--- LIPSEA
    QTextBrowser    # <--- NECESAR PENTRU RAPORT
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from logic.patient_manager import PatientManager
from ai_agents.llm_connector import AIConnector
from logger import log
from ai_agents.profiler_agent import ProfilerAgent


# ==========================================
# 🎨 STIL CYBERPUNK (ERGONOMIC)
# ==========================================
PATIENT_STYLE = """
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    QLineEdit, QTextEdit, QComboBox {
        background-color: #1a1a1a; 
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 5px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 1px solid #00e5ff;
        background-color: #222;
    }
    QListWidget {
        background-color: #121212;
        color: #ffffff;
        border: 1px solid #444;
    }
    QListWidget::item:selected {
        background-color: #004d40;
        color: #00ff69;
        font-weight: bold;
    }
    QScrollArea { border: none; background-color: #0b0b0b; }
    QScrollBar:vertical { background: #111; width: 8px; }
    QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
    
    QPushButton {
        background-color: #1f1f1f;
        color: #ccc;
        border: 1px solid #444;
        padding: 6px;
        border-radius: 3px;
    }
    QPushButton:hover { background-color: #333; border: 1px solid #666; color: white; }
"""

# ==========================================
# 🎨 WIDGET CUSTOM: RIGLA HOLISTICĂ
# ==========================================
class HolisticRuler(QWidget):
    def __init__(self, axis_name, left_pole, right_pole, score, confidence, date_str, norm_mean=50, norm_std_dev=15, este_monstru=False, questions_used=0, questions_total=0):
        super().__init__()
        self.setFixedHeight(55)
        
        self.axis_name = axis_name
        self.left_pole = left_pole
        self.right_pole = right_pole
        self.raw_score = score
        self.confidence = confidence
        self.date_str = str(date_str)[:10] 
        self.este_monstru = este_monstru # Salvăm starea de monstru
        self.questions_used = questions_used
        self.questions_total = questions_total
        
        self.val_left = 100 - score
        self.val_right = score
        self.norm_mean = norm_mean
        self.norm_sd = norm_std_dev
        
        self.col_neon = QColor("#00e5ff")
        self.col_dim  = QColor("#444444")
        self.col_date = QColor("#888888")
        self.bg_track = QColor("#222222")
        self.norm_zone = QColor(0, 229, 255, 30)

        # Culori pentru marker în funcție de deviația de la normă
        dev = abs(score - norm_mean)
        if dev > (2 * norm_std_dev): self.marker_color = QColor("#ff0055") # Roșu alertă
        elif dev > norm_std_dev: self.marker_color = QColor("#ffcc00") # Galben
        else: self.marker_color = QColor("#00ff69") # Verde

        if confidence >= 80: self.acc_color = QColor("#00ff69")
        elif confidence >= 50: self.acc_color = QColor("#ffcc00")
        else: self.acc_color = QColor("#ff0055")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height(); cy = h / 2 + 5 
        
        # Lărgim badge-ul pentru a face loc textului cu întrebări: 50 → 120
        w_name_area = 180; w_side_text = 200; w_badge = 120; margin = 10
        rect_name = QRect(margin, 5, w_name_area, 20)
        rect_date = QRect(margin, 25, w_name_area, 20)
        rect_left = QRect(w_name_area + margin, 15, w_side_text, 30)
        x_ruler_start = w_name_area + w_side_text + (margin*2)
        # Scurtăm ruler-ul prin reducerea w_side_text (220→200) și mărirea w_badge (50→120)
        x_ruler_end = w - w_side_text - w_badge - (margin*2)
        ruler_width = x_ruler_end - x_ruler_start
        if ruler_width < 30: ruler_width = 30
        rect_right = QRect(x_ruler_end + margin, 15, w_side_text, 30)
        rect_badge = QRect(w - w_badge - margin, 15, w_badge, 20)

        is_left_dominant = self.raw_score <= 50
        font_main = QFont("Segoe UI", 9, QFont.Bold)
        font_dim = QFont("Segoe UI", 8, QFont.Normal)

        # --- MODIFICARE TITLU: DACĂ E MONSTRU, PUNEM ROȘU ---
        if self.este_monstru:
            p.setPen(QColor("#ff5252")) # Roșu aprins de tip Monstru
        else:
            p.setPen(QColor("white"))
            
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(rect_name, Qt.AlignLeft | Qt.AlignVCenter, self.axis_name)
        
        p.setPen(self.col_date); p.setFont(QFont("Consolas", 8))
        p.drawText(rect_date, Qt.AlignLeft | Qt.AlignVCenter, f"Last: {self.date_str}")
        
        str_left = f"{self.left_pole} {self.val_left}%"
        p.setPen(self.col_neon if is_left_dominant else self.col_dim)
        p.setFont(font_main if is_left_dominant else font_dim)
        p.drawText(rect_left, Qt.AlignRight | Qt.AlignVCenter, str_left)
        
        str_right = f"{self.val_right}% {self.right_pole}"
        p.setPen(self.col_neon if not is_left_dominant else self.col_dim)
        p.setFont(font_main if not is_left_dominant else font_dim)
        p.drawText(rect_right, Qt.AlignLeft | Qt.AlignVCenter, str_right)
        
        track_y = int(cy)
        p.setPen(QPen(self.bg_track, 2))
        p.drawLine(x_ruler_start, track_y, x_ruler_end, track_y)
        p.setPen(QPen(QColor("#333"), 1))
        for i in range(11):
            tx = x_ruler_start + (i * ruler_width / 10)
            p.drawLine(int(tx), track_y - 3, int(tx), track_y + 3)
            
        ns = max(0, self.norm_mean - self.norm_sd)
        ne = min(100, self.norm_mean + self.norm_sd)
        nx = x_ruler_start + (ns / 100 * ruler_width)
        nw = (ne - ns) / 100 * ruler_width
        p.setPen(Qt.NoPen); p.setBrush(self.norm_zone)
        p.drawRect(int(nx), track_y - 4, int(nw), 9)
        
        bx = x_ruler_start + (self.raw_score / 100 * ruler_width)
        p.setBrush(QColor(self.marker_color.red(), self.marker_color.green(), self.marker_color.blue(), 60))
        p.drawEllipse(int(bx - 8), int(track_y - 8), 16, 16)
        p.setBrush(self.marker_color)
        p.drawEllipse(int(bx - 5), int(track_y - 5), 10, 10)
        
        p.setBrush(QColor(self.acc_color.red(), self.acc_color.green(), self.acc_color.blue(), 30))
        p.setPen(QPen(self.acc_color, 1))
        p.drawRoundedRect(rect_badge, 4, 4)
        p.setFont(QFont("Consolas", 9, QFont.Bold)); p.setPen(self.acc_color)
        # Afișăm procentul de confidență + întrebări folosite/total
        text_badge = f"{self.confidence}% [{self.questions_used}/{self.questions_total}]"
        p.drawText(rect_badge, Qt.AlignCenter, text_badge)


class PatientsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = PatientManager()
        self.ai = AIConnector()
        # ADĂUGĂM ACEASTĂ LINIE:
        self.profiler_agent = ProfilerAgent() 
        
        self.current_patient_id = None
        self.setStyleSheet(PATIENT_STYLE)
        self.setup_ui()
        self.refresh_list()


    def showEvent(self, event):
        # RESTAURARE STARE: Restaurăm ultimul pacient selectat
        if not self.current_patient_id:
            from logic.settings_manager import SettingsManager
            settings = SettingsManager.load_settings()
            last_patient_id = settings.get("last_selected_patient_id")
            
            if last_patient_id:
                print(f"[TAB1 showEvent] Restoring last patient: {last_patient_id}")
                # Căutăm pacientul în listă și îl selectăm
                for i in range(self.patients_list.count()):
                    item = self.patients_list.item(i)
                    if item.data(Qt.UserRole) == last_patient_id:
                        self.patients_list.setCurrentItem(item)
                        self.on_patient_selected(item)
                        break
        
        self.refresh_list()
        if self.current_patient_id:
            self.load_holistic_matrix(self.current_patient_id)
        super().showEvent(event)

    def setup_ui(self):
        # Layout-ul principal al tab-ului este ORIZONTAL
        # Acesta separă zona de lucru (Stânga + Mijloc) de Bazinul Holistic (Dreapta)
        self.layout_principal_tab_pacienti = QHBoxLayout(self)
        self.layout_principal_tab_pacienti.setContentsMargins(5, 5, 5, 5)
        self.layout_principal_tab_pacienti.setSpacing(10)

        # =====================================================================
        # ZONA DIN STÂNGA ȘI MIJLOC (Containerul pentru Listă, Fișă și Consolă)
        # =====================================================================
        self.container_stanga_mijloc = QWidget()
        self.container_stanga_mijloc.setMaximumWidth(650) 
        self.layout_vertical_stanga_mijloc = QVBoxLayout(self.container_stanga_mijloc)
        self.layout_vertical_stanga_mijloc.setContentsMargins(0, 0, 0, 0)
        self.layout_vertical_stanga_mijloc.setSpacing(10)

        # --- PARTEA DE SUS (Splitter pentru Lista și Fișă) ---
        self.container_superior_informatie = QWidget()
        self.layout_superior_informatie = QHBoxLayout(self.container_superior_informatie)
        self.layout_superior_informatie.setContentsMargins(0, 0, 0, 0)
        self.layout_superior_informatie.setSpacing(10)

        # COLOANA 1: LISTA PACIENȚI
        self.panou_coloana_lista = QFrame()
        self.panou_coloana_lista.setFixedWidth(260)
        self.layout_coloana_lista = QVBoxLayout(self.panou_coloana_lista)
        self.layout_coloana_lista.setContentsMargins(5, 5, 5, 5)

        self.label_titlu_lista_pacienti = QLabel("👥 LISTA PACIENȚI:")
        self.layout_coloana_lista.addWidget(self.label_titlu_lista_pacienti)

        self.search_bar_pacienti = QLineEdit()
        self.search_bar_pacienti.setPlaceholderText("🔍 Caută subiect...")
        self.search_bar_pacienti.textChanged.connect(self.filter_list)
        self.layout_coloana_lista.addWidget(self.search_bar_pacienti)

        self.patients_list = QListWidget()
        self.patients_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.patients_list.itemClicked.connect(self.on_patient_selected)
        self.patients_list.itemChanged.connect(self.on_patient_check_changed)
        self.layout_coloana_lista.addWidget(self.patients_list)

        self.buton_pacient_nou_creare = QPushButton("➕ PACIENT NOU")
        self.buton_pacient_nou_creare.setStyleSheet("color: #00e5ff; border: 1px dashed #00e5ff; font-weight: bold;")
        self.buton_pacient_nou_creare.clicked.connect(self.prepare_new_patient)
        self.layout_coloana_lista.addWidget(self.buton_pacient_nou_creare)

        self.layout_rand_import_export = QHBoxLayout()
        self.buton_import_pachet_pacienti = QPushButton("📥 IMPORT")
        self.buton_import_pachet_pacienti.clicked.connect(self.import_patients_handler)
        self.buton_export_pachet_pacienti = QPushButton("📤 EXPORT")
        self.buton_export_pachet_pacienti.clicked.connect(self.export_patients_handler)
        self.layout_rand_import_export.addWidget(self.buton_import_pachet_pacienti)
        self.layout_rand_import_export.addWidget(self.buton_export_pachet_pacienti)
        self.layout_coloana_lista.addLayout(self.layout_rand_import_export)

        # COLOANA 2: FIȘA PERSONALĂ
        self.panou_coloana_fisa = QFrame()
        self.panou_coloana_fisa.setFixedWidth(350)
        self.layout_coloana_fisa = QVBoxLayout(self.panou_coloana_fisa)
        self.layout_coloana_fisa.setContentsMargins(5, 5, 5, 5)

        self.label_titlu_fisa_personala = QLabel("📝 FIȘA PERSONALĂ:")
        self.layout_coloana_fisa.addWidget(self.label_titlu_fisa_personala)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Numele complet al subiectului")
        self.layout_coloana_fisa.addWidget(self.inp_name)

        self.layout_rand_cnp_varsta = QHBoxLayout()
        self.label_eticheta_cnp = QLabel("CNP:")
        self.inp_cnp = QLineEdit()
        self.label_eticheta_varsta = QLabel("ANI:")
        self.inp_age = QLineEdit()
        self.inp_age.setFixedWidth(40)
        self.layout_rand_cnp_varsta.addWidget(self.label_eticheta_cnp)
        self.layout_rand_cnp_varsta.addWidget(self.inp_cnp)
        self.layout_rand_cnp_varsta.addWidget(self.label_eticheta_varsta)
        self.layout_rand_cnp_varsta.addWidget(self.inp_age)
        self.layout_coloana_fisa.addLayout(self.layout_rand_cnp_varsta)

        self.layout_rand_job_sex = QHBoxLayout()
        self.label_eticheta_job = QLabel("JOB:")
        self.inp_job = QLineEdit()
        self.label_eticheta_sex = QLabel("SEX:")
        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["M", "F", "N/A"])
        self.cmb_gender.setFixedWidth(60)
        self.layout_rand_job_sex.addWidget(self.label_eticheta_job)
        self.layout_rand_job_sex.addWidget(self.inp_job)
        self.layout_rand_job_sex.addWidget(self.label_eticheta_sex)
        self.layout_rand_job_sex.addWidget(self.cmb_gender)
        self.layout_coloana_fisa.addLayout(self.layout_rand_job_sex)

        # --- AJUSTARE VIZUALĂ: MĂRIM ZONA DE NOTE PENTRU A OCUPA SPAȚIUL GOL ---
        self.txt_notes = QTextEdit()
        self.txt_notes.setFixedHeight(220) # Mărit de la 100 la 220 pixeli
        self.layout_coloana_fisa.addWidget(QLabel("NOTE CLINICE:"))
        self.layout_coloana_fisa.addWidget(self.txt_notes)

        self.layout_rand_actiuni_fisa = QHBoxLayout()
        self.btn_save = QPushButton("💾 SALVEAZĂ")
        self.btn_save.setStyleSheet("background-color: #004d40; color: #00ff69; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_patient)
        self.btn_delete = QPushButton("🗑️ ȘTERGE")
        self.btn_delete.setStyleSheet("color: #ff5252;")
        self.btn_delete.clicked.connect(self.delete_patient)
        self.layout_rand_actiuni_fisa.addWidget(self.btn_save)
        self.layout_rand_actiuni_fisa.addWidget(self.btn_delete)
        self.layout_coloana_fisa.addLayout(self.layout_rand_actiuni_fisa)




        # -------------------------------------------------------------
        # BLOC NOU: CONTROALE AI (REARANJATE)
        # -------------------------------------------------------------
        self.panou_controale_ai_bloc = QFrame()
        self.panou_controale_ai_bloc.setStyleSheet("background-color: #1a1a1a; border: 1px solid #4a148c; border-radius: 5px; margin-top: 10px;")
        self.layout_controale_ai_bloc = QVBoxLayout(self.panou_controale_ai_bloc)
        
        self.cmb_ai_persona = QComboBox()
        self.cmb_ai_persona.addItems(["HR (Resurse Umane)", "Psych (Psiholog)", "Academic (Psihiatru)"])
        
        # --- SUBTILITATE 1: MEMORARE POZIȚIE COMBOBOX ---
        from logic.settings_manager import SettingsManager
        setari_actuale = SettingsManager.load_settings()
        index_salvat = setari_actuale.get("last_ai_persona_index", 0)
        self.cmb_ai_persona.setCurrentIndex(index_salvat)
        
        # Salvăm indexul automat în JSON ori de câte ori utilizatorul îl schimbă
        self.cmb_ai_persona.currentIndexChanged.connect(
            lambda index: SettingsManager.update_key("last_ai_persona_index", index)
        )
        # Verificăm starea butoanelor (dacă există raport salvat)
        self.cmb_ai_persona.currentIndexChanged.connect(self.update_ai_buttons_state)
        
        self.layout_controale_ai_bloc.addWidget(QLabel("🧠 PERSONALITATE AI:"))
        self.layout_controale_ai_bloc.addWidget(self.cmb_ai_persona)

        # RÂND 1: RAPORT NOU ȘI RAPORT SALVAT
        self.layout_rand_rapoarte = QHBoxLayout()
        self.buton_generare_raport_nou = QPushButton("📊 RAPORT NOU")
        self.buton_generare_raport_nou.setStyleSheet("background-color: #4a148c; color: white; font-weight: bold;")
        self.buton_generare_raport_nou.clicked.connect(self.run_group_analysis)
        
        self.buton_recitire_raport_salvat = QPushButton("📂 RAPORT SALVAT")
        self.buton_recitire_raport_salvat.clicked.connect(self.reciteste_raport_arhivat)
        
        self.layout_rand_rapoarte.addWidget(self.buton_generare_raport_nou)
        self.layout_rand_rapoarte.addWidget(self.buton_recitire_raport_salvat)
        self.layout_controale_ai_bloc.addLayout(self.layout_rand_rapoarte)




        self.layout_rand_edit_clear = QHBoxLayout()
        self.buton_editare_prompt_text = QPushButton("📝 EDIT PROMPT")
        self.buton_editare_prompt_text.clicked.connect(self.open_active_prompt_editor)
        
        self.buton_curata_chat_istoric = QPushButton("🧹 ȘTERGE CHAT")
        self.buton_curata_chat_istoric.clicked.connect(self.clear_ai_chat)
        
        self.layout_rand_edit_clear.addWidget(self.buton_editare_prompt_text)
        self.layout_rand_edit_clear.addWidget(self.buton_curata_chat_istoric)
        self.layout_controale_ai_bloc.addLayout(self.layout_rand_edit_clear)

        self.layout_coloana_fisa.addWidget(self.panou_controale_ai_bloc)
        self.layout_coloana_fisa.addStretch()

        # Asamblăm rândul superior
        self.layout_superior_informatie.addWidget(self.panou_coloana_lista)
        self.layout_superior_informatie.addWidget(self.panou_coloana_fisa)
        self.layout_vertical_stanga_mijloc.addWidget(self.container_superior_informatie, 2)

        # --- CONSOLA DE CHAT ---
        self.txt_ai_chat_log = QTextEdit()
        self.txt_ai_chat_log.setReadOnly(True)
        self.txt_ai_chat_log.setAcceptRichText(True)
        self.txt_ai_chat_log.setStyleSheet("background-color: #000; color: #00e5ff; font-family: 'Consolas'; border: 1px solid #333;")
        self.layout_vertical_stanga_mijloc.addWidget(self.txt_ai_chat_log, 1)

        # Input Chat
        self.layout_rand_input_chat = QHBoxLayout()
        self.inp_ai_chat = QLineEdit()
        self.inp_ai_chat.setPlaceholderText("Adresează o întrebare despre subiecții bifați...")
        self.inp_ai_chat.returnPressed.connect(self.send_ai_chat_message)
        
        self.buton_trimite_chat_mesaj = QPushButton("⚡")
        self.buton_trimite_chat_mesaj.setFixedWidth(50)
        self.buton_trimite_chat_mesaj.clicked.connect(self.send_ai_chat_message)
        
        self.layout_rand_input_chat.addWidget(self.inp_ai_chat)
        self.layout_rand_input_chat.addWidget(self.buton_trimite_chat_mesaj)
        self.layout_vertical_stanga_mijloc.addLayout(self.layout_rand_input_chat)

        # Adăugăm grupul stânga-mijloc în layout-ul principal

        self.layout_principal_tab_pacienti.addWidget(self.container_stanga_mijloc, 6)

        # =====================================================================
        # COLOANA 3: BAZIN HOLISTIC (Pe toată înălțimea, în dreapta)
        # =====================================================================
        self.panou_bazin_holistic_dreapta = QFrame()
        self.layout_bazin_holistic_dreapta = QVBoxLayout(self.panou_bazin_holistic_dreapta)
        self.layout_bazin_holistic_dreapta.setContentsMargins(5, 5, 5, 5)

        self.layout_antet_bazin_holistic = QHBoxLayout()
        self.layout_antet_bazin_holistic.addWidget(QLabel("🧬 BAZIN HOLISTIC (SUMA CUNOȘTINȚELOR)"))
        
        # --- BUTONUL AI PROFILER A FOST ELIMINAT DE AICI ---
        
        self.layout_bazin_holistic_dreapta.addLayout(self.layout_antet_bazin_holistic)

        self.scroll_area_matrice_holistica = QScrollArea()
        self.scroll_area_matrice_holistica.setWidgetResizable(True)
        self.container_matrice_axe = QWidget()
        self.matrix_layout = QVBoxLayout(self.container_matrice_axe)
        self.matrix_layout.setAlignment(Qt.AlignTop)
        self.matrix_layout.setSpacing(5)
        self.scroll_area_matrice_holistica.setWidget(self.container_matrice_axe)
        self.layout_bazin_holistic_dreapta.addWidget(self.scroll_area_matrice_holistica)

        self.buton_generare_dosar_istoric_complet = QPushButton("📚 DOSAR COMPLET (ISTORIC)")
        self.buton_generare_dosar_istoric_complet.setStyleSheet("background-color: #e65100; color: white; font-weight: bold; padding: 10px;")
        self.buton_generare_dosar_istoric_complet.clicked.connect(self.generate_full_history_report)
        self.layout_bazin_holistic_dreapta.addWidget(self.buton_generare_dosar_istoric_complet)

        self.layout_principal_tab_pacienti.addWidget(self.panou_bazin_holistic_dreapta, 4)

    # ==========================
    # LOGICA NOUA TAB 1
    # ==========================

    def on_patient_check_changed(self, item):
        """Metodă integrală care monitorizează bifele și loghează în consolă starea memoriei AI."""
        nume_pacient_lista = item.text()
        
        # Verificăm starea bifei (Qt.Checked sau Qt.Unchecked)
        if item.checkState() == Qt.Checked:
            mesaj_log = f"<p style='color: #888;'><i>[SYSTEM]: Dosar Pacient <b>{nume_pacient_lista}</b> încărcat în memoria activă de analiză.</i></p>"
        else:
            mesaj_log = f"<p style='color: #888;'><i>[SYSTEM]: Dosar Pacient <b>{nume_pacient_lista}</b> eliberat din memoria de analiză.</i></p>"
            
        # Adăugăm mesajul formatat în consolă
        self.txt_ai_chat_log.append(mesaj_log)

    def open_active_prompt_editor(self):
        """Metodă integrală care deschide fișierul text al promptului utilizat în editorul de sistem."""
        persona_selectata_prompt = self.cmb_ai_persona.currentText()
        
        # Identificăm numele fișierului corespunzător
        nume_fisier_prompt_activ = "analyze_hr.txt"
        if "Psych" in persona_selectata_prompt:
            nume_fisier_prompt_activ = "analyze_psych.txt"
        elif "Academic" in persona_selectata_prompt:
            nume_fisier_prompt_activ = "analyze_academic.txt"
        
        import os
        cale_catre_prompts = os.path.join("prompts", nume_fisier_prompt_activ)
        
        if os.path.exists(cale_catre_prompts):
            try:
                # Deschide fișierul folosind editorul implicit de text (Notepad, TextEdit etc.)
                os.startfile(cale_catre_prompts)
                self.txt_ai_chat_log.append(f"<p style='color: #888;'><i>[SYSTEM]: Deschis editor pentru prompt: {nume_fisier_prompt_activ}</i></p>")
            except Exception as eroare_deschidere:
                QMessageBox.warning(self, "Eroare", f"Nu s-a putut deschide fișierul: {str(eroare_deschidere)}")
        else:
            QMessageBox.warning(self, "Eroare", f"Fișierul de prompt nu a fost găsit la calea: {cale_catre_prompts}")


    def run_group_analysis(self):
        """Metodă integrală care generează raportul AI, îl afișează în consolă și îl salvează ca fișier .md."""
        # 1. Colectăm datele holistice pentru toți pacienții care au bifa pusă
        selected_patients_context = self.get_checked_patients_context()
        
        if not selected_patients_context:
            QMessageBox.warning(self, "Atenție", "Bifați cel puțin un pacient în listă pentru a genera un raport.")
            return

        # 2. Identificăm personalitatea AI selectată
        persona_curenta = self.cmb_ai_persona.currentText()
        cod_persona = "HR" if "HR" in persona_curenta else ("Psych" if "Psych" in persona_curenta else "Academic")
        
        # 3. Solicităm analiza de la ProfilerAgent
        self.txt_ai_chat_log.append(f"<p style='color: #e040fb;'><b>[AI]:</b> Generez raportul {cod_persona} pentru {len(selected_patients_context)} subiecți...</p>")
        
        # Această linie reparată forțează interfața să arate mesajul de mai sus înainte de a începe calculul greu
        QApplication.processEvents()
        
        raport_generat_markdown = self.profiler_agent.run_analysis(selected_patients_context, cod_persona)
        
        # 4. Afișăm raportul în consolă folosind formatarea Markdown
        self.txt_ai_chat_log.append(f"<h2>RAPORT PSIHOMETRIC - {persona_curenta}</h2>")
        # Conversie din Markdown în formatul vizual al consolei
        self.txt_ai_chat_log.setMarkdown(self.txt_ai_chat_log.toMarkdown() + "\n\n" + raport_generat_markdown)

        # 5. SALVARE ÎN SISTEMUL DE FIȘIERE (*.md în folderul fiecărui pacient bifat)
        import os
        from datetime import datetime
        
        for pacient_date in selected_patients_context:
            # Curățăm numele pentru a putea crea un folder valid pe disc
            nume_curatat_folder = "".join([c for c in pacient_date['name'] if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
            
            # Calea: pacienti / Nume_Pacient
            cale_director_pacient = os.path.join(Config.PATIENTS_DIR, nume_curatat_folder)
            
            if not os.path.exists(cale_director_pacient):
                os.makedirs(cale_director_pacient)
            
            # Nume fișier: Raport_Persona_Data_Ora.md
            timestamp_raport = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nume_fisier_raport = f"Raport_{cod_persona}_{timestamp_raport}.md"
            cale_finala_fisier = os.path.join(cale_director_pacient, nume_fisier_raport)
            
            try:
                with open(cale_finala_fisier, "w", encoding="utf-8") as fisier_raport:
                    fisier_raport.write(raport_generat_markdown)
                self.txt_ai_chat_log.append(f"<small style='color: #00ff69;'><i>Fisier salvat: {cale_finala_fisier}</i></small>")
            except Exception as eroare_salvare:
                self.txt_ai_chat_log.append(f"<small style='color: #ff5252;'><i>Eroare salvare: {str(eroare_salvare)}</i></small>")


    def update_ai_buttons_state(self):
        """Metodă integrală care verifică dacă există un raport salvat și schimbă culoarea butonului."""
        if not self.current_patient_id:
            self.buton_recitire_raport_salvat.setStyleSheet("")
            return

        persona_selectata = self.cmb_ai_persona.currentText()
        cod_persona = "HR" if "HR" in persona_selectata else ("Psych" if "Psych" in persona_selectata else "Academic")
        
        # Verificăm în bază dacă există raport
        raport_existent = self.manager.get_latest_report(self.current_patient_id, cod_persona)
        
        if raport_existent:
            # Butonul se aprinde (Neon Green border)
            self.buton_recitire_raport_salvat.setStyleSheet("""
                QPushButton {
                    background-color: #004d40; 
                    color: #00ff69; 
                    border: 2px solid #00ff69; 
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #00695c; }
            """)
        else:
            # Revenim la stilul normal (stins)
            self.buton_recitire_raport_salvat.setStyleSheet("")


    def export_patients_handler(self):
        """Metodă integrală care exportă pacienții bifați într-un fișier JSON (Pachet)."""
        pacienti_bifati_pentru_export = []
        for index_lista in range(self.patients_list.count()):
            element_lista = self.patients_list.item(index_lista)
            if element_lista.checkState() == Qt.Checked:
                pacienti_bifati_pentru_export.append(element_lista)
        
        if not pacienti_bifati_pentru_export:
            QMessageBox.warning(self, "Export", "Vă rugăm să bifați pacienții pe care doriți să îi includeți în pachetul de export.")
            return

        lista_date_complete_export = []
        for element_pacient in pacienti_bifati_pentru_export:
            id_db_pacient = element_pacient.data(Qt.UserRole)
            # Cerem managerului pachetul complet de date (Profil + Holistic + Sesiuni)
            set_date_pacient = self.manager.get_full_patient_data_for_export(id_db_pacient)
            lista_date_complete_export.append(set_date_pacient)

        cale_salvare_json, _ = QFileDialog.getSaveFileName(self, "Salvează Pachet Export", "", "JSON Files (*.json)")
        
        if cale_salvare_json:
            try:
                with open(cale_salvare_json, "w", encoding="utf-8") as fisier_json_export:
                    json.dump(lista_date_complete_export, fisier_json_export, indent=4)
                QMessageBox.information(self, "Succes", f"Pachetul conținând {len(lista_date_complete_export)} pacienți a fost salvat cu succes.")
            except Exception as eroare_json:
                QMessageBox.critical(self, "Eroare", f"Eșec la scrierea fișierului: {str(eroare_json)}")

    def import_patients_handler(self):
        """Metodă integrală care importă pacienți dintr-un pachet JSON."""
        cale_fisier_import_json, _ = QFileDialog.getOpenFileName(self, "Selectează Pachet Import", "", "JSON Files (*.json)")
        
        if not cale_fisier_import_json:
            return

        try:
            with open(cale_fisier_import_json, "r", encoding="utf-8") as fisier_import:
                date_importate_pachet = json.load(fisier_import)
            
            numar_succese = 0
            # Aici iterăm prin pachet și chemăm o metodă din manager pentru a reconstrui tabelele
            # Aceasta este o logică complexă ce necesită suport în PatientManager
            # Momentan confirmăm citirea datelor.
            QMessageBox.information(self, "Import", f"Pachetul conține {len(date_importate_pachet)} dosare. Această funcție va popula baza de date în pasul următor.")
            self.refresh_list()
        except Exception as eroare_import:
            QMessageBox.critical(self, "Eroare Import", f"Fișierul selectat nu este valid: {str(eroare_import)}")



    def send_ai_chat_message(self):
        """Trimite mesajul din consolă către AI luând în considerare contextul grupului."""
        mesaj_utilizator = self.inp_ai_chat.text().strip()
        if not mesaj_utilizator:
            return
            
        context_pacienti = self.get_selected_patients_context()
        
        if not context_pacienti:
            self.txt_ai_chat_log.append("<b style='color: #ff5252;'> Hunter System:</b> Vă rugăm să selectați cel puțin un pacient din listă (folosiți Ctrl+Click).")
            return

        # Afișăm mesajul tău în consolă
        self.txt_ai_chat_log.append(f"<b style='color: #ffffff;'>DOMNULE SPECIALIST:</b> {mesaj_utilizator}")
        self.inp_ai_chat.clear()
        
        # Identificăm personalitatea selectată (HR, Psych sau Academic)
        personalitate_text_complet = self.cmb_ai_persona.currentText()
        # Extragem doar prefixul (HR, Psych sau Academic)
        if "HR" in personalitate_text_complet: personalitate_cod = "HR"
        elif "Psych" in personalitate_text_complet: personalitate_cod = "Psych"
        else: personalitate_cod = "Academic"
        
        # Generăm răspunsul prin intermediul agentului
        raspuns_ai = self.profiler_agent.chat_step(mesaj_utilizator, context_pacienti, personalitate_cod)
        
        self.txt_ai_chat_log.append(f"<b style='color: #e040fb;'>HUNTER AI [{personalitate_cod}]:</b> {raspuns_ai}<br>")

    


    def format_text_pentru_raport(self, text_brut):
        # Convertim Markdown-ul simplu în HTML cu culori specifice Hunter
        text_html = text_brut.replace("\n", "<br>")
        # Exemplu: Orice cifră sau procent îl facem albastru deschis (ca în poza ta)
        import re
        text_html = re.sub(r'(\d+%)', r'<b style="color: #00e5ff;">\1</b>', text_html)
        # Paragrafele importante
        text_html = f"<div style='color: #e0e0e0; line-height: 1.6;'>{text_html}</div>"
        return text_html

    def reciteste_raport_arhivat(self):
        """Metodă integrală care încarcă raportul din baza de date fără a apela AI-ul."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "Atenție", "Selectați un pacient pentru a-i citi arhiva.")
            return

        persona_selectata = self.cmb_ai_persona.currentText()
        cod_persona = "HR" if "HR" in persona_selectata else ("Psych" if "Psych" in persona_selectata else "Academic")
        
        raport_existent = self.manager.get_latest_report(self.current_patient_id, cod_persona)
        
        if raport_existent:
            # Folosim ReportWindow pentru a afișa textul arhivat
            fereastra_raport = ReportWindow(
                titlu=f"ARHIVĂ RAPORT - {persona_selectata}",
                continut_html=raport_existent,
                id_pacient_pentru_salvare=self.current_patient_id,
                persona=cod_persona,
                manager_pacienti=self.manager,
                parinte=self
            )
            fereastra_raport.exec()
        else:
            QMessageBox.information(self, "Info", f"Nu există niciun raport salvat pentru persona {cod_persona} la acest subiect.")



    def clear_ai_chat(self):
        """Curăță consola vizuală și resetează istoricul de memorie al agentului AI."""
        self.txt_ai_chat_log.clear()
        self.profiler_agent.clear_history()
        self.txt_ai_chat_log.append("<i style='color: #555;'>Memoria AI a fost resetată.</i>")


    def get_checked_patients_context(self):
        """Metodă integrală care colectează datele holistice doar pentru pacienții bifați (checkbox)."""
        lista_context_pacienti = []
        
        # Iterăm prin toate elementele din lista vizuală
        for index in range(self.patients_list.count()):
            element_lista = self.patients_list.item(index)
            
            # Verificăm dacă pătrățelul (checkbox) este bifat (Qt.Checked)
            if element_lista.checkState() == Qt.Checked:
                id_pacient = element_lista.data(Qt.UserRole)
                
                # Obținem datele holistice din baza de date pentru acest pacient
                date_profil_holistic = self.manager.get_holistic_profile(id_pacient)
                
                informatii_pacient = {
                    "id": id_pacient,
                    "name": element_lista.text(),
                    "holistic": [
                        {"name": rand[0], "score": rand[1], "confidence": rand[2]} 
                        for rand in date_profil_holistic
                    ]
                }
                lista_context_pacienti.append(informatii_pacient)
                
        return lista_context_pacienti

    def send_ai_chat_message(self):
        """Metodă integrală care trimite mesajul din consolă către AI folosind contextul pacienților bifați."""
        mesaj_utilizator = self.inp_ai_chat.text().strip()
        if not mesaj_utilizator:
            return
            
        # Folosim noua metodă bazată pe bife
        context_pacienti = self.get_checked_patients_context()
        
        if not context_pacienti:
            self.txt_ai_chat_log.append("<b style='color: #ff5252;'> Hunter System:</b> Vă rugăm să bifați cel puțin un pacient în listă pentru a iniția conversația.")
            return

        # Afișăm mesajul tău în consolă cu formatare
        self.txt_ai_chat_log.append(f"<p style='color: #ffffff;'><b>DOMNULE SPECIALIST:</b> {mesaj_utilizator}</p>")
        self.inp_ai_chat.clear()
        
        # Identificăm persona selectată
        personalitate_text = self.cmb_ai_persona.currentText()
        cod_persona = "HR" if "HR" in personalitate_text else ("Psych" if "Psych" in personalitate_text else "Academic")
        
        # Generăm răspunsul prin intermediul agentului
        raspuns_ai = self.profiler_agent.chat_step(mesaj_utilizator, context_pacienti, cod_persona)
        
        # Afișăm răspunsul în consolă folosind setMarkdown pentru a interpreta formatarea de la AI
        self.txt_ai_chat_log.append(f"<b style='color: #e040fb;'>HUNTER AI [{cod_persona}]:</b>")
        self.txt_ai_chat_log.setMarkdown(self.txt_ai_chat_log.toMarkdown() + "\n" + raspuns_ai + "\n---")
        
        # Scroll automat la final
        cursor = self.txt_ai_chat_log.textCursor()
        cursor.movePosition(cursor.End)
        self.txt_ai_chat_log.setTextCursor(cursor)

    def run_group_analysis(self):
        """Metodă integrală care generează raportul AI în fereastră nouă și îl salvează pe disc."""
        # 1. Colectăm contextul folosind bifele
        selected_patients_context = self.get_checked_patients_context()
        
        if not selected_patients_context:
            QMessageBox.warning(self, "Atenție", "Bifați cel puțin un pacient în listă (căsuța din stânga) pentru a genera un raport.")
            return

        # 2. Identificăm personalitatea AI selectată
        persona_curenta = self.cmb_ai_persona.currentText()
        cod_persona = "HR" if "HR" in persona_curenta else ("Psych" if "Psych" in persona_curenta else "Academic")
        
        # 3. Mesaj de status în consolă
        self.txt_ai_chat_log.append(f"<p style='color: #e040fb;'><b>[SYSTEM]:</b> Se procesează raportul {cod_persona} pentru {len(selected_patients_context)} subiecți...</p>")
        QApplication.processEvents()
        
        try:
            # 4. Solicităm analiza de la ProfilerAgent
            raport_generat_markdown = self.profiler_agent.run_analysis(selected_patients_context, cod_persona)
            
            # 5. Formatăm textul pentru fereastra de raport (convertim în HTML)
            continut_html = self.format_text_pentru_raport(raport_generat_markdown)
            
            # Identificăm dacă e un singur pacient pentru a permite arhivarea în DB
            id_pentru_salvare = selected_patients_context[0]['id'] if len(selected_patients_context) == 1 else None
            
            # 6. Deschidem fereastra de raport stilizată
            fereastra_raport = ReportWindow(
                titlu=f"RAPORT HUNTER PROTOCOL - {persona_curenta}",
                continut_html=continut_html,
                id_pacient_pentru_salvare=id_pentru_salvare,
                persona=cod_persona,
                manager_pacienti=self.manager,
                parinte=self
            )
            fereastra_raport.exec()

            # 7. Salvare pe disc în folderul pacienților
            import os
            from datetime import datetime
            for pacient_date in selected_patients_context:
                nume_dosar = pacient_date['name'].replace(" ", "_")
                cale_folder = os.path.join(Config.PATIENTS_DIR, nume_dosar)
                if not os.path.exists(cale_folder):
                    os.makedirs(cale_folder)
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                cale_fisier = os.path.join(cale_folder, f"Raport_{cod_persona}_{timestamp}.md")
                with open(cale_fisier, "w", encoding="utf-8") as f:
                    f.write(raport_generat_markdown)
            
            self.txt_ai_chat_log.append("<p style='color: #00ff69;'><b>[SYSTEM]:</b> Raport generat și arhivat cu succes.</p>")
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare AI", f"Eroare la generarea raportului: {str(e)}")


    # ==========================
    # LOGICA
    # ==========================
    def refresh_list(self):
        # Curățăm lista existentă
        self.patients_list.clear()
        
        # Luăm toți pacienții din manager
        lista_pacienti = self.manager.get_all_patients()
        
        for date_pacient in lista_pacienti:
            id_db, nume_complet, varsta, ocupatie, cnp_hash = date_pacient
            
            # Creăm textul de afișare
            text_afisat = f"{nume_complet} ({varsta})"
            element_lista = QListWidgetItem(text_afisat)
            
            # Adăugăm ID-ul pentru referințe viitoare
            element_lista.setData(Qt.UserRole, id_db)
            
            # --- ACTIVARE BIFE (CHECKBOX) ---
            element_lista.setFlags(element_lista.flags() | Qt.ItemIsUserCheckable)
            element_lista.setCheckState(Qt.Unchecked)
            
            element_lista.setToolTip(f"Ocupație: {ocupatie}\nID: {cnp_hash}")
            self.patients_list.addItem(element_lista)
    
    def filter_list(self, text):
        for i in range(self.patients_list.count()):
            item = self.patients_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def prepare_new_patient(self):
        self.current_patient_id = None; self.inp_name.clear(); self.inp_cnp.clear(); self.inp_age.clear(); self.inp_job.clear(); self.txt_notes.clear(); self.clear_matrix(); self.inp_cnp.setReadOnly(False)
    
    def save_patient(self):
        name = self.inp_name.text(); cnp = self.inp_cnp.text()
        if not name or not cnp: QMessageBox.warning(self, "Eroare", "Numele și CNP-ul sunt obligatorii!"); return
        try: age = int(self.inp_age.text())
        except: age = 0
        if self.current_patient_id: QMessageBox.information(self, "Info", "Editare neimplementată.")
        else:
            if self.manager.add_patient(name, cnp, age, self.cmb_gender.currentText(), self.inp_job.text(), self.txt_notes.toPlainText()):
                self.refresh_list(); self.prepare_new_patient(); QMessageBox.information(self, "Succes", "Pacient înregistrat.")
            else: QMessageBox.critical(self, "Eroare", "CNP duplicat.")
    
    def on_patient_selected(self, item):
        """Metodă integrală care populează fișa personală și încarcă bazinul holistic la click."""
        # 1. Extragem ID-ul pacientului salvat în obiectul din listă
        id_pacient_selectat = item.data(Qt.UserRole)
        self.current_patient_id = id_pacient_selectat
        
        # SALVARE STARE: Memorăm ultimul pacient selectat
        from logic.settings_manager import SettingsManager
        SettingsManager.update_key("last_selected_patient_id", id_pacient_selectat)
        
        # SINCRONIZARE GLOBALĂ: Notificăm celelalte tab-uri
        main_window = self.window()
        if hasattr(main_window, 'sync_patient_selection'):
            main_window.sync_patient_selection(id_pacient_selectat, 'tab_patients')
        
        # 2. Interogăm managerul pentru a obține detaliile brute din baza de date
        date_pacient = self.manager.get_patient_details(id_pacient_selectat)
        
        if date_pacient:
            # d[2] = Nume Complet, d[1] = CNP Hash, d[3] = Vârstă, d[4] = Gen, d[5] = Job, d[6] = Note
            self.inp_name.setText(str(date_pacient[2]))      # Nume Complet
            self.inp_cnp.setText(str(date_pacient[1]))       # CNP (Hash Mascat)
            self.inp_cnp.setReadOnly(True)                   # Blocăm editarea CNP-ului existent pentru integritate
            
            self.inp_age.setText(str(date_pacient[3]))       # Vârstă
            self.inp_job.setText(str(date_pacient[5]))       # Ocupație
            
            # Setăm Genul în ComboBox (M, F sau N/A)
            index_gender = self.cmb_gender.findText(str(date_pacient[4]))
            if index_gender >= 0:
                self.cmb_gender.setCurrentIndex(index_gender)
                
            self.txt_notes.setText(str(date_pacient[6]))     # Note Clinice
            
            # 3. Actualizăm vizual Bazinul Holistic (Graficele din dreapta)
            self.load_holistic_matrix(id_pacient_selectat)

            # 4. Verificăm dacă există rapoarte salvate pentru a aprinde sau stinge butonul "RAPORT SALVAT"
            self.update_ai_buttons_state()
    
    def clear_matrix(self):
        while self.matrix_layout.count():
            item = self.matrix_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_holistic_matrix(self, pid):
        self.clear_matrix()
        date_brute = self.manager.get_holistic_profile(pid)
        
        if not date_brute: 
            lbl = QLabel("Niciun test efectuat."); lbl.setAlignment(Qt.AlignCenter); self.matrix_layout.addWidget(lbl); return

        # Datele vin deja sortate din DB: alfabetic, monștrii la final
        for rand in date_brute:
            # Despachetare sigură a celor 13 coloane (acum include axis_id la început)
            axis_id, name, score, conf, date, cat, left, right, n_mean, n_sd, este_monstru, total_q, used_q = rand
            
            if n_mean is None: n_mean = 50
            if n_sd is None: n_sd = 15
            if total_q is None: total_q = 0
            if used_q is None: used_q = 0
            
            # 🔍 DEBUG: Afișează detalii pentru fiecare axă (doar dacă e activat în logger.py)
            from logger import log, LOG_CONFIG
            
            if LOG_CONFIG.get("holistic_debug", False):
                # Obținem toate sesiunile care au testat această axă
                import sqlite3
                from config import Config
                conn_debug = sqlite3.connect(Config.DB_NAME)
                c_debug = conn_debug.cursor()
                
                # DEBUGGING: Afișez schema tabelelor pentru a vedea ce coloane există
                log("holistic_debug", f"AXA ID {axis_id:03d} - {name}", "=" * 80)
                c_debug.execute("PRAGMA table_info(session_responses)")
                cols_resp = c_debug.fetchall()
                log("holistic_debug", f"Schema session_responses: {[col[1] for col in cols_resp]}")
                
                c_debug.execute("PRAGMA table_info(questions_bank)")
                cols_qb = c_debug.fetchall()
                log("holistic_debug", f"Schema questions_bank: {[col[1] for col in cols_qb]}")
                
                # Toate sesiunile pacientului cu această axă
                c_debug.execute("""
                    SELECT 
                        s.id,
                        s.date_taken,
                        sr.final_score,
                        sr.confidence
                    FROM sessions s
                    JOIN session_results sr ON s.id = sr.session_id
                    WHERE s.patient_id = ? AND sr.axis_id = ?
                    ORDER BY s.date_taken DESC
                """, (pid, axis_id))
                
                sessions_data = c_debug.fetchall()
                
                log("holistic_debug", f"Teste în care apare ({len(sessions_data)} teste):")
                
                for sess_id, date_taken, sess_score, sess_conf in sessions_data:
                    date_short = date_taken[:16] if date_taken else "N/A"
                    
                    # Număr întrebările pentru această axă în această sesiune
                    # session_responses DEJA ARE axis_id!
                    c_debug.execute("""
                        SELECT COUNT(*)
                        FROM session_responses resp
                        WHERE resp.session_id = ? AND resp.axis_id = ?
                    """, (sess_id, axis_id))
                    q_count = c_debug.fetchone()[0]
                    log("holistic_debug", f"  • Test #{sess_id} ({date_short}): {q_count} întrebări, scor={sess_score}, conf={sess_conf}%")
                
                # Calculez CUMUL REAL direct aici pentru verificare
                c_debug.execute("""
                    SELECT COUNT(*)
                    FROM session_responses resp
                    JOIN sessions s ON resp.session_id = s.id
                    WHERE s.patient_id = ? AND resp.axis_id = ?
                """, (pid, axis_id))
                real_count = c_debug.fetchone()[0]
                log("holistic_debug", f"Număr REAL din DB: {real_count} întrebări")
                
                conn_debug.close()
                
                log("holistic_debug", f"TOTAL TAB 1: {conf}% - {used_q}/{total_q} întrebări (din cache)")
                if str(real_count) != str(used_q):
                    log("holistic_debug", f"⚠️  DISCREPANȚĂ: Cache={used_q}, DB Real={real_count}")
                log("holistic_debug", "=" * 80)
            
            # Creăm rigla cu toate parametrii
            ruler = HolisticRuler(
                name, left, right, score, conf, date, 
                n_mean, n_sd, este_monstru=(este_monstru > 0),
                questions_used=used_q, questions_total=total_q
            )
            self.matrix_layout.addWidget(ruler)


    def run_ai_profiler(self):
        """Metodă integrală pentru butonul rapid de AI Profiler din panoul drept."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "Atenție", "Selectați un pacient din listă pentru profilare rapidă.")
            return

        # În loc de self.ai_output care nu mai există, scriem în consolă
        self.txt_ai_chat_log.append("<p style='color: #e040fb;'><i>Analiză rapidă în curs...</i></p>")
        QApplication.processEvents()

        # Colectăm datele pacientului curent
        d = self.manager.get_patient_details(self.current_patient_id)
        nume_pacient = d[2]
        profil_holistic = self.manager.get_holistic_profile(self.current_patient_id)
        
        context_pacient = [{
            "id": self.current_patient_id,
            "name": nume_pacient,
            "holistic": [{"name": r[0], "score": r[1], "confidence": r[2]} for r in profil_holistic]
        }]

        # Rulăm o analiză rapidă folosind persona implicită (Psych)
        raspuns_ai = self.profiler_agent.run_analysis(context_pacient, "Psych")
        
        self.txt_ai_chat_log.append(f"<h3>PROFIL RAPID: {nume_pacient}</h3>")
        self.txt_ai_chat_log.append(raspuns_ai)
    
    def delete_patient(self):
        if not self.current_patient_id: return
        if QMessageBox.question(self, "STERGE", "Sigur?") == QMessageBox.Yes:
            self.manager.delete_patient(self.current_patient_id); self.refresh_list(); self.prepare_new_patient()

    # ==========================
    # LOGICA DOSAR COMPLET (MODIFICAT PT NUMEROTARE)
    # ==========================
    def generate_full_history_report(self):
        """Metodă integrală: Dosar istoric pe disc cu reparație pentru prefixe ABCD."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "Eroare", "Selectați un pacient.")
            return

        nume_raw = self.inp_name.text()
        nume_curatat = "".join([c for c in nume_raw if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        cale_dir = os.path.join(Config.PATIENTS_DIR, nume_curatat)
        if not os.path.exists(cale_dir): os.makedirs(cale_dir)

        conn = self.manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.timestamp, q.text_content, r.answer_chosen, r.score_snapshot, r.question_hash,
                   a.name, q.wave_target, a.source_system
            FROM session_responses r
            JOIN questions_bank q ON r.question_hash = q.version_hash
            JOIN sessions s ON r.session_id = s.id
            JOIN axes a ON q.axis_id = a.id
            WHERE s.patient_id = ? ORDER BY r.timestamp DESC
        """, (self.current_patient_id,))
        
        rows = cursor.fetchall()
        if not rows: conn.close(); return

        harta_L = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        text_out = f"DOSAR ISTORIC COMPLET: {nume_raw}\n" + "="*70 + "\n\n"
        
        current_date = ""
        for idx, (ts, q_txt, ans_idx, score, q_hash, a_name, wave, src) in enumerate(rows, 1):
            date_str = str(ts)[:10]
            if date_str != current_date:
                text_out += f"\n--- DATA: {date_str} ---\n\n"
                current_date = date_str
            
            text_out += f"#{idx}. Axa: {a_name} | Sursa: {src}\nQ: {q_txt}\n"
            
            cursor.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash = ? ORDER BY option_index", (q_hash,))
            try: sel_litera = harta_L.get(int(ans_idx), "?")
            except: sel_litera = "?"
            
            for o_idx, o_txt, o_pts in cursor.fetchall():
                mark = "[X]" if o_idx == sel_litera else "[ ]"
                
                # REPARARE PREFIX DUBLU
                clean_opt = o_txt
                if not clean_opt.startswith(f"{o_idx})"):
                    clean_opt = f"{o_idx}) {clean_opt}"
                    
                text_out += f"   {mark} {clean_opt} ({o_pts} pts)\n"
            text_out += f"   >> IMPACT: {score} pct.\n" + "-"*50 + "\n\n"

        conn.close()
        cale_save = os.path.join(cale_dir, f"Dosar_Complet_{nume_curatat}.txt")
        filename, _ = QFileDialog.getSaveFileName(self, "Salvează Dosar", cale_save, "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f: f.write(text_out)

    def create_reports_table(self):
        """Creează tabela pentru stocarea rapoartelor AI dacă nu există."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS ai_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    persona TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(patient_id) REFERENCES patients(id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def save_ai_report(self, patient_id, persona, content):
        """Salvează sau actualizează raportul pentru un pacient și o persona specifică."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # Verificăm dacă există deja un raport pentru această persona la acest pacient
            c.execute("SELECT id FROM ai_reports WHERE patient_id = ? AND persona = ?", (patient_id, persona))
            row = c.fetchone()
            
            if row:
                c.execute("UPDATE ai_reports SET content = ?, created_at = datetime('now') WHERE id = ?", (content, row[0]))
            else:
                c.execute("INSERT INTO ai_reports (patient_id, persona, content) VALUES (?, ?, ?)", (patient_id, persona, content))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Eroare salvare raport: {e}")
            return False
        finally:
            conn.close()

    def get_latest_report(self, patient_id, persona):
        """Recuperează conținutul raportului salvat."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT content FROM ai_reports WHERE patient_id = ? AND persona = ?", (patient_id, persona))
            row = c.fetchone()
            return row[0] if row else None
        finally:
            conn.close()



    def set_selected_patient(self, patient_id, from_sync=False):
        """
        Setează pacientul selectat (folosit pentru sincronizare între tab-uri)
        @param patient_id: ID-ul pacientului
        @param from_sync: True dacă apelat din sincronizare (evită loop infinit)
        """
        print(f"[TAB1] set_selected_patient({patient_id}, from_sync={from_sync})")
        
        # Verificăm dacă Tab 1 e complet inițializat
        if not hasattr(self, 'patients_list') or not hasattr(self, 'manager'):
            print(f"[TAB1] Tab not fully initialized yet, skipping sync")
            return
        
        # Căutăm pacientul în listă
        for i in range(self.patients_list.count()):
            item = self.patients_list.item(i)
            if item.data(Qt.UserRole) == patient_id:
                # Selectăm item-ul
                self.patients_list.setCurrentItem(item)
                
                # BIFĂM CHECKBOX-UL (cerință: bifa pe pacientul selectat)
                item.setCheckState(Qt.Checked)
                
                # Încărcăm datele pacientului
                self.current_patient_id = patient_id
                date_pacient = self.manager.get_patient_details(patient_id)
                
                if date_pacient:
                    self.inp_name.setText(str(date_pacient[2]))
                    self.inp_cnp.setText(str(date_pacient[1]))
                    self.inp_cnp.setReadOnly(True)
                    self.inp_age.setText(str(date_pacient[3]))
                    self.inp_job.setText(str(date_pacient[5]))
                    
                    index_gender = self.cmb_gender.findText(str(date_pacient[4]))
                    if index_gender >= 0:
                        self.cmb_gender.setCurrentIndex(index_gender)
                    
                    self.txt_notes.setText(str(date_pacient[6]))
                    self.load_holistic_matrix(patient_id)
                    self.update_ai_buttons_state()
                
                # Dacă nu vine din sync, notificăm celelalte tab-uri
                if not from_sync:
                    main_window = self.window()
                    if hasattr(main_window, 'sync_patient_selection'):
                        main_window.sync_patient_selection(patient_id, 'tab_patients')
                
                print(f"[TAB1] Patient {patient_id} selected and checked successfully")
                break


class ReportWindow(QDialog):
    def __init__(self, titlu, continut_html, id_pacient_pentru_salvare, persona, manager_pacienti, parinte=None):
        super().__init__(parinte)
        self.setWindowTitle(titlu)
        self.setMinimumSize(900, 700)
        self.id_pacient = id_pacient_pentru_salvare
        self.continut_raport = continut_html
        self.persona = persona
        self.manager = manager_pacienti
        
        # Stilistică Cyberpunk / Hunter Protocol
        self.setStyleSheet("""
            QDialog { background-color: #0b0b0b; border: 2px solid #007acc; }
            QTextBrowser { 
                background-color: #050505; 
                color: #e0e0e0; 
                font-family: 'Segoe UI'; 
                font-size: 15px; 
                border: none;
                padding: 20px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
            }
            QPushButton#SaveButton { background-color: #004d40; border: 1px solid #00ff69; }
            QPushButton#CloseButton { background-color: #333; }
        """)
        
        layout_fereastra = QVBoxLayout(self)
        
        # Titlu mare sus
        self.label_header = QLabel("RAPORT PSIHOMETRIC FINAL")
        self.label_header.setAlignment(Qt.AlignCenter)
        self.label_header.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout_fereastra.addWidget(self.label_header)
        
        # Zona de afișare text cu formatare
        self.browser_text = QTextBrowser()
        self.browser_text.setHtml(continut_html)
        layout_fereastra.addWidget(self.browser_text)
        
        # Butoane Jos
        layout_butoane = QHBoxLayout()
        
        self.buton_arhiveaza = QPushButton("💾 SALVEAZĂ ACEST DOSAR ÎN BAZĂ")
        self.buton_arhiveaza.setObjectName("SaveButton")
        self.buton_arhiveaza.clicked.connect(self.salveaza_si_inchide)
        
        self.buton_inchide = QPushButton("ÎNCHIDE")
        self.buton_inchide.setObjectName("CloseButton")
        self.buton_inchide.clicked.connect(self.close)
        
        layout_butoane.addWidget(self.buton_arhiveaza)
        layout_butoane.addWidget(self.buton_inchide)
        
        layout_fereastra.addLayout(layout_butoane)

    def salveaza_si_inchide(self):
        """Salvează raportul în DB și trimite semnal către tab-ul părinte să actualizeze butonul."""
        if self.id_pacient:
            succes = self.manager.save_ai_report(self.id_pacient, self.persona, self.continut_raport)
            if succes:
                QMessageBox.information(self, "Succes", "Raportul a fost arhivat.")
                # Dacă părintele are metoda de update, o apelăm să se aprindă butonul imediat
                if hasattr(self.parent(), 'update_ai_buttons_state'):
                    self.parent().update_ai_buttons_state()
                self.close()

