from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QProgressBar, QFrame, QMessageBox, QStackedWidget,
    QSplitter, QListWidget, QListWidgetItem  # <--- ACESTEA LIPSEAU
)
from PySide6.QtCore import Qt
from logic.exam_engine import ExamEngine
from logic.patient_manager import PatientManager
from logic.architect_manager import ArchitectManager
from logger import log

# ==========================================
# 🎨 STIL CYBERPUNK (EXAMEN FIX) - REPARAT SELECTOR
# ==========================================
EXAM_STYLE = """
    /* BAZA */
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }

    /* MENIURILE DERULANTE (COMBOBOX) */
    QComboBox {
        background-color: #1a1a1a;
        color: #00e5ff;
        border: 1px solid #444;
        border-radius: 5px;
        padding: 8px;
        font-size: 14px;
        font-weight: bold;
    }

    /* TEXT ÎNTREBARE */
    QLabel#QuestionText { 
        font-size: 26px; 
        color: #ffcc00; 
        font-weight: bold; 
        margin: 20px; 
    }
    
    /* BUTOANE RĂSPUNS - FOLOSIM # PENTRU OBJECT NAME */
    QPushButton#OptionBtn {
        background-color: #1a1a1a;
        color: #ddd;
        border: 2px solid #444;
        border-radius: 10px;
        padding: 20px;
        font-size: 24px;     /* Am pus 24px pentru impact maxim */
        text-align: left;
        min-height: 60px;    /* Forțăm o înălțime minimă pentru a acomoda textul mare */
    }
    
    QPushButton#OptionBtn:hover {
        background-color: #333;
        border-color: #00e5ff;
        color: white;
    }
    
    /* PROGRESS BAR */
    QProgressBar {
        border: 1px solid #444;
        border-radius: 5px;
        text-align: center;
        background-color: #111;
        color: white;
        font-weight: bold;
    }
    QProgressBar::chunk { background-color: #00e5ff; }
"""

class ExamTab(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = ExamEngine()
        self.patient_mgr = PatientManager()
        self.arch_mgr = ArchitectManager()
        
        self.setStyleSheet(EXAM_STYLE)
        self.setup_ui()

    def showEvent(self, event):
        """
        AUTO-REFRESH: Această funcție se activează singură
        de fiecare dată când dai click pe tab-ul 'Examen'.
        Nu mai trebuie să apeși 'Refresh Liste'.
        """
        self.refresh_lists()
        super().showEvent(event)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # STACK 1: SETUP
        self.setup_page = QWidget()
        self.setup_ui_page(self.setup_page)
        
        # STACK 2: EXAMEN
        self.exam_page = QWidget()
        self.exam_ui_page(self.exam_page)
        
        # STACK 3: FINAL
        self.final_page = QWidget()
        self.final_ui_page(self.final_page)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.setup_page)
        self.stack.addWidget(self.exam_page)
        self.stack.addWidget(self.final_page)
        
        layout.addWidget(self.stack)

    # --- PAGINA 1: SETUP ---
    def setup_ui_page(self, page):
        """Metodă integrală pentru pagina de configurare (Start Nou vs Reluare)."""
        layout_principal = QVBoxLayout(page)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        
        # Titlu Centrat
        lbl_main_title = QLabel("🏁 GESTIONARE EXAMINARE HUNTER PROTOCOL")
        lbl_main_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold; margin-bottom: 20px;")
        lbl_main_title.setAlignment(Qt.AlignCenter)
        layout_principal.addWidget(lbl_main_title)
        
        # Splitter orizontal între Start Nou și Reluare
        self.splitter_setup = QSplitter(Qt.Horizontal)
        
        # --- PANEL STÂNGA: START NOU ---
        container_nou = QFrame()
        container_nou.setStyleSheet("background-color: #0f0f0f; border: 1px solid #333; border-radius: 10px;")
        layout_nou = QVBoxLayout(container_nou)
        layout_nou.setContentsMargins(25, 25, 25, 25)
        layout_nou.setSpacing(15)
        
        layout_nou.addWidget(QLabel("🚀 PORNEȘTE O SESIUNE NOUĂ"))
        
        self.cmb_patient = QComboBox()
        self.cmb_template = QComboBox()
        self.cmb_strategy = QComboBox()  # DROPDOWN STRATEGIE
        self.cmb_patient.currentIndexChanged.connect(self.update_info_label)
        self.cmb_patient.activated.connect(self._broadcast_patient_sync)  # SYNC doar la acțiune umană
        self.cmb_template.currentIndexChanged.connect(self.update_info_label)
        self.cmb_strategy.currentIndexChanged.connect(self.update_info_label)  # SIGNAL STRATEGIE
        
        layout_nou.addWidget(QLabel("SELECTEAZĂ PACIENT:"))
        layout_nou.addWidget(self.cmb_patient)
        layout_nou.addWidget(QLabel("SELECTEAZĂ PROTOCOL (TEST):"))
        layout_nou.addWidget(self.cmb_template)
        layout_nou.addWidget(QLabel("SELECTEAZĂ STRATEGIE:"))  # LABEL STRATEGIE
        layout_nou.addWidget(self.cmb_strategy)  # COMBO STRATEGIE
        
        # Etichetă info dinamică
        self.lbl_info = QLabel("Așteptare selecție...")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setMinimumHeight(80)
        self.lbl_info.setStyleSheet("color: #aaa; font-style: italic; background: #151515; padding: 10px; border-radius: 5px;")
        layout_nou.addWidget(self.lbl_info)
        
        # Layout cu 2 butoane: START și EXPORT
        buttons_layout = QHBoxLayout()
        
        btn_start = QPushButton("🚀 ÎNCEPE TESTAREA")
        btn_start.setStyleSheet("""
            QPushButton { 
                background-color: #004d40; color: #00ff69; 
                padding: 15px; font-weight: bold; font-size: 16px; 
                border: 1px solid #00ff69; border-radius: 5px;
            }
            QPushButton:hover { background-color: #00695c; color: white; }
        """)
        btn_start.clicked.connect(self.start_exam)
        buttons_layout.addWidget(btn_start)
        
        btn_export = QPushButton("📤 EXPORT PENTRU STANDALONE")
        btn_export.setStyleSheet("""
            QPushButton { 
                background-color: #1a237e; color: #82b1ff; 
                padding: 15px; font-weight: bold; font-size: 16px; 
                border: 1px solid #82b1ff; border-radius: 5px;
            }
            QPushButton:hover { background-color: #283593; color: white; }
        """)
        btn_export.clicked.connect(self.export_exam_package)
        buttons_layout.addWidget(btn_export)
        
        layout_nou.addLayout(buttons_layout)
        layout_nou.addStretch()

        # --- PANEL DREAPTĂ: RELUARE SESIUNE ---
        container_reluare = QFrame()
        container_reluare.setStyleSheet("background-color: #0a0a0a; border: 1px solid #4a148c; border-radius: 10px;")
        layout_reluare = QVBoxLayout(container_reluare)
        layout_reluare.setContentsMargins(25, 25, 25, 25)
        layout_reluare.setSpacing(15)
        
        layout_reluare.addWidget(QLabel("⏳ SESIUNI SUSPENDATE (PAUZĂ)"))
        
        self.list_pending_sessions = QListWidget()
        self.list_pending_sessions.setStyleSheet("background-color: #000; color: #e0e0e0; border: 1px solid #222; padding: 5px;")
        layout_reluare.addWidget(self.list_pending_sessions)
        
        btn_resume = QPushButton("RELUARE SESIUNE SELECTATĂ")
        btn_resume.setStyleSheet("""
            QPushButton { 
                background-color: #4a148c; color: white; 
                padding: 15px; font-weight: bold; font-size: 14px;
                border: 1px solid #e040fb; border-radius: 5px;
            }
            QPushButton:hover { background-color: #6a1b9a; }
        """)
        btn_resume.clicked.connect(self.resume_exam_handler)
        layout_reluare.addWidget(btn_resume)
        
        self.splitter_setup.addWidget(container_nou)
        self.splitter_setup.addWidget(container_reluare)
        self.splitter_setup.setSizes([500, 500])
        
        layout_principal.addWidget(self.splitter_setup)


    # --- PAGINA 2: GAMEPLAY ---
    def exam_ui_page(self, page):
        """Metodă integrală care construiește ecranul de testare propriu-zis."""
        layout_examen = QVBoxLayout(page)
        layout_examen.setContentsMargins(40, 40, 40, 40)
        layout_examen.setSpacing(20)
        
        # --- ZONA SUPERIOARĂ: INDICATORI PROGRES ---
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(10)
        
        # ETICHETA DETALIATĂ (cea care dădea eroarea AttributeError)
        self.lbl_progress_details = QLabel("Pregătire motor...")
        self.lbl_progress_details.setStyleSheet("""
            color: #00ff69; 
            font-weight: bold; 
            font-family: 'Consolas', monospace; 
            font-size: 16px;
        """)
        self.lbl_progress_details.setAlignment(Qt.AlignCenter)
        header_vbox.addWidget(self.lbl_progress_details)
        
        # Rând cu Bara de Progres și Butonul de Pauză
        row_progres = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        self.btn_pause = QPushButton("⏸ PAUZĂ ȘI SALVARE")
        self.btn_pause.setFixedWidth(180)
        self.btn_pause.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold; font-size: 12px;")
        self.btn_pause.clicked.connect(self.pause_and_save_exam)
        
        row_progres.addWidget(self.progress_bar, 1)
        row_progres.addWidget(self.btn_pause)
        header_vbox.addLayout(row_progres)
        
        layout_examen.addLayout(header_vbox)
        
        # --- ZONA CENTRALĂ: ÎNTREBARE ---
        self.lbl_question = QLabel("Încărcare întrebare...")
        self.lbl_question.setObjectName("QuestionText") # Folosește stilul de 26px definit în EXAM_STYLE
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setAlignment(Qt.AlignCenter)
        layout_examen.addWidget(self.lbl_question, 1)
        
        # --- ZONA INFERIOARĂ: BUTOANE RĂSPUNS ---
        self.btn_opts = []
        for i in range(4):
            btn = QPushButton(f"Varianta {i}")
            btn.setObjectName("OptionBtn") # Folosește stilul de 24px definit în EXAM_STYLE
            btn.setCursor(Qt.PointingHandCursor)
            # Conectăm butonul folosind o funcție anonimă pentru a transmite indexul
            btn.clicked.connect(lambda checked=False, idx=i: self.answer_clicked(idx))
            layout_examen.addWidget(btn)
            self.btn_opts.append(btn)
            
        layout_examen.addStretch()

    def pause_and_save_exam(self):
        """Metodă integrală care suspendă examenul curent."""
        confirmare = QMessageBox.question(self, "Pauză", "Dorești să salvezi progresul și să închizi testul acum?", QMessageBox.Yes | QMessageBox.No)
        if confirmare == QMessageBox.Yes:
            if self.engine.save_session_state():
                QMessageBox.information(self, "Succes", "Sesiunea a fost salvată. O poți relua oricând din panoul de start.")
                self.stack.setCurrentIndex(0) # Înapoi la setup
                self.refresh_lists() # Reîmprospătăm listele ca să apară sesiunea salvată

    def resume_exam_handler(self):
        """Metodă integrală care pornește reluarea unei sesiuni selectate."""
        item = self.list_pending_sessions.currentItem()
        if not item:
            QMessageBox.warning(self, "Atenție", "Selectează o sesiune din listă!")
            return
            
        session_id = item.data(Qt.UserRole)
        success, msg = self.engine.load_session_state(session_id)
        
        if success:
            self.stack.setCurrentIndex(1) # Trecem direct la pagina de întrebări
            self.load_next_question()
        else:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut relua sesiunea: {msg}")

    # --- PAGINA 3: FINAL ---
    def final_ui_page(self, page):
        l = QVBoxLayout(page)
        l.setAlignment(Qt.AlignCenter)
        
        container = QFrame()
        container.setStyleSheet("background-color: #0f0f0f; border: 2px solid #00ff69; border-radius: 20px; padding: 40px;")
        cl = QVBoxLayout(container)
        
        lbl = QLabel("✅ TEST FINALIZAT")
        lbl.setStyleSheet("font-size: 32px; color: #00ff69; font-weight: bold; qproperty-alignment: AlignCenter;")
        cl.addWidget(lbl)
        
        info = QLabel("\nDatele au fost salvate cu succes.\nPoți vedea interpretarea în Tab-ul 'Rezultate'.")
        info.setStyleSheet("color: white; font-size: 16px; qproperty-alignment: AlignCenter;")
        cl.addWidget(info)
        
        btn_home = QPushButton("🏠 Înapoi la Panou")
        btn_home.setStyleSheet("background-color: #333; color: white; padding: 10px; margin-top: 20px;")
        btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        cl.addWidget(btn_home)
        
        l.addWidget(container)

    # ==========================
    # LOGICA
    # ==========================
    def refresh_lists(self):
        """Metodă integrală care populează dropdown-urile și lista de sesiuni suspendate."""
        # SALVĂM selecțiile curente ÎNAINTE de refresh
        current_patient_id = self.cmb_patient.currentData()
        current_template_id = self.cmb_template.currentData()
        current_strategy_id = self.cmb_strategy.currentData()
        
        print(f"[TAB5 refresh_lists] Saving current selections: patient={current_patient_id}, template={current_template_id}, strategy={current_strategy_id}")
        
        self.cmb_patient.blockSignals(True)
        self.cmb_template.blockSignals(True)
        self.cmb_strategy.blockSignals(True)  # BLOCHEZ STRATEGIE
        
        self.cmb_patient.clear()
        self.cmb_template.clear()
        self.cmb_strategy.clear()  # CURAT STRATEGIE
        self.list_pending_sessions.clear()
        
        # 1. Populare Pacienți
        lista_pacienti = self.patient_mgr.get_all_patients()
        if not lista_pacienti:
            self.cmb_patient.addItem("⚠️ Niciun pacient în DB!", None)
        else:
            for pacient in lista_pacienti:
                # pacient = (id, nume, age, job, cnp_hash)
                self.cmb_patient.addItem(f"{pacient[1]} (ID: {pacient[4][:4]})", pacient[0])
            
        # 2. Populare Template-uri (Protocoale)
        lista_template = self.arch_mgr.get_all_templates()
        if not lista_template:
            self.cmb_template.addItem("⚠️ Niciun test creat!", None)
        else:
            for test in lista_template:
                # test = (id, nume, desc)
                self.cmb_template.addItem(f"{test[1]}", test[0])
        
        # 2.5. Populare Strategii (Hunter Protocol v3)
        import sqlite3
        from config import Config
        conn_strategies = sqlite3.connect(Config.DB_NAME)
        c_strat = conn_strategies.cursor()
        c_strat.execute("SELECT id, name FROM exam_strategies ORDER BY name")
        lista_strategii = c_strat.fetchall()
        conn_strategies.close()
        
        if not lista_strategii:
            self.cmb_strategy.addItem("⚠️ Nicio strategie în DB!", None)
        else:
            for strat in lista_strategii:
                # strat = (id, nume)
                self.cmb_strategy.addItem(f"{strat[1]}", strat[0])
        
        # 3. Populare Sesiuni Suspendate (PENTRU RELUARE)
        import sqlite3
        from config import Config
        conexiune = sqlite3.connect(Config.DB_NAME)
        cursor = conexiune.cursor()
        
        # Căutăm sesiunile cu status 'Paused'
        query_sesiuni = """
            SELECT s.id, p.full_name, t.name, s.date_taken 
            FROM sessions s
            JOIN patients p ON s.patient_id = p.id
            JOIN test_templates t ON s.template_id = t.id
            WHERE s.status = 'Paused'
            ORDER BY s.date_taken DESC
        """
        cursor.execute(query_sesiuni)
        sesiuni_pauza = cursor.fetchall()
        conexiune.close()
        
        if not sesiuni_pauza:
            item_gol = QListWidgetItem("Nicio sesiune suspendată.")
            item_gol.setFlags(Qt.NoItemFlags) # Nu poate fi selectat
            self.list_pending_sessions.addItem(item_gol)
        else:
            for sid, p_name, t_name, data_test in sesiuni_pauza:
                text_afisat = f"ID:{sid} | {p_name} | {t_name} ({data_test[:16]})"
                item_sesiune = QListWidgetItem(text_afisat)
                item_sesiune.setData(Qt.UserRole, sid) # Salvăm ID-ul sesiunii pentru reluare
                self.list_pending_sessions.addItem(item_sesiune)

        # RESTAURĂM selecțiile DUPĂ refresh
        if current_patient_id:
            index = self.cmb_patient.findData(current_patient_id)
            if index >= 0:
                self.cmb_patient.setCurrentIndex(index)
                print(f"[TAB5 refresh_lists] Restored patient selection to index {index}")
        
        if current_template_id:
            index = self.cmb_template.findData(current_template_id)
            if index >= 0:
                self.cmb_template.setCurrentIndex(index)
                print(f"[TAB5 refresh_lists] Restored template selection")
        
        if current_strategy_id:
            index = self.cmb_strategy.findData(current_strategy_id)
            if index >= 0:
                self.cmb_strategy.setCurrentIndex(index)
                print(f"[TAB5 refresh_lists] Restored strategy selection")

        self.cmb_patient.blockSignals(False)
        self.cmb_template.blockSignals(False)
        self.cmb_strategy.blockSignals(False)  # DEBLOCHEZ STRATEGIE
        self.update_info_label()

    def _broadcast_patient_sync(self, index=None):
        """Sincronizează pacientul către celelalte tab-uri — DOAR la o alegere făcută de utilizator.
        Folosește semnalul 'activated' (nu se declanșează la schimbări programatice), deci nu creează bucle."""
        if getattr(self, '_in_sync_update', False):
            return
        pacient_id = self.cmb_patient.currentData()
        if not pacient_id:
            return
        main_window = self.window()
        if hasattr(main_window, 'sync_patient_selection'):
            print(f"[TAB5] Triggering sync for patient {pacient_id}")
            main_window.sync_patient_selection(pacient_id, 'tab_exam')

    def update_info_label(self):
        """Metodă integrală care actualizează feedback-ul vizual pentru sesiunea nouă."""
        # Verificăm dacă widget-ul există (safety check)
        if not hasattr(self, 'lbl_info'):
            return

        pacient_id = self.cmb_patient.currentData()
        template_id = self.cmb_template.currentData()
        strategy_id = self.cmb_strategy.currentData()  # ID STRATEGIE
        
        if pacient_id and template_id and strategy_id:  # VERIFICĂM TOATE 3
            nume_pacient = self.cmb_patient.currentText()
            nume_test = self.cmb_template.currentText()
            nume_strategie = self.cmb_strategy.currentText()  # NUME STRATEGIE
            
            self.lbl_info.setText(f"✅ GATA DE START\n\n👤 Subiect: {nume_pacient}\n📝 Protocol: {nume_test}\n🎯 Strategie: {nume_strategie}")  # AFIȘEZ STRATEGIE
            self.lbl_info.setStyleSheet("""
                color: #00ff69; font-weight: bold; background: #051505; 
                padding: 10px; border: 1px solid #00ff69; border-radius: 5px;
            """)
        else:
            self.lbl_info.setText("⚠️ Vă rugăm să selectați un Pacient, un Protocol și o Strategie din listele de mai sus.")  # TEXT ACTUALIZAT
            self.lbl_info.setStyleSheet("""
                color: #ff5252; background: #150505; 
                padding: 10px; border: 1px solid #ff5252; border-radius: 5px;
            """)

    def start_exam(self):
        """
        Metodă integrală care inițializează o sesiune nouă de examinare,
        resetează indicatorii de progres și comută interfața la ecranul de întrebări.
        """
        # 1. Extragem ID-urile selectate de utilizator din meniurile derulante
        identificator_pacient = self.cmb_patient.currentData()
        identificator_template = self.cmb_template.currentData()
        identificator_strategie = self.cmb_strategy.currentData()  # ID STRATEGIE
        
        # 2. Validăm selecția pentru a ne asigura că avem date de start valide
        if identificator_pacient is None or identificator_template is None or identificator_strategie is None:  # VERIFICĂM SI STRATEGIA
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Eroare Configurare", 
                "Date invalide! Vă rugăm să selectați un Pacient, un Protocol (Template) și o Strategie de testare."  # TEXT ACTUALIZAT
            )
            return

        # 3. RESETAREA CONTOARELOR DE PROGRES (Esențial pentru indicatorul X/Y)
        # Resetăm numărătoarea întrebărilor pentru fiecare din cele 3 Valuri posibile
        self.contor_progres_valuri = {
            1: 0,  # Valul 1: Screening
            2: 0,  # Valul 2: Clarificare
            3: 0   # Valul 3: Monștri
        }
        
        # 4. Solicităm motorului de examen să creeze o sesiune nouă în baza de date
        # Această metodă va calcula și coada inițială de întrebări
        succes_pornire, mesaj_sistem = self.engine.start_new_session(identificator_pacient, identificator_template, identificator_strategie)  # TRIMIT STRATEGIA
        
        # 5. Verificăm dacă sesiunea a putut fi pornită cu succes
        if succes_pornire:
            from logger import log
            # Logăm evenimentul în consolă pentru monitorizare
            log("ui", f"Sesiunea de examen a început cu succes pentru subiectul {identificator_pacient}.")
            
            # 6. Schimbăm pagina vizibilă la ecranul de Examen (indexul 1 în QStackedWidget)
            self.stack.setCurrentIndex(1)
            
            # 7. Încărcăm prima întrebare din coadă pentru a începe testarea propriu-zisă
            self.load_next_question()
        else:
            # În caz de eșec (ex: template gol, erori DB), afișăm eroarea primită de la motor
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Eroare Start Examen", 
                f"Nu s-a putut începe sesiunea de testare.\nMotiv: {mesaj_sistem}"
            )

    def load_next_question(self):
        """
        Metodă integrală care încarcă următoarea întrebare din coada motorului de examen
        și actualizează indicatorii de progres (text și bară) în funcție de Valul curent.
        """
        # 1. Solicităm următoarea întrebare de la motorul de examen
        date_intrebare = self.engine.get_next_question()
        
        # 2. Dacă nu mai există întrebări în coadă, finalizăm sesiunea
        if date_intrebare is None:
            # Calculăm rezultatele finale și actualizăm bazinul holistic
            self.engine.finish_session()
            # Mutăm interfața la pagina de final (Stack index 2)
            self.stack.setCurrentIndex(2)
            # Resetăm tracker-ul de progres pentru o eventuală sesiune viitoare
            if hasattr(self, 'contor_progres_valuri'):
                self.contor_progres_valuri = {1: 0, 2: 0, 3: 0}
            return

        # 3. Identificăm numărul Valului (Wave) și numele acestuia pentru interfață
        numar_val_curent = date_intrebare.get('wave', 1)
        
        harta_nume_valuri = {
            1: "Screening (Evaluare Standard)",
            2: "Clarificare (Investigație Rigoare)",
            3: "Deep Dive (Analiză Monștri și Riscuri)"
        }
        nume_val_afisat = harta_nume_valuri.get(numar_val_curent, "Analiză")

        # 4. Gestionăm contorul de progres intern pentru Valul curent
        # Verificăm dacă tracker-ul există, dacă nu, îl inițializăm
        if not hasattr(self, 'contor_progres_valuri'):
            self.contor_progres_valuri = {1: 0, 2: 0, 3: 0}
            
        # Incrementăm numărul întrebării în cadrul acestui val specific
        self.contor_progres_valuri[numar_val_curent] += 1
        
        # PROGRES DIN ENGINE (pentru pauză/reluare corectă)
        # Folosim valorile salvate în engine pentru a păstra progresul la reluare
        pozitie_actuala_in_val = self.engine.questions_answered + 1  # +1 pentru întrebarea curentă afișată
        total_intrebari_val_curent = self.engine.total_questions_planned
        
        # 6. Actualizăm eticheta textuală de progres (ex: Val 1 din 3 | Întrebarea 5/9)
        text_detaliat_progres = (
            f"VAL {numar_val_curent} din 3 ({nume_val_afisat}) | "
            f"Întrebarea {pozitie_actuala_in_val} din {total_intrebari_val_curent}"
        )
        self.lbl_progress_details.setText(text_detaliat_progres)

        # 7. Actualizăm vizual bara de progres (procentaj raportat la valul curent)
        procentaj_bara = int((pozitie_actuala_in_val / total_intrebari_val_curent) * 100) if total_intrebari_val_curent > 0 else 0
        self.progress_bar.setValue(procentaj_bara)

        # 8. Afișăm textul întrebării pe ecran
        self.lbl_question.setText(date_intrebare['text'])
        
        # 9. Configurăm butoanele de răspuns
        harta_litere_optiuni = {0: "A", 1: "B", 2: "C", 3: "D"}
        
        # Resetăm toate butoanele (le ascundem inițial)
        for buton_optiune in self.btn_opts:
            buton_optiune.setVisible(False)

        # Populăm butoanele cu variantele de răspuns din baza de date
        lista_optiuni_db = date_intrebare.get('options', [])
        for index_optiune, date_varianta in enumerate(lista_optiuni_db):
            # Verificăm să nu depășim numărul de butoane fizice de pe ecran (4)
            if index_optiune < len(self.btn_opts):
                buton_tinta = self.btn_opts[index_optiune]
                
                # date_varianta este un tuplu de forma (index, text, scor_impact)
                litera_afisata = harta_litere_optiuni.get(index_optiune, "?")
                text_raspuns = date_varianta[1]
                valoare_scor = date_varianta[2]
                
                # Setăm proprietățile vizuale și tehnice ale butonului
                buton_tinta.setText(f"{litera_afisata})  {text_raspuns}")
                buton_tinta.setProperty("score", valoare_scor)
                buton_tinta.setProperty("text", text_raspuns)
                buton_tinta.setVisible(True)

    def answer_clicked(self, btn_index):
        btn = self.btn_opts[btn_index]
        score = btn.property("score")
        text = btn.property("text")
        
        self.engine.submit_answer(btn_index, score, text)
        self.load_next_question()



    def _analyze_axis_consistency_recursive(self, cursor, axis_id):
        """Metodă integrală: Generează un Audit Tehnic de Înaltă Densitate pentru fiecare decizie."""
        scores = self.answers_log.get(axis_id, [])
        if len(scores) < 2: return
        
        avg = statistics.mean(scores)
        val_min = min(scores)
        val_max = max(scores)
        diff = val_max - val_min
        
        # --- 1. EVALUARE FILTRU INTEGRITATE (Contradicție/Salt) ---
        prio_contra = 0
        if diff >= 100: 
            prio_contra = self.strat_red_qty
            txt_contra = f"CONTRADICȚIE MAJORĂ (Salt critic {diff} pcte, prag 100)"
        elif diff >= 66: 
            prio_contra = self.strat_yellow_qty
            txt_contra = f"CONTRADICȚIE MINORĂ (Salt {diff} pcte, prag 66)"
        else: 
            prio_contra = 0
            txt_contra = f"CONSISTENT (Salt {diff} pcte)"

        # --- 2. EVALUARE FILTRU PROFILARE (Abatere de la Normă) ---
        n_mean, n_sd = self._get_axis_norms_from_db(axis_id)
        dist = abs(avg - n_mean)
        prio_dev = 0
        if dist >= self.strat_dev_major_threshold:
            prio_dev = self.strat_red_qty
            txt_dev = f"ABATERE EXTREMĂ (Dist {dist:.1f} >= prag {self.strat_dev_major_threshold})"
        elif dist >= self.strat_dev_minor_threshold:
            prio_dev = self.strat_yellow_qty
            txt_dev = f"ABATERE ATIPICĂ (Dist {dist:.1f} >= prag {self.strat_dev_minor_threshold})"
        else:
            prio_dev = 0
            txt_dev = f"ÎN NORMĂ (Dist {dist:.1f})"

        # --- 3. DECIZIA FINALĂ (SENTINȚA MAXIMĂ) ---
        final_qty = max(prio_contra, prio_dev)
        if final_qty == 0:
            print(f"\033[96m[CALC] Axa {axis_id}: {txt_contra} + {txt_dev}. Rezultat: VERDE.\033[0m")
            return

        # Construim AVALANȘA de date pentru explicație
        if prio_contra >= prio_dev:
            decision_type = "INTEGRITATE (Sinceritate)"
        else:
            decision_type = "PROFILARE (Atipic)"

        # String-ul de audit care va ajunge în Tabul 6
        audit_dossier = (
            f"🔍 ANALIZĂ DUALĂ FINALIZATĂ | "
            f"FILTRU 1 [INTEGRITATE]: {txt_contra}, Secvență: {scores} | "
            f"FILTRU 2 [PROFILARE]: {txt_dev}, Medie: {avg:.1f} vs Normă: {n_mean} | "
            f"SENTINȚĂ: {decision_type} a dictat injectarea a +{final_qty} itemi."
        )

        print(f"\033[92m[DECISION] {audit_dossier}\033[0m")
        
        # Salvăm în DB cu eticheta corectă
        self._log_audit_decision(axis_id, 2, decision_type, audit_dossier, "Analiza de Rigoare")
        
        # Injectăm întrebările extra (recursiv)
        self._fetch_and_process_logic(cursor, axis_id, wave_target=2, limit=final_qty)

    def export_exam_package(self):
        """Exportă protocolul și strategia într-un DB standalone."""
        from PySide6.QtWidgets import QMessageBox, QFileDialog
        
        template_id = self.cmb_template.currentData()
        strategy_id = self.cmb_strategy.currentData()
        
        if not template_id or not strategy_id:
            QMessageBox.warning(self, "Eroare", "Selectați Protocol ȘI Strategie.")
            return
        
        patient_id = self.cmb_patient.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Eroare", "Selectați un pacient înainte de export.")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Salvează Pachet Testare", 
            "exam_package.db", 
            "Database (*.db)"
        )
        
        if not save_path:
            return
        
        try:
            import sqlite3, shutil, json, os
            from config import Config
            
            # Dacă există un pachet vechi la aceeași cale, îl ștergem ca să exportăm proaspăt
            if os.path.exists(save_path):
                os.remove(save_path)
            
            # Creăm DB-ul gol
            conn_export = sqlite3.connect(save_path)
            c = conn_export.cursor()
            
            # Creăm structura minimă
            c.execute("""CREATE TABLE meta (
                protocol_name TEXT, strategy_name TEXT, 
                template_id INTEGER, strategy_id INTEGER,
                patient_id INTEGER, patient_name TEXT
            )""")
            
            c.execute("""CREATE TABLE axes (
                id INTEGER PRIMARY KEY, name TEXT, left_pole TEXT, 
                right_pole TEXT, category TEXT, norm_mean REAL, norm_std_dev REAL
            )""")
            
            c.execute("""CREATE TABLE questions_bank (
                id INTEGER PRIMARY KEY, axis_id INTEGER, 
                text_content TEXT, version_hash TEXT, wave_target INTEGER
            )""")
            
            c.execute("""CREATE TABLE question_options (
                question_hash TEXT, option_index INTEGER, 
                text_content TEXT, score_value INTEGER
            )""")
            
            c.execute("""CREATE TABLE exam_strategies (
                id INTEGER PRIMARY KEY, name TEXT, 
                w1_base_qty INTEGER, yellow_extra_qty INTEGER, 
                red_extra_qty INTEGER, dev_threshold_minor REAL, 
                dev_threshold_major REAL
            )""")
            
            c.execute("""CREATE TABLE sessions (
                id INTEGER PRIMARY KEY, candidate_name TEXT, 
                template_id INTEGER, strategy_id INTEGER, 
                date_taken TEXT, status TEXT
            )""")
            
            c.execute("""CREATE TABLE session_responses (
                id INTEGER PRIMARY KEY, session_id INTEGER, 
                question_hash TEXT, axis_id INTEGER, 
                answer_chosen INTEGER, score_snapshot INTEGER
            )""")
            
            c.execute("""CREATE TABLE session_audit (
                id INTEGER PRIMARY KEY, session_id INTEGER,
                axis_id INTEGER, wave_target INTEGER,
                decision_type TEXT, explanation TEXT
            )""")
            
            c.execute("""CREATE TABLE synergy_rules (
                monster_axis_id INTEGER, trigger_axis_id INTEGER,
                operator TEXT, threshold REAL
            )""")
            
            # Copiem datele
            conn_main = sqlite3.connect(Config.DB_NAME)
            c_main = conn_main.cursor()
            
            # Protocol și strategie
            c_main.execute("SELECT name FROM test_templates WHERE id=?", (template_id,))
            proto_name = c_main.fetchone()[0]
            c_main.execute("SELECT name FROM exam_strategies WHERE id=?", (strategy_id,))
            strat_name = c_main.fetchone()[0]
            
            # Pacientul selectat (turnat în pachet pentru import)
            c_main.execute("SELECT full_name FROM patients WHERE id=?", (patient_id,))
            row_pat = c_main.fetchone()
            patient_name = row_pat[0] if row_pat else "Necunoscut"
            
            c.execute("INSERT INTO meta VALUES (?,?,?,?,?,?)", 
                     (proto_name, strat_name, template_id, strategy_id, patient_id, patient_name))
            
            # Axele din protocol
            c_main.execute("SELECT config_json FROM test_templates WHERE id=?", (template_id,))
            config = json.loads(c_main.fetchone()[0])
            axis_ids = config.get("axes", [])
            
            for aid in axis_ids:
                c_main.execute("SELECT id, name, left_pole, right_pole, category, norm_mean, norm_std_dev FROM axes WHERE id=?", (aid,))
                c.execute("INSERT INTO axes VALUES (?,?,?,?,?,?,?)", c_main.fetchone())
            
            # Întrebările - TOATE valurile
            for aid in axis_ids:
                c_main.execute("SELECT id, axis_id, text_content, version_hash, wave_target FROM questions_bank WHERE axis_id=? AND is_active=1", (aid,))
                for q in c_main.fetchall():
                    c.execute("INSERT INTO questions_bank VALUES (?,?,?,?,?)", q)
                    
                    # Opțiunile
                    c_main.execute("SELECT question_hash, option_index, text_content, score_value FROM question_options WHERE question_hash=?", (q[3],))
                    for opt in c_main.fetchall():
                        c.execute("INSERT INTO question_options VALUES (?,?,?,?)", opt)
            
            # Strategia
            c_main.execute("SELECT id, name, w1_base_qty, yellow_extra_qty, red_extra_qty, dev_threshold_minor, dev_threshold_major FROM exam_strategies WHERE id=?", (strategy_id,))
            c.execute("INSERT INTO exam_strategies VALUES (?,?,?,?,?,?,?)", c_main.fetchone())
            
            # Regulile de sinergie pentru monștri
            c_main.execute("""SELECT sr.monster_axis_id, sr.trigger_axis_id, sr.operator, sr.threshold
                             FROM synergy_rules sr
                             JOIN axes a ON sr.monster_axis_id = a.id
                             WHERE a.category IN ('Monster', 'Clinic', 'Control')""")
            for rule in c_main.fetchall():
                c.execute("INSERT INTO synergy_rules VALUES (?,?,?,?)", rule)
            
            conn_main.close()
            conn_export.commit()
            conn_export.close()
            
            QMessageBox.information(self, "✅ Export Complet", 
                f"Pachet salvat: {save_path}\n\nPoate fi folosit cu standalone_exam.py")
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare Export", str(e))

    def set_selected_patient(self, patient_id, from_sync=False):
        """
        Setează pacientul selectat (folosit pentru sincronizare între tab-uri)
        @param patient_id: ID-ul pacientului
        @param from_sync: True dacă apelat din sincronizare (evită loop infinit)
        """
        print(f"[TAB5] set_selected_patient({patient_id}, from_sync={from_sync})")
        
        # Verificăm dacă dropdown-ul există
        if not hasattr(self, 'cmb_patient'):
            print(f"[TAB5] WARNING: cmb_patient not initialized yet")
            return
        
        # Blocăm semnalele pentru a evita loop infinit
        self.cmb_patient.blockSignals(True)
        
        # Găsim indexul pacientului în dropdown
        found = False
        for i in range(self.cmb_patient.count()):
            if self.cmb_patient.itemData(i) == patient_id:
                self.cmb_patient.setCurrentIndex(i)
                found = True
                print(f"[TAB5] Found patient at index {i}, set dropdown to '{self.cmb_patient.currentText()}'")
                break
        
        if not found:
            print(f"[TAB5] WARNING: Patient {patient_id} not found in dropdown!")
        
        # Reactivăm semnalele
        self.cmb_patient.blockSignals(False)
        
        # Actualizăm info label (marcăm că suntem în sync)
        self._in_sync_update = True
        self.update_info_label()
        self._in_sync_update = False
        
        print(f"[TAB5] Sync complete!")
