import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QLineEdit, QPushButton, QSplitter, QFrame, QTextEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QAbstractItemView, QGridLayout, QFileDialog,
    QApplication  # <--- ACESTA ESTE IMPORTUL CARE LIPSEA
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from logic.knowledge_manager import KnowledgeManager
from logic.settings_manager import SettingsManager
from logger import log, log_error
from ai_agents.architect_agent import ArchitectAgent 

# ==========================================
# 🎨 CYBERPUNK STYLESHEET
# ==========================================
CYBER_STYLE = """
    /* BAZA */
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    QFrame { border: none; }
    QSplitter::handle { background-color: #333; width: 2px; }

    /* INPUTS */
    QLineEdit, QTextEdit, QComboBox {
        background-color: #050505; 
        color: #00e5ff;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 5px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #00e5ff; }
    
    QComboBox::drop-down { border: 0px; }
    QComboBox QAbstractItemView {
        background-color: #111;
        color: #00e5ff;
        selection-background-color: #00e5ff;
        selection-color: black;
    }

    /* LISTE */
    QListWidget, QTableWidget {
        background-color: #121212;
        color: #ffffff;
        border: 1px solid #444;
    }
    QListWidget::item:selected, QTableWidget::item:selected {
        background-color: #00e5ff;
        color: #000000;
        font-weight: bold;
    }
    QHeaderView::section { background-color: #222; color: #aaa; border: 1px solid #333; }

    /* LABELS */
    QLabel { color: #aaaaaa; font-weight: bold; }
    QLabel#IDLabel { color: #555; font-family: 'Consolas'; font-size: 11px; }

    /* BUTTONS */
    QPushButton {
        background-color: #1a1a1a;
        color: #ccc;
        border: 1px solid #444;
        padding: 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #252526; border: 1px solid #666; color: white; }
"""

CAT_OPTIONS = [
    ("Core", "Personalitate (Core)"),
    ("Monster", "Monștri & Riscuri"),
    ("Bio", "Biologie & Lifestyle"),
    ("EQ", "Inteligență Emoțională"),
    ("Style", "Stil & Valori"),
    ("Career", "Carieră"),
    ("Clinic", "Patologie"),
    ("Dating", "Dating & Relații"),
    ("Values", "Valori & Credințe"),
    ("Control", "Control & Validitate")
]

class KnowledgeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = KnowledgeManager()
        
        # --- ACEASTA ESTE LINIA CARE LIPSEA ---
        self.ai_agent = ArchitectAgent() 
        
        self.current_axis_id = None
        self.current_question_id = None
        
        self.all_axes_cache = []
        from logic.settings_manager import SettingsManager
        self.settings = SettingsManager.load_settings()
        
        # Aplicăm stilul Cyberpunk local
        # (Asigură-te că CYBER_STYLE este definit în fișier)
        if 'CYBER_STYLE' in globals():
            self.setStyleSheet(CYBER_STYLE)
            
        self.setup_ui()
        self.load_axes_from_db()
        
        # Restaurăm filtrul de categorie salvat
        saved_filter_index = self.settings.get("knowledge_filter_index", 0)
        if saved_filter_index < self.cmb_category.count():
            self.cmb_category.setCurrentIndex(saved_filter_index)
        else:
            self.apply_filters()

    def setup_ui(self):
        # Layout principal orizontal al întregului tab
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(5, 5, 5, 5)
        self.layout_principal.setSpacing(10)
        
        self.splitter_principal = QSplitter(Qt.Horizontal)

        # =====================================================================
        # PANOU STÂNGA: LISTA AXE ȘI FILTRE (COMPACTAT)
        # =====================================================================
        self.panou_stanga = QFrame()
        self.layout_stanga = QVBoxLayout(self.panou_stanga)
        self.layout_stanga.setContentsMargins(5, 5, 5, 5)
        
        self.layout_filtre_orizontal = QHBoxLayout()
        self.layout_filtre_orizontal.setSpacing(10)

        self.layout_coloana_categorie = QVBoxLayout()
        self.layout_coloana_categorie.setSpacing(2)
        self.layout_coloana_categorie.addWidget(QLabel("📂 CATEGORIE:"))
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("Toate Axele", "ALL")
        self.cmb_category.currentIndexChanged.connect(self.apply_filters)
        self.layout_coloana_categorie.addWidget(self.cmb_category)
        
        self.layout_coloana_sortare = QVBoxLayout()
        self.layout_coloana_sortare.setSpacing(2)
        self.layout_coloana_sortare.addWidget(QLabel("⚖️ SORTARE:"))
        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["Nume (A-Z)", "ID (Crescator)"])
        
        index_sort_salvat = self.settings.get("knowledge_sort_index", 0)
        self.cmb_sort.setCurrentIndex(index_sort_salvat)
        self.cmb_sort.currentIndexChanged.connect(self.on_sort_changed)
        self.layout_coloana_sortare.addWidget(self.cmb_sort)

        self.layout_filtre_orizontal.addLayout(self.layout_coloana_categorie, 1)
        self.layout_filtre_orizontal.addLayout(self.layout_coloana_sortare, 1)
        self.layout_stanga.addLayout(self.layout_filtre_orizontal)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Caută axă după nume sau ID...")
        self.search_bar.textChanged.connect(self.apply_filters)
        self.layout_stanga.addWidget(self.search_bar)

        self.axes_list = QListWidget()
        
        # SCHIMBARE CRITICĂ: Înlocuim itemClicked cu currentItemChanged
        # Acest semnal reacționează la orice schimbare de selecție (Click, Săgeți Sus/Jos, Tab)
        self.axes_list.currentItemChanged.connect(self.on_axis_selection_changed)
        
        self.layout_stanga.addWidget(self.axes_list)

        self.layout_portabilitate_unite = QHBoxLayout()
        self.btn_export_knowledge = QPushButton("📤 EXPORT JSON")
        self.btn_export_knowledge.clicked.connect(self.export_axes_to_text)
        self.btn_import_knowledge = QPushButton("📥 IMPORT JSON")
        self.btn_import_knowledge.clicked.connect(self.import_axes_handler)
        self.layout_portabilitate_unite.addWidget(self.btn_export_knowledge)
        self.layout_portabilitate_unite.addWidget(self.btn_import_knowledge)
        self.layout_stanga.addLayout(self.layout_portabilitate_unite)

        # =====================================================================
        # PANOU DREAPTA: EDITOR DEFINIȚIE ȘI ÎNTREBĂRI
        # =====================================================================
        self.panou_dreapta = QFrame()
        self.layout_dreapta = QVBoxLayout(self.panou_dreapta)
        self.layout_dreapta.setContentsMargins(5, 5, 5, 5)

        # --- 1. SKIN EDITOR (GRILĂ 2/3 vs 1/3) ---
        self.skin_group = QFrame()
        self.skin_group.setStyleSheet("background-color: #161616; border: 1px solid #333; border-radius: 5px;")
        self.layout_grid_skin = QGridLayout(self.skin_group)
        
        self.inp_axis_name = QLineEdit()
        self.inp_axis_name.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.inp_axis_category_manual = QLineEdit()
        self.inp_axis_color_hex = QLineEdit()
        self.inp_axis_color_hex.setFixedWidth(80)
        self.inp_source_system = QLineEdit()

        self.layout_rand_poli = QHBoxLayout()
        self.inp_left_pole = QLineEdit(); self.inp_right_pole = QLineEdit()
        self.layout_rand_poli.addWidget(QLabel("0:")); self.layout_rand_poli.addWidget(self.inp_left_pole)
        self.layout_rand_poli.addWidget(QLabel("100:")); self.layout_rand_poli.addWidget(self.inp_right_pole)

        self.layout_grid_skin.addWidget(QLabel("TITLU AXĂ:"), 0, 0)
        self.layout_grid_skin.addWidget(self.inp_axis_name, 1, 0)
        
        self.layout_meta_axa = QHBoxLayout()
        self.layout_meta_axa.addWidget(QLabel("CAT:")); self.layout_meta_axa.addWidget(self.inp_axis_category_manual, 1)
        self.layout_meta_axa.addWidget(QLabel("COL:")); self.layout_meta_axa.addWidget(self.inp_axis_color_hex)
        self.layout_grid_skin.addLayout(self.layout_meta_axa, 2, 0)
        
        self.layout_grid_skin.addWidget(QLabel("SURSA SISTEM:"), 3, 0)
        self.layout_grid_skin.addWidget(self.inp_source_system, 4, 0)
        self.layout_grid_skin.addLayout(self.layout_rand_poli, 5, 0)

        self.layout_v_descriere = QVBoxLayout()
        self.layout_v_descriere.addWidget(QLabel("📖 DEFINIȚIE ȘI NOTE TEHNICE:"))
        self.txt_axis_description = QTextEdit()
        self.layout_v_descriere.addWidget(self.txt_axis_description)
        self.layout_grid_skin.addLayout(self.layout_v_descriere, 0, 1, 6, 1)

        self.btn_save_skin = QPushButton("💾 ACTUALIZEAZĂ DEFINIȚIA AXEI")
        self.btn_save_skin.setStyleSheet("background-color: #004d40; color: #00ff69; font-weight: bold; padding: 8px;")
        self.btn_save_skin.clicked.connect(self.save_axis_skin)
        self.layout_grid_skin.addWidget(self.btn_save_skin, 6, 0, 1, 2)

        self.layout_dreapta.addWidget(self.skin_group)

        # --- 2. LISTA ÎNTREBĂRI (CU REORDONARE) ---
        self.lbl_questions_count = QLabel("ÎNTREBĂRI ÎN ORDINEA PRIORITĂȚII DE EXTRAGERE:")
        self.layout_dreapta.addWidget(self.lbl_questions_count)
        
        self.layout_zona_lista_reordonare = QHBoxLayout()
        
        self.questions_list = QListWidget()
        self.questions_list.itemClicked.connect(self.on_question_selected)
        # Permitem textului să ocupe tot spațiul fără scroll orizontal dacă se poate
        self.questions_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.questions_list.setWordWrap(True) 
        self.layout_zona_lista_reordonare.addWidget(self.questions_list, 1)
        
        # Butoane Reordonare (Sus / Jos)
        self.layout_butoane_prioritate = QVBoxLayout()
        self.btn_move_q_up = QPushButton("▲"); self.btn_move_q_up.setFixedWidth(40)
        self.btn_move_q_up.setToolTip("Mută întrebarea mai sus (Prioritate mai mare)")
        self.btn_move_q_up.clicked.connect(self.move_question_up)
        
        self.btn_move_q_down = QPushButton("▼"); self.btn_move_q_down.setFixedWidth(40)
        self.btn_move_q_down.setToolTip("Mută întrebarea mai jos (Prioritate mai mică)")
        self.btn_move_q_down.clicked.connect(self.move_question_down)
        
        self.layout_butoane_prioritate.addStretch()
        self.layout_butoane_prioritate.addWidget(self.btn_move_q_up)
        self.layout_butoane_prioritate.addWidget(self.btn_move_q_down)
        self.layout_butoane_prioritate.addStretch()
        
        self.layout_zona_lista_reordonare.addLayout(self.layout_butoane_prioritate)
        self.layout_dreapta.addLayout(self.layout_zona_lista_reordonare)
        
        self.btn_new_q = QPushButton("✨ ADAUGĂ ÎNTREBARE NOUĂ")
        self.btn_new_q.clicked.connect(self.prepare_new_question)
        self.layout_dreapta.addWidget(self.btn_new_q)

        # --- 3. EDITOR ÎNTREBARE ---
        self.editor_form = QFrame()
        self.editor_form.setStyleSheet("background-color: #111; border-top: 2px solid #ff9800;")
        self.editor_form.setVisible(False)
        self.layout_formular = QVBoxLayout(self.editor_form)
        
        self.inp_q_text = QTextEdit()
        self.inp_q_text.setPlaceholderText("Scrie textul întrebării aici...")
        self.inp_q_text.setFixedHeight(60)
        self.layout_formular.addWidget(self.inp_q_text)
        
        self.layout_meta_intrebare = QHBoxLayout()
        self.inp_tags = QLineEdit(); self.inp_tags.setPlaceholderText("Tag-uri...")
        self.cmb_wave_hidden = QComboBox() # Îl păstrăm ascuns pentru compatibilitate cu baza de date
        self.layout_meta_intrebare.addWidget(QLabel("TAG-URI:")); self.layout_meta_intrebare.addWidget(self.inp_tags)
        self.layout_formular.addLayout(self.layout_meta_intrebare)
        
        self.tbl_options = QTableWidget(4, 2)
        self.tbl_options.setHorizontalHeaderLabels(["VARIANTA RĂSPUNS", "SCOR"])
        self.tbl_options.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_options.setColumnWidth(1, 60)
        self.setup_options_table()
        self.layout_formular.addWidget(self.tbl_options)
        
        self.layout_actiuni_q = QHBoxLayout()
        self.btn_ai_suggest_q = QPushButton("🤖 SUGESTIE AI"); self.btn_ai_suggest_q.setStyleSheet("background-color: #4a148c; color: white;")
        self.btn_ai_suggest_q.clicked.connect(self.suggest_question_with_ai)
        self.btn_save_q = QPushButton("💾 SALVEAZĂ"); self.btn_save_q.setStyleSheet("background-color: #e65100; color: white;")
        self.btn_save_q.clicked.connect(self.save_question)
        self.btn_delete_q = QPushButton("🗑️ ȘTERGE"); self.btn_delete_q.clicked.connect(self.delete_question)
        self.layout_actiuni_q.addWidget(self.btn_ai_suggest_q); self.layout_actiuni_q.addWidget(self.btn_save_q); self.layout_actiuni_q.addWidget(self.btn_delete_q)
        self.layout_formular.addLayout(self.layout_actiuni_q)
        
        self.layout_dreapta.addWidget(self.editor_form)

        # Finalizare Splitter
        self.splitter_principal.addWidget(self.panou_stanga)
        self.splitter_principal.addWidget(self.panou_dreapta)
        self.splitter_principal.setSizes([350, 850])
        self.layout_principal.addWidget(self.splitter_principal)


    # ==========================
    # LOGICA AXE
    # ==========================
    def load_axes_from_db(self):
        """Metodă integrală care încarcă axele și păstrează filtrul selectat anterior."""
        # --- PASUL 1: REȚINEM CE AVEM SELECTAT ACUM ---
        categorie_activa_anterior = self.cmb_category.currentData()
        text_cautat_anterior = self.search_bar.text()
        
        # --- PASUL 2: ÎNCĂRCĂM DATELE DIN DB ---
        raw_data = self.manager.get_all_axes() 
        self.all_axes_cache = []
        
        for r in raw_data:
            # Structura r: id, name, category, left, right, source, description, hex_color
            self.all_axes_cache.append({
                "id": r[0],
                "name": r[1],
                "cat": r[2],
                "left": r[3],
                "right": r[4],
                "source": r[5],
                "description": r[6] if len(r) > 6 else "",
                "hex_color": r[7] if len(r) > 7 else "#ffffff"
            })
            
        # --- PASUL 3: RECONSTRUIM DROPDOWN-UL DE CATEGORII ---
        categorii_gasite = sorted(list(set([ax["cat"] for ax in self.all_axes_cache])))
        
        self.cmb_category.blockSignals(True) # Blocăm semnalele ca să nu ruleze apply_filters de 10 ori
        self.cmb_category.clear()
        self.cmb_category.addItem("Toate Axele", "ALL")
        for c in categorii_gasite:
            self.cmb_category.addItem(c, c)
            
        # --- PASUL 4: RESTAURĂM FILTRUL ---
        index_de_restaurat = self.cmb_category.findData(categorie_activa_anterior)
        if index_de_restaurat >= 0:
            self.cmb_category.setCurrentIndex(index_de_restaurat)
        else:
            self.cmb_category.setCurrentIndex(0) # Fallback la "Toate"
            
        self.cmb_category.blockSignals(False)
        
        # Restaurăm și textul din search bar (fără să declanșăm evenimente inutile)
        self.search_bar.blockSignals(True)
        self.search_bar.setText(text_cautat_anterior)
        self.search_bar.blockSignals(False)
        
        # Aplicăm filtrele finale pentru a vedea lista corectă
        self.apply_filters()

    def on_filter_changed(self, index):
        SettingsManager.update_key("knowledge_filter_index", index)
        self.apply_filters()

    def apply_filters(self):
        """Metodă integrală care filtrează, sortează și colorează lista de axe folosind codurile HEX din DB."""
        # Curățăm lista vizuală înainte de repopulare
        self.axes_list.clear()
        
        text_cautat = self.search_bar.text().lower()
        cod_categorie_filtru = self.cmb_category.currentData()
        mod_sortare = self.cmb_sort.currentText()
        
        # 1. Aplicăm Filtrarea
        axe_filtrate = []
        for date_axa in self.all_axes_cache:
            nume_axa = str(date_axa["name"]).lower()
            categorie_axa = str(date_axa["cat"])
            
            # Filtru text (Căutare)
            if text_cautat and (text_cautat not in nume_axa):
                continue
            
            # Filtru Categorie
            if cod_categorie_filtru != "ALL" and categorie_axa != cod_categorie_filtru:
                continue
                
            axe_filtrate.append(date_axa)
            
        # 2. Aplicăm Sortarea conform preferinței salvate
        if "ID" in mod_sortare:
            axe_filtrate.sort(key=lambda x: x["id"])
        else:
            axe_filtrate.sort(key=lambda x: x["name"].lower())
            
        # 3. Construim elementele listei și aplicăm culorile
        for axa in axe_filtrate:
            text_afisat = f"{axa['name']} [{axa['id']}]"
            item_lista = QListWidgetItem(text_afisat)
            
            # Preluăm culoarea HEX salvată (sau alb dacă lipsește)
            cod_hex = axa.get("hex_color", "#ffffff")
            
            # Validăm codul HEX înainte de aplicare pentru a evita crash-ul
            if cod_hex and len(cod_hex) >= 4 and cod_hex.startswith("#"):
                item_lista.setForeground(QColor(cod_hex))
            else:
                item_lista.setForeground(QColor("#ffffff"))
            
            # Adăugăm Tooltip-ul informativ (Sursă + început de descriere)
            info_tooltip = f"SISTEM: {axa['source']}"
            if axa.get("description"):
                # Punem doar primele 150 de caractere în tooltip
                desc_curat = axa["description"][:150].replace("\n", " ")
                info_tooltip += f"\n\nDEFINIȚIE: {desc_curat}..."
            
            item_lista.setToolTip(info_tooltip)
            
            # Atașăm obiectul cu datele complete la item-ul vizual
            item_lista.setData(Qt.UserRole, axa)
            self.axes_list.addItem(item_lista)


    def on_sort_changed(self, index):
        """Metodă integrală care salvează preferința de sortare și reîmprospătează lista."""
        self.settings["knowledge_sort_index"] = index
        SettingsManager.save_settings(self.settings)
        self.apply_filters()

    def on_axis_selected(self, item):
        """Metodă integrală care populează datele axei și resetează vizual editorul de întrebări."""
        # 1. Extragem datele complete ale axei salvate în obiectul item
        axa = item.data(Qt.UserRole)
        if not axa:
            return
            
        # 2. Fixăm ID-ul axei curente
        self.current_axis_id = axa["id"]
        self.current_question_id = None

        # 3. Populăm câmpurile de text din zona "Editare Definiție Axă"
        self.inp_axis_name.setText(str(axa["name"]))
        self.inp_axis_category_manual.setText(str(axa["cat"]))
        self.inp_axis_color_hex.setText(str(axa.get("hex_color", "#ffffff")))
        self.inp_source_system.setText(str(axa["source"]))
        self.inp_left_pole.setText(str(axa["left"]))
        self.inp_right_pole.setText(str(axa["right"]))
        self.txt_axis_description.setPlainText(str(axa.get("description", "")))

        # 4. Închidem și curățăm editorul de întrebări (subtilitatea de curățenie)
        self.editor_form.setVisible(False)
        self.inp_q_text.clear()
        self.inp_tags.clear()
        self.setup_options_table()

        # 5. Încărcăm lista de întrebări pentru noua axă
        self.refresh_questions_list()

    def save_axis_skin(self):
        """Metodă integrală care salvează definiția și menține contextul vizual (filtru și selecție)."""
        if not self.current_axis_id: 
            return
        
        # Salvăm ID-ul curent pentru a-l reselecta la final
        id_axa_editata = self.current_axis_id
        
        # Colectăm datele din interfață
        nume = self.inp_axis_name.text()
        cat = self.inp_axis_category_manual.text()
        stanga = self.inp_left_pole.text()
        dreapta = self.inp_right_pole.text()
        sursa = self.inp_source_system.text()
        descriere = self.txt_axis_description.toPlainText()
        culoare = self.inp_axis_color_hex.text()
        
        # Trimitem datele către manager pentru UPDATE
        success = self.manager.update_axis_skin(
            self.current_axis_id, nume, cat, stanga, dreapta, sursa, descriere, culoare
        )
        
        if success:
            # Reîncărcăm datele (load_axes_from_db va păstra filtrele de categorie/căutare)
            self.load_axes_from_db()
            
            # --- SUBTILITATE EXTRA: RESELECTĂM AXA ÎN LISTĂ ---
            for i in range(self.axes_list.count()):
                item = self.axes_list.item(i)
                date_axa = item.data(Qt.UserRole)
                if date_axa["id"] == id_axa_editata:
                    self.axes_list.setCurrentItem(item)
                    # Facem scroll automat la ea dacă e nevoie
                    self.axes_list.scrollToItem(item)
                    break

            QMessageBox.information(self, "Succes", f"Axa '{nume}' a fost actualizată fără a reseta filtrele.")
        else:
            QMessageBox.critical(self, "Eroare", "Nu s-a putut salva definiția în baza de date.")

    def export_axes_to_text(self):
            """Metodă integrală care exportă axele în format JSON (pentru AI și pentru Import ulterior)."""
            cale_fisier, _ = QFileDialog.getSaveFileName(
                self, "Exportă Baza de Axe", "", "JSON Files (*.json);;Toate fișierele (*.*)"
            )
            if not cale_fisier:
                return

            # Colectăm datele brute din cache-ul nostru local (care e deja sincronizat cu DB)
            # Structura: id, name, cat, left, right, source, description, hex_color
            date_pentru_export = []
            for axa in self.all_axes_cache:
                date_pentru_export.append({
                    "nume": axa["name"],
                    "categorie": axa["cat"],
                    "pol_stanga": axa["left"],
                    "pol_dreapta": axa["right"],
                    "sursa_sistem": axa["source"],
                    "descriere": axa["description"],
                    "culoare_hex": axa["hex_color"]
                })

            try:
                with open(cale_fisier, "w", encoding="utf-8") as f:
                    json.dump(date_pentru_export, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "Succes", f"Au fost exportate {len(date_pentru_export)} axe în format JSON.")
                self.txt_ai_chat_log.append(f"<p style='color: #00ff69;'><i>[SYSTEM]: Export finalizat în {cale_fisier}</i></p>")
            except Exception as e:
                QMessageBox.critical(self, "Eroare", f"Nu s-a putut scrie fișierul: {str(e)}")

    def import_axes_handler(self):
        """Metodă integrală care importă axe dintr-un fișier JSON și le sincronizează cu baza de date."""
        cale_fisier, _ = QFileDialog.getOpenFileName(
            self, "Selectează fișierul de Import (JSON)", "", "JSON Files (*.json);;Toate fișierele (*.*)"
        )
        if not cale_fisier:
            return

        try:
            with open(cale_fisier, "r", encoding="utf-8") as f:
                date_importate = json.load(f)

            if not isinstance(date_importate, list):
                raise ValueError("Formatul fișierului nu este o listă validă de axe.")

            confirmare = QMessageBox.question(
                self, "Confirmare Import",
                f"Fișierul conține {len(date_importate)} axe.\n\n"
                "Sunteți sigur că doriți să le importați?\n"
                "Axele cu nume identice vor fi ACTUALIZATE.",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirmare != QMessageBox.Yes:
                return

            # Dezactivăm semnalele pentru a nu bloca UI-ul la fiecare rând
            self.axes_list.blockSignals(True)
            
            import_count = 0
            update_count = 0

            # Luăm o listă cu numele axelor existente pentru a decide INSERT sau UPDATE
            conexiune = self.manager.get_connection()
            cursor = conexiune.cursor()
            
            for item in date_importate:
                # Extragem datele folosind cheile definite la Export
                nume = item.get("nume")
                cat = item.get("categorie", "General")
                stanga = item.get("pol_stanga", "Pol 0")
                dreapta = item.get("pol_dreapta", "Pol 100")
                sursa = item.get("sursa_sistem", "Imported")
                desc = item.get("descriere", "")
                culoare = item.get("culoare_hex", "#ffffff")

                if not nume: continue

                # Verificăm dacă axa există deja după nume
                cursor.execute("SELECT id FROM axes WHERE name = ?", (nume,))
                rand_existent = cursor.fetchone()

                if rand_existent:
                    # UPDATE
                    id_existent = rand_existent[0]
                    self.manager.update_axis_skin(id_existent, nume, cat, stanga, dreapta, sursa, desc, culoare)
                    update_count += 1
                else:
                    # INSERT (Trebuie să scriem un mic insert în manager sau aici direct)
                    cursor.execute("""
                        INSERT INTO axes (name, category, left_pole, right_pole, source_system, description, hex_color)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (nume, cat, stanga, dreapta, sursa, desc, culoare))
                    import_count += 1
            
            conexiune.commit()
            conexiune.close()

            # Reîncărcăm totul în UI
            self.axes_list.blockSignals(False)
            self.load_axes_from_db()

            mesaj_final = f"Import finalizat!\n- Axe noi create: {import_count}\n- Axe existente actualizate: {update_count}"
            QMessageBox.information(self, "Succes Import", mesaj_final)
            
            if hasattr(self, 'txt_ai_chat_log'):
                self.txt_ai_chat_log.append(f"<p style='color: #00ff69;'><i>[SYSTEM]: {mesaj_final}</i></p>")

        except Exception as e:
            QMessageBox.critical(self, "Eroare la Import", f"A apărut o problemă: {str(e)}")

    def refresh_questions_list(self):
        """Metodă integrală care încarcă întrebările și le numerotează conform priorității din DB."""
        if not self.current_axis_id:
            return

        # Blocăm semnalele pentru a evita activarea 'on_question_selected' în timpul curățării
        self.questions_list.blockSignals(True)
        self.questions_list.clear()
        
        # Luăm întrebările de la manager (care sunt deja ORDER BY wave_target ASC)
        intrebari = self.manager.get_questions_for_axis(self.current_axis_id)
        
        # Actualizăm label-ul de numărare
        self.lbl_questions_count.setText(f"ORDINEA DE EXTRAGERE ({len(intrebari)} întrebări în bancă):")
        
        for index, q in enumerate(intrebari, 1):
            # Afișăm numărul de ordine urmat de text
            text_afisat = f"#{index}. {q['text']}"
            item = QListWidgetItem(text_afisat)
            
            # Primele 3 întrebări sunt considerate baza (Screening)
            if index <= 3:
                item.setForeground(QColor("#00ff69")) # Verde Neon
            else:
                item.setForeground(QColor("#888888")) # Gri discret pentru restul
            
            # Stocăm datele pentru utilizare ulterioară
            item.setData(Qt.UserRole, q)
            self.questions_list.addItem(item)
            
        self.questions_list.blockSignals(False)


    def on_question_selected(self, item):
        """Metodă integrală care încarcă datele întrebării selectate în editor."""
        q_data = item.data(Qt.UserRole)
        self.current_question_id = q_data['id']
        
        # Facem editorul vizibil
        self.editor_form.setVisible(True)
        
        # Populăm textul și tag-urile
        self.inp_q_text.setText(q_data['text'])
        self.inp_tags.setText(q_data['tags'])
        
        # Eliminăm referința la cmb_wave (care cauza eroarea) 
        # deoarece prioritatea este gestionată acum de butoanele SUS/JOS
        
        # Populăm opțiunile de răspuns
        self.tbl_options.setRowCount(0)
        self.tbl_options.setRowCount(4)
        for i, opt in enumerate(q_data['options']):
            if i < 4:
                self.tbl_options.setItem(i, 0, QTableWidgetItem(opt[1]))
                self.tbl_options.setItem(i, 1, QTableWidgetItem(str(opt[2])))


    def prepare_new_question(self):
        if not self.current_axis_id:
            QMessageBox.warning(self, "Atenție", "Selectează o axă!")
            return
        self.current_question_id = None
        self.editor_form.setVisible(True)
        self.inp_q_text.clear()
        self.inp_tags.clear()
        self.cmb_wave.setCurrentIndex(0)
        self.setup_options_table()
        self.inp_q_text.setFocus()

    def setup_options_table(self):
        self.tbl_options.clearContents()
        defaults = [("Da / Categoric", 100), ("Mai degrabă Da", 66), ("Mai degrabă Nu", 33), ("Nu / Deloc", 0)]
        for i, (txt, score) in enumerate(defaults):
            self.tbl_options.setItem(i, 0, QTableWidgetItem(txt))
            self.tbl_options.setItem(i, 1, QTableWidgetItem(str(score)))

    def save_question(self):
        """Metodă integrală care salvează întrebarea păstrând prioritatea ei actuală."""
        if not self.current_axis_id: return
        
        text = self.inp_q_text.toPlainText().strip()
        tags = self.inp_tags.text().strip()
        if not text: return

        # Colectăm opțiunile din tabel
        options = []
        labels = ['A', 'B', 'C', 'D']
        for i in range(4):
            t = self.tbl_options.item(i, 0).text() if self.tbl_options.item(i, 0) else ""
            try: s = int(self.tbl_options.item(i, 1).text())
            except: s = 0
            options.append((labels[i], t, s))

        # Dacă e o întrebare nouă, o punem la finalul listei (prioritate maximă)
        if not self.current_question_id:
            existente = self.manager.get_questions_for_axis(self.current_axis_id)
            prioritate = len(existente) + 1
        else:
            # Dacă e editare, păstrăm prioritatea existentă
            item_selectat = self.questions_list.currentItem()
            if item_selectat:
                prioritate = item_selectat.data(Qt.UserRole)['wave']
            else:
                prioritate = 1

        success = self.manager.save_question(
            self.current_axis_id, text, tags, prioritate, options, self.current_question_id
        )
        
        if success:
            self.refresh_questions_list()
            self.editor_form.setVisible(False)
            QMessageBox.information(self, "Succes", "Întrebarea a fost salvată în bancă.")


    def delete_question(self):
        if self.current_question_id:
            self.manager.delete_question(self.current_question_id)
            self.refresh_questions_list()
            self.editor_form.setVisible(False)


    def suggest_question_with_ai(self):
        """Metodă integrală care analizează baza de date actuală și cere o sugestie AI complementară."""
        if not self.current_axis_id:
            QMessageBox.warning(self, "Atenție", "Selectați mai întâi o axă din listă pentru a genera o întrebare.")
            return

        # 1. Colectăm datele axei selectate din cache-ul local
        axa_data = next((ax for ax in self.all_axes_cache if ax["id"] == self.current_axis_id), None)
        if not axa_data: 
            return

        # 2. FEEDBACK VIZUAL: Schimbăm textul butonului
        self.btn_ai_suggest_q.setText("⌛ Analizez baza de date...")
        self.btn_ai_suggest_q.setEnabled(False)
        # Forțăm interfața să se updateze (aici era eroarea)
        QApplication.processEvents()

        # 3. EXTRAGEM ÎNTREBĂRILE EXISTENTE (pentru a evita redundanța)
        intrebari_existente = self.manager.get_questions_for_axis(self.current_axis_id)

        # 4. SOLICITĂM AI-ULUI O ÎNTREBARE NOUĂ ȘI UNICĂ
        self.btn_ai_suggest_q.setText("⌛ Generez întrebare unică...")
        QApplication.processEvents()
        
        rezultat_json = self.ai_agent.generate_single_question(axa_data, intrebari_existente)

        if rezultat_json and "text" in rezultat_json:
            # 5. POPULĂM FORMULARUL ÎNTREBĂRII
            self.inp_q_text.setPlainText(rezultat_json["text"])
            self.inp_tags.setText(rezultat_json["tags"])
            
            # Resetăm și populăm tabelul de opțiuni (cele 4 rânduri standard)
            self.tbl_options.setRowCount(0)
            self.tbl_options.setRowCount(4)
            for i, optiune in enumerate(rezultat_json["options"]):
                if i < 4:
                    # Inserăm textul variantei de răspuns
                    self.tbl_options.setItem(i, 0, QTableWidgetItem(optiune["text"]))
                    # Inserăm scorul asociat (0, 33, 66, 100)
                    self.tbl_options.setItem(i, 1, QTableWidgetItem(str(optiune["score"])))
            
            # Ne asigurăm că editorul este vizibil
            self.editor_form.setVisible(True)
            
            # Mesaj de confirmare în consolă dacă există
            if hasattr(self, 'txt_ai_chat_log'):
                self.txt_ai_chat_log.append(f"<p style='color: #e040fb;'><i>[AI]: Am analizat cele {len(intrebari_existente)} întrebări existente și am generat o variantă nouă pentru axa '{axa_data['name']}'.</i></p>")
        else:
            QMessageBox.critical(self, "Eroare AI", "Nu s-a putut genera o sugestie validă. Verificați conexiunea la internet sau cheia API.")

        # 6. RESTAURĂM BUTONUL
        self.btn_ai_suggest_q.setText("🤖 SUGESTIE AI")
        self.btn_ai_suggest_q.setEnabled(True)


    def update_question_priority(self, question_id, new_priority):
        """Metodă integrală care actualizează rangul de prioritate al unei întrebări."""
        conexiune = self.get_connection()
        try:
            cursor = conexiune.cursor()
            query = "UPDATE questions_bank SET wave_target = ? WHERE id = ?"
            cursor.execute(query, (new_priority, question_id))
            conexiune.commit()
            return True
        except Exception as e:
            log_error(f"Eroare la schimbarea priorității pentru întrebarea {question_id}", e)
            return False
        finally:
            conexiune.close()

    def move_question_up(self):
        """Împinge întrebarea selectată mai sus și salvează noua ierarhie în DB."""
        rand_curent = self.questions_list.currentRow()
        if rand_curent <= 0: return # Prima sau nimic selectat

        # 1. Obținem toate ID-urile în ordinea actuală din listă
        toate_id_urile = []
        for i in range(self.questions_list.count()):
            toate_id_urile.append(self.questions_list.item(i).data(Qt.UserRole)['id'])

        # 2. Inversăm ID-urile în listă (cel selectat cu cel de deasupra)
        toate_id_urile[rand_curent], toate_id_urile[rand_curent - 1] = toate_id_urile[rand_curent - 1], toate_id_urile[rand_curent]

        # 3. Trimitem noua secvență la manager pentru a fi salvată în DB
        success = self.manager.resequence_questions(self.current_axis_id, toate_id_urile)

        if success:
            # 4. Reîncărcăm lista și păstrăm selecția pe întrebarea mutată
            self.refresh_questions_list()
            self.questions_list.setCurrentRow(rand_curent - 1)


    def move_question_down(self):
        """Împinge întrebarea selectată mai jos și salvează noua ierarhie în DB."""
        rand_curent = self.questions_list.currentRow()
        if rand_curent < 0 or rand_curent >= self.questions_list.count() - 1: return

        # 1. Obținem toate ID-urile în ordinea actuală din listă
        toate_id_urile = []
        for i in range(self.questions_list.count()):
            toate_id_urile.append(self.questions_list.item(i).data(Qt.UserRole)['id'])

        # 2. Inversăm ID-urile (cel selectat cu cel de dedesubt)
        toate_id_urile[rand_curent], toate_id_urile[rand_curent + 1] = toate_id_urile[rand_curent + 1], toate_id_urile[rand_curent]

        # 3. Salvăm noua stare în baza de date
        success = self.manager.resequence_questions(self.current_axis_id, toate_id_urile)

        if success:
            # 4. Reîncărcăm și fixăm cursorul
            self.refresh_questions_list()
            self.questions_list.setCurrentRow(rand_curent + 1)

    def on_axis_selection_changed(self, element_curent, element_anterior):
        """Metodă integrală care încarcă datele axei indiferent dacă schimbarea vine din mouse sau tastatură."""
        # Verificăm dacă există un element selectat (pentru a evita erori la curățarea listei)
        if element_curent is not None:
            # Apelăm metoda ta existentă care populează câmpurile de editare
            self.on_axis_selected(element_curent)