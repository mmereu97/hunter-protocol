import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QLineEdit, QPushButton, QSplitter, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QMessageBox, QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt
# ACEASTA ESTE LINIA CORECTATĂ:
from PySide6.QtGui import QColor, QFont
from logic.architect_manager import ArchitectManager
from logic.knowledge_manager import KnowledgeManager
from logic.strategy_manager import StrategyManager
from ai_agents.architect_agent import ArchitectAgent
from logger import log

class ArchitectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = ArchitectManager()
        self.knowledge = KnowledgeManager()
        self.strategy_mgr = StrategyManager()
        self.ai_agent = ArchitectAgent()
        
        self.all_axes_cache = [] 
        self.current_template_id = None
        
        # Stil Cyberpunk adaptat
        self.setStyleSheet("background-color: #0b0b0b; color: #e0e0e0; font-family: 'Segoe UI';")
        
        self.setup_ui()
        self.load_available_axes()
        self.load_strategies_into_combo()
        self.refresh_templates_list()

    def setup_ui(self):
        from logic.settings_manager import SettingsManager
        setari = SettingsManager.load_settings()

        # Layout principal orizontal
        self.layout_principal_tab = QHBoxLayout(self)
        self.layout_principal_tab.setContentsMargins(10, 10, 10, 10)
        self.layout_principal_tab.setSpacing(15)
        
        self.splitter_principal = QSplitter(Qt.Horizontal)

        # STILIZARE CYBERPUNK (Consistență cu restul aplicației)
        self.setStyleSheet("""
            QWidget { background-color: #0b0b0b; color: #e0e0e0; font-family: 'Segoe UI'; font-size: 13px; }
            QFrame { border: none; }
            QListWidget { background-color: #0d0d0d; border: 1px solid #333; border-radius: 4px; outline: none; }
            QListWidget::item { padding: 3px; border-bottom: 1px solid #1a1a1a; }
            QListWidget::item:selected { background-color: #1a1a1a; border-left: 3px solid #00e5ff; color: #00ff69; }
            QTableWidget { background-color: #0d0d0d; gridline-color: #222; border: 1px solid #333; }
            QHeaderView::section { background-color: #1a1a1a; color: #00e5ff; font-weight: bold; border: 1px solid #222; padding: 6px; }
            QLineEdit, QComboBox { background-color: #050505; border: 1px solid #444; color: #00ff69; padding: 8px; border-radius: 3px; }
            QPushButton { background-color: #161616; border: 1px solid #333; border-bottom: 2px solid #333; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton#SaveBtn { color: #00ff69; border-bottom: 2px solid #00ff69; }
            QPushButton#DeleteBtn { color: #ff5252; border-bottom: 2px solid #ff5252; }
            QPushButton#ManualBtn { color: #00e5ff; border-bottom: 2px solid #00e5ff; }
            QPushButton#GenerateBtn { background-color: #4a148c; color: #e040fb; border: 1px solid #e040fb; }
            QSplitter::handle { background-color: #222; }
        """)

        # =====================================================================
        # PANOU STÂNGA: RESURSE (IDENTIC CU VAULT)
        # =====================================================================
        self.panou_stanga_resurse = QFrame()
        self.layout_stanga_resurse = QVBoxLayout(self.panou_stanga_resurse)
        self.layout_stanga_resurse.setContentsMargins(0, 0, 0, 0)
        
        self.left_vertical_splitter = QSplitter(Qt.Vertical)
        
        # --- 1. CONTAINER AXE (Zonă superioară) ---
        self.container_axe = QWidget()
        self.layout_axe_intern = QVBoxLayout(self.container_axe)
        self.layout_axe_intern.setContentsMargins(0, 0, 0, 5)
        
        self.label_axe_disp = QLabel("⚡ AXE DISPONIBILE:")
        self.label_axe_disp.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 14px;")
        self.layout_axe_intern.addWidget(self.label_axe_disp)

        # RÂND FILTRE (CATEGORIE + SORTARE) - Identic cu Vault
        self.layout_filtre_orizontal = QHBoxLayout()
        self.layout_filtre_orizontal.setSpacing(10)

        # Filtru Categorie
        self.layout_v_cat = QVBoxLayout()
        self.layout_v_cat.setSpacing(2)
        self.layout_v_cat.addWidget(QLabel("📂 CATEGORIE:"))
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("Toate", "ALL")
        self.cmb_category.currentIndexChanged.connect(self.filter_axes_list)
        self.layout_v_cat.addWidget(self.cmb_category)

        # Filtru Sortare
        self.layout_v_sort = QVBoxLayout()
        self.layout_v_sort.setSpacing(2)
        self.layout_v_sort.addWidget(QLabel("⚖️ SORTARE:"))
        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["Nume (A-Z)", "ID (Crescator)"])
        
        # RESTAURARE STARE: Restaurăm sortarea favorită
        from logic.settings_manager import SettingsManager
        settings = SettingsManager.load_settings()
        last_sort_index = settings.get("tab4_sort_index", 0)  # Default: Nume (A-Z)
        self.cmb_sort.setCurrentIndex(last_sort_index)
        print(f"[TAB4] Restored sort index: {last_sort_index}")
        
        # Conectăm schimbarea + salvarea
        self.cmb_sort.currentIndexChanged.connect(self.on_sort_changed)
        self.layout_v_sort.addWidget(self.cmb_sort)

        self.layout_filtre_orizontal.addLayout(self.layout_v_cat, 1)
        self.layout_filtre_orizontal.addLayout(self.layout_v_sort, 1)
        self.layout_axe_intern.addLayout(self.layout_filtre_orizontal)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Caută axă după nume sau ID...")
        self.search_bar.textChanged.connect(self.filter_axes_list)
        self.layout_axe_intern.addWidget(self.search_bar)
        
        self.list_axes = QListWidget()
        self.list_axes.itemDoubleClicked.connect(self.add_axis_to_table_event)
        self.layout_axe_intern.addWidget(self.list_axes)
        
        # --- 2. CONTAINER PROTOCOALE SALVATE (Zonă inferioară) ---
        self.container_protocoale = QWidget()
        self.layout_protocoale_intern = QVBoxLayout(self.container_protocoale)
        self.label_prot_salvate = QLabel("📂 PROTOCOALE SALVATE:")
        self.label_prot_salvate.setStyleSheet("color: #00e5ff; font-weight: bold;")
        self.layout_protocoale_intern.addWidget(self.label_prot_salvate)
        self.list_templates = QListWidget()
        self.list_templates.itemClicked.connect(self.on_template_selected)
        self.layout_protocoale_intern.addWidget(self.list_templates)
        
        self.layout_rand_admin_stanga = QHBoxLayout()
        self.btn_manual_plan = QPushButton("🛠️ MANUAL")
        self.btn_manual_plan.setObjectName("ManualBtn")
        self.btn_manual_plan.clicked.connect(self.reset_form)
        self.btn_delete_protocol = QPushButton("🗑️ ȘTERGE")
        self.btn_delete_protocol.setObjectName("DeleteBtn")
        self.btn_delete_protocol.clicked.connect(self.delete_protocol_handler)
        self.btn_reset_formular = QPushButton("📄 RESET")
        self.btn_reset_formular.clicked.connect(self.reset_form)
        self.layout_rand_admin_stanga.addWidget(self.btn_manual_plan)
        self.layout_rand_admin_stanga.addWidget(self.btn_reset_formular)
        self.layout_rand_admin_stanga.addWidget(self.btn_delete_protocol)
        self.layout_protocoale_intern.addLayout(self.layout_rand_admin_stanga)

        self.left_vertical_splitter.addWidget(self.container_axe)
        self.left_vertical_splitter.addWidget(self.container_protocoale)
        
        dimensiuni_salvate = setari.get("architect_left_splitter_sizes")
        if dimensiuni_salvate:
            self.left_vertical_splitter.setSizes(dimensiuni_salvate)
        else:
            self.left_vertical_splitter.setSizes([500, 300])

        self.left_vertical_splitter.splitterMoved.connect(self.save_left_splitter_state)
        self.layout_stanga_resurse.addWidget(self.left_vertical_splitter)

        # =====================================================================
        # PANOU DREAPTA: CONSTRUCȚIE (Tabel)
        # =====================================================================
        self.panou_dreapta_constructie = QFrame()
        self.layout_dreapta_constructie = QVBoxLayout(self.panou_dreapta_constructie)
        
        # AI Wizard
        self.layout_rand_ai_wizard = QHBoxLayout()
        self.inp_ai_prompt = QLineEdit(); self.inp_ai_prompt.setPlaceholderText("🔮 AI WIZARD...")
        self.inp_ai_prompt.setStyleSheet("background-color: #1a0526; color: #e040fb; border: 1px solid #4a148c;")
        self.btn_ai = QPushButton("✨ GENEREAZĂ"); self.btn_ai.setObjectName("GenerateBtn")
        self.btn_ai.clicked.connect(self.run_ai_wizard)
        self.layout_rand_ai_wizard.addWidget(self.inp_ai_prompt, 1); self.layout_rand_ai_wizard.addWidget(self.btn_ai)
        self.layout_dreapta_constructie.addLayout(self.layout_rand_ai_wizard)

        # Metadate
        self.panou_metadate = QFrame(); self.panou_metadate.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")
        self.layout_metadate_v = QVBoxLayout(self.panou_metadate)
        row1 = QHBoxLayout()
        self.inp_name = QLineEdit(); self.inp_name.setPlaceholderText("Nume Protocol")
        self.cmb_strategy = QComboBox()
        row1.addWidget(QLabel("NUME:")); row1.addWidget(self.inp_name, 2); row1.addWidget(QLabel("🧩 STRATEGIE:")); row1.addWidget(self.cmb_strategy, 1)
        self.layout_metadate_v.addLayout(row1)
        row2 = QHBoxLayout()
        self.inp_desc = QLineEdit(); self.inp_desc.setPlaceholderText("Descriere tactică...")
        row2.addWidget(QLabel("DESC:")); row2.addWidget(self.inp_desc, 1)
        self.layout_metadate_v.addLayout(row2)
        self.layout_dreapta_constructie.addWidget(self.panou_metadate)

        # Tabel
        self.table_config = QTableWidget(0, 4)
        self.table_config.setHorizontalHeaderLabels(["Nume Axă", "Categorie", "Sursă", "ID"])
        self.table_config.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_config.setColumnHidden(3, True)
        self.table_config.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layout_dreapta_constructie.addWidget(self.table_config)
        
        # Butoane Salvare
        self.layout_rand_actiuni_finale = QHBoxLayout()
        self.btn_save_protocol = QPushButton("💾 SALVEAZĂ PROTOCOLUL"); self.btn_save_protocol.setObjectName("SaveBtn")
        self.btn_save_protocol.clicked.connect(self.save_configuration)
        self.btn_elimina_rand = QPushButton("❌ Elimină Rând"); self.btn_elimina_rand.clicked.connect(self.remove_selected_row)
        self.layout_rand_actiuni_finale.addWidget(self.btn_save_protocol, 2); self.layout_rand_actiuni_finale.addWidget(self.btn_elimina_rand, 1)
        self.layout_dreapta_constructie.addLayout(self.layout_rand_actiuni_finale)

        self.splitter_principal.addWidget(self.panou_stanga_resurse)
        self.splitter_principal.addWidget(self.panou_dreapta_constructie)
        self.splitter_principal.setSizes([350, 850])
        self.layout_principal_tab.addWidget(self.splitter_principal)

    def load_strategies_into_combo(self):
        """Metodă integrală care populează meniul de strategii și păstrează selecția curentă."""
        # 1. Reținem ce era selectat înainte de curățare (ca să nu pierdem munca)
        id_selectat_anterior = self.cmb_strategy.currentData()
        
        # Blocăm semnalele pentru a nu declanșa evenimente de "schimbare" inutile în timpul curățării
        self.cmb_strategy.blockSignals(True)
        self.cmb_strategy.clear()
        
        # 2. Citim strategiile proaspete din baza de date
        toate_strategiile = self.strategy_mgr.get_all_strategies()
        
        if not toate_strategiile:
            self.cmb_strategy.addItem("- Nicio Strategie Definită (Mergi la 4.2) -", None)
        else:
            for strat in toate_strategiile:
                # strat: (id, name, desc, ...)
                self.cmb_strategy.addItem(strat[1], strat[0])
        
        # 3. Restaurăm selecția dacă este posibil
        if id_selectat_anterior is not None:
            index_de_restaurat = self.cmb_strategy.findData(id_selectat_anterior)
            if index_de_restaurat >= 0:
                self.cmb_strategy.setCurrentIndex(index_de_restaurat)
        
        self.cmb_strategy.blockSignals(False)
        log("ui", f"Meniul de strategii a fost actualizat ({len(toate_strategiile)} profile găsite).")


    def add_axis_to_table_event(self, item):
        """Metodă integrală declanșată la dublu-click pe o axă din lista de resurse."""
        if not item:
            return
            
        # Extragem dicționarul de date atașat item-ului din listă
        axa_data = item.data(Qt.UserRole)
        
        if axa_data:
            # Delegăm construcția rândului către metoda universală
            self.insert_axis_row(axa_data)

    def save_configuration(self):
        name = self.inp_name.text().strip()
        strategy_id = self.cmb_strategy.currentData()
        
        if not name or not strategy_id:
            QMessageBox.warning(self, "Eroare", "Numele și Strategia sunt obligatorii!")
            return
        
        axis_ids = []
        for r in range(self.table_config.rowCount()):
            axis_ids.append(int(self.table_config.item(r, 3).text()))

        if not axis_ids:
            QMessageBox.warning(self, "Eroare", "Adăugați cel puțin o axă!")
            return

        if self.manager.save_template(name, self.inp_desc.text(), axis_ids, strategy_id, self.current_template_id):
            QMessageBox.information(self, "Succes", "Protocol salvat!")
            self.refresh_templates_list()
        else:
            QMessageBox.critical(self, "Eroare", "Eșec la salvare.")

    def on_template_selected(self, item):
        """Metodă integrală care încarcă un protocol salvat și îi restaurează starea completă."""
        id_protocol = item.data(Qt.UserRole)
        self.current_template_id = id_protocol
        
        # Luăm datele brute din baza de date prin manager
        date_brute_test = self.manager.load_template_data(id_protocol)
        
        if date_brute_test:
            # Structura returnată: (nume, descriere, config_json, strategy_id)
            nume_test, descriere_test, config_json_axe, id_strategie = date_brute_test
            
            self.inp_name.setText(nume_test)
            self.inp_desc.setText(descriere_test)
            self.table_config.setRowCount(0) # Curățăm tabelul înainte de populare
            
            # Sincronizăm meniul de strategii
            self.load_strategies_into_combo()
            index_strat = self.cmb_strategy.findData(id_strategie)
            if index_strat >= 0:
                self.cmb_strategy.setCurrentIndex(index_strat)
            
            # Decodăm lista de axe și le căutăm în cache-ul de 107 axe pentru a lua și culorile
            config_obiect = json.loads(config_json_axe)
            lista_id_axe = config_obiect.get("axes", [])
            
            for aid in lista_id_axe:
                date_axa_completa = next((axa for axa in self.all_axes_cache if axa["id"] == aid), None)
                if date_axa_completa:
                    # Apelăm metoda universală de inserare definită la punctul 1
                    self.insert_axis_row(date_axa_completa)

    def load_available_axes(self):
        """Metodă integrală care încarcă axele și populează dropdown-ul de categorii."""
        date_brute_db = self.knowledge.get_all_axes() 
        
        self.all_axes_cache = []
        categori_unice = set()
        
        for rand in date_brute_db:
            # rand: id, name, cat, left, right, source, desc, hex
            self.all_axes_cache.append({
                "id": rand[0],
                "name": rand[1],
                "cat": rand[2],
                "source": rand[5],
                "description": rand[6],
                "hex_color": rand[7] if len(rand) > 7 else "#ffffff"
            })
            categori_unice.add(rand[2])
            
        # Populăm dropdown-ul de categorii
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("Toate", "ALL")
        for cat_name in sorted(list(categori_unice)):
            self.cmb_category.addItem(cat_name, cat_name)
        self.cmb_category.blockSignals(False)
            
        self.filter_axes_list()

    def on_sort_changed(self, index):
        """Salvează tipul de sortare selectat și refiltrează lista"""
        from logic.settings_manager import SettingsManager
        SettingsManager.update_key("tab4_sort_index", index)
        print(f"[TAB4] Saved sort preference: index={index}")
        self.filter_axes_list()

    def filter_axes_list(self):
        """Metodă integrală care filtrează, sortează și colorează lista conform selecției."""
        self.list_axes.clear()
        text_cautat = self.search_bar.text().lower()
        categorie_filtru = self.cmb_category.currentData()
        sort_mode = self.cmb_sort.currentText()
        
        # 1. Filtrare
        axe_filtrate = []
        for ax in self.all_axes_cache:
            nume_axa = ax['name'].lower()
            id_axa = str(ax['id'])
            
            # Căutare după nume sau ID
            if text_cautat and (text_cautat not in nume_axa and text_cautat not in id_axa):
                continue
            
            # Filtrare după categorie
            if categorie_filtru != "ALL" and ax['cat'] != categorie_filtru:
                continue
                
            axe_filtrate.append(ax)
            
        # 2. Sortare
        if "ID" in sort_mode:
            axe_filtrate.sort(key=lambda x: x["id"])
        else:
            axe_filtrate.sort(key=lambda x: x["name"].lower())
            
        # 3. Afișare
        for ax in axe_filtrate:
            item = QListWidgetItem(f"{ax['name']} [{ax['id']}]")
            
            # Aplicăm culoarea HEX salvată
            culoare_hex = ax.get("hex_color", "#ffffff")
            try:
                item.setForeground(QColor(culoare_hex))
            except:
                item.setForeground(QColor("#ffffff"))
            
            item.setToolTip(f"Sursă: {ax['source']}\nCategorie: {ax['cat']}")
            item.setData(Qt.UserRole, ax)
            self.list_axes.addItem(item)

    def run_ai_wizard(self):
        """Metodă integrală care permite AI-ului să configureze testul pe ecran, folosind inserarea universală."""
        intentie_utilizator = self.inp_ai_prompt.text().strip()
        if not intentie_utilizator: 
            return

        # 1. Feedback vizual
        self.inp_name.setText("⌛ AI-ul analizează sistemele (OCEAN, HEXACO, 16PF)...")
        QApplication.processEvents() 

        # 2. Apelăm Agentul pentru a obține JSON-ul cu ID-uri
        rezultat_ai = self.ai_agent.generate_template_structure(intentie_utilizator)
        
        if rezultat_ai and "selected_axis_ids" in rezultat_ai:
            # 3. Curățăm masa de lucru curentă
            self.table_config.setRowCount(0)
            self.current_template_id = None
            
            # 4. Completăm Metadatele (Nume și Descriere)
            self.inp_name.setText(rezultat_ai.get("test_name", "Protocol Nou"))
            self.inp_desc.setText(rezultat_ai.get("description", ""))
            
            # 5. "Alegem" axele pe ecran folosind metoda universală insert_axis_row
            ids_selectate = rezultat_ai["selected_axis_ids"]
            
            for aid in ids_selectate:
                # Căutăm axa în cache-ul local de 107 axe pentru a prelua și culorile HEX
                axa_data = next((x for x in self.all_axes_cache if x["id"] == aid), None)
                
                if axa_data:
                    # REPARARE: Folosim metoda universală pentru a păstra culorile Cyberpunk și a evita duplicatele
                    self.insert_axis_row(axa_data)
            
            log("ui", f"AI Wizard a populat testul '{rezultat_ai['test_name']}' cu {len(ids_selectate)} axe.")
            QMessageBox.information(self, "AI Wizard", f"Am selectat automat cele mai relevante {len(ids_selectate)} axe pentru: {intentie_utilizator}.")
        else:
            self.inp_name.setText("")
            QMessageBox.critical(self, "Eroare AI", "AI-ul nu a putut genera o selecție validă. Verificați cheia API.")

    def refresh_templates_list(self):
        self.list_templates.clear()
        for t in self.manager.get_all_templates():
            item = QListWidgetItem(t[1]); item.setData(Qt.UserRole, t[0])
            self.list_templates.addItem(item)

    def reset_form(self):
        """Metodă integrală care golește complet spațiul de lucru pentru un test nou."""
        # 1. Resetăm ID-ul curent pentru a nu suprascrie accidental un test vechi
        self.current_template_id = None
        
        # 2. Curățăm câmpurile de text (Metadate)
        self.inp_name.clear()
        self.inp_desc.clear()
        self.inp_ai_prompt.clear()
        
        # 3. Resetăm selectorul de strategie pe prima poziție
        if self.cmb_strategy.count() > 0:
            self.cmb_strategy.setCurrentIndex(0)
            
        # 4. Goliți complet tabelul de construcție a axelor
        self.table_config.setRowCount(0)
        
        # 5. Deselectăm orice element din listele din stânga
        self.list_axes.clearSelection()
        self.list_templates.clearSelection()
        
        # 6. Mutăm focusul pe câmpul de nume pentru a începe scrierea
        self.inp_name.setFocus()
        
        log("ui", "Spațiul de lucru din Arhitect a fost resetat pentru o planificare nouă.")

    def remove_selected_row(self):
        if self.table_config.currentRow() >= 0: self.table_config.removeRow(self.table_config.currentRow())

    def delete_protocol_handler(self):
        """Metodă integrală care șterge protocolul selectat cu confirmare prealabilă."""
        element_selectat = self.list_templates.currentItem()
        
        if not element_selectat:
            QMessageBox.warning(self, "Atenție", "Vă rugăm să selectați un protocol din lista 'PROTOCOALE SALVATE' pentru a-l șterge.")
            return
            
        id_protocol = element_selectat.data(Qt.UserRole)
        nume_protocol = element_selectat.text()
        
        confirmare = QMessageBox.question(
            self, 
            "Confirmare Ștergere", 
            f"Sunteți sigur că doriți să ștergeți definitiv protocolul: '{nume_protocol}'?\n\n"
            "Această acțiune nu poate fi anulată.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmare == QMessageBox.Yes:
            # Apelăm managerul pentru ștergerea din baza de date
            self.manager.delete_template(id_protocol)
            
            # Notificăm utilizatorul și curățăm interfața
            log("ui", f"Protocolul '{nume_protocol}' a fost șters.")
            self.refresh_templates_list()
            
            # Dacă protocolul șters era cel încărcat în formular, resetăm formularul
            if self.current_template_id == id_protocol:
                self.reset_form()
            
            QMessageBox.information(self, "Succes", f"Protocolul '{nume_protocol}' a fost eliminat cu succes.")


    def save_left_splitter_state(self):
        """Metodă integrală care salvează poziția splitter-ului vertical din stânga în JSON."""
        from logic.settings_manager import SettingsManager
        dimensiuni_actuale = self.left_vertical_splitter.sizes()
        SettingsManager.update_key("architect_left_splitter_sizes", dimensiuni_actuale)


    def showEvent(self, event):
        """Metodă integrală care forțează reîncărcarea strategiilor când intri în tab."""
        self.load_strategies_into_combo()
        # Apelăm și refresh-ul listei de axe pentru a fi siguri că suntem la zi
        self.load_available_axes()
        super().showEvent(event)


    def insert_axis_row(self, axa_data):
        """Metodă integrală care inserează un rând în tabel folosind un dicționar de date."""
        # 1. Evităm duplicatele în tabel
        for rand_existent in range(self.table_config.rowCount()):
            id_celula = self.table_config.item(rand_existent, 3)
            if id_celula and int(id_celula.text()) == axa_data['id']:
                return

        # 2. Creăm rândul nou
        numar_rand = self.table_config.rowCount()
        self.table_config.insertRow(numar_rand)
        
        # 3. Pregătim celulele
        item_nume = QTableWidgetItem(str(axa_data['name']))
        item_cat = QTableWidgetItem(str(axa_data['cat']))
        item_sursa = QTableWidgetItem(str(axa_data['source']))
        item_id = QTableWidgetItem(str(axa_data['id']))
        
        # 4. Aplicăm stilul Cyberpunk bazat pe culoarea din DB
        cod_hex_culoare = axa_data.get("hex_color", "#ffffff")
        culoare_axa = QColor(cod_hex_culoare)
        
        item_nume.setForeground(culoare_axa)
        item_nume.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        # Categoria și sursa le lăsăm cu un gri discret pentru contrast
        culoare_text_secundar = QColor("#888888")
        item_cat.setForeground(culoare_text_secundar)
        item_sursa.setForeground(culoare_text_secundar)
        
        # 5. Fixăm celulele în tabel
        self.table_config.setItem(numar_rand, 0, item_nume)
        self.table_config.setItem(numar_rand, 1, item_cat)
        self.table_config.setItem(numar_rand, 2, item_sursa)
        self.table_config.setItem(numar_rand, 3, item_id)