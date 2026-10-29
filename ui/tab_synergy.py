from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QComboBox, QSpinBox, QPushButton, QSplitter, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QLineEdit
)
from PySide6.QtCore import Qt
from logic.synergy_manager import SynergyManager
from logger import log

# Stil Cyberpunk Local (pt Tabele si Liste specifice)
MONSTER_STYLE = """
    /* BAZA */
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }

    /* LISTA MONȘTRI (STÂNGA) */
    QListWidget { 
        background-color: #1a0505; 
        color: #ff5252; 
        border: 1px solid #550000; 
        font-size: 13px; 
    }
    QListWidget::item:selected { 
        background-color: #ff0000; 
        color: black; 
        font-weight: bold; 
    }
    
    /* INPUTS & COMBOS */
    QLineEdit, QComboBox, QSpinBox { 
        background-color: #151515; 
        color: white; 
        border: 1px solid #555; 
        padding: 5px; 
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1px solid #ff5252; 
    }
    
    /* LABELS */
    QLabel { font-weight: bold; color: #ccc; }
    
    /* TABEL DREAPTA */
    QTableWidget { 
        background-color: #0f0f0f; 
        color: cyan; 
        gridline-color: #333; 
        border: 1px solid #333; 
    }
    QHeaderView::section { background-color: #222; color: white; }
    
    /* BUTOANE */
    QPushButton {
        background-color: #1f1f1f;
        color: #ccc;
        border: 1px solid #444;
        padding: 6px;
        border-radius: 3px;
    }
    QPushButton:hover { background-color: #333; border: 1px solid #666; color: white; }
"""

class SynergyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = SynergyManager()
        self.current_monster_id = None
        
        # Cache pentru filtrare/sortare
        self.all_monsters_cache = [] 
        
        self.setStyleSheet(MONSTER_STYLE)
        self.setup_ui()
        self.load_monsters()
        self.load_trigger_options()

    def setup_ui(self):
        from logic.settings_manager import SettingsManager
        
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # ==========================
        # STÂNGA: LISTA MONȘTRI & SETĂRI
        # ==========================
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 10, 5, 10)
        
        left_layout.addWidget(QLabel("👹 SELECTEAZĂ MONSTRUL:"))
        
        # TOOLBAR FILTRARE
        filter_row = QHBoxLayout()
        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["Sort: Nume (A-Z)", "Sort: ID (Cresc.)"])
        self.cmb_sort.currentIndexChanged.connect(self.filter_monsters_list)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Caută...")
        self.search_bar.textChanged.connect(self.filter_monsters_list)
        
        filter_row.addWidget(self.cmb_sort, 1)
        filter_row.addWidget(self.search_bar, 1)
        left_layout.addLayout(filter_row)
        
        # Lista propriu-zisă
        self.monsters_list = QListWidget()
        self.monsters_list.itemClicked.connect(self.on_monster_selected)
        left_layout.addWidget(self.monsters_list)
        
        # ==========================
        # DREAPTA: EDITOR REGULI
        # ==========================
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        self.lbl_current_monster = QLabel("NICIUN MONSTRU SELECTAT")
        self.lbl_current_monster.setStyleSheet("font-size: 16px; color: #ff5252; border-bottom: 2px solid #550000; padding-bottom: 10px;")
        right_layout.addWidget(self.lbl_current_monster)
        
        # Tabel Reguli Existente
        right_layout.addWidget(QLabel("📋 REGULI ACTIVE (Condiții de declanșare):"))
        self.rules_table = QTableWidget(0, 4) 
        self.rules_table.setHorizontalHeaderLabels(["Dacă Axa...", "Este...", "Decât...", "ID"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rules_table.setColumnHidden(3, True) 
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        right_layout.addWidget(self.rules_table)
        
        btn_del_rule = QPushButton("🗑️ Șterge Regula Selectată")
        btn_del_rule.setStyleSheet("color: #ff5252; border: 1px solid #ff5252; padding: 5px;")
        btn_del_rule.clicked.connect(self.delete_rule)
        right_layout.addWidget(btn_del_rule)
        
        # Formular Adăugare Regulă Nouă
        add_box = QFrame()
        add_box.setStyleSheet("background-color: #111; border: 1px solid #333; margin-top: 20px; border-radius: 5px;")
        add_layout = QVBoxLayout(add_box)
        add_layout.addWidget(QLabel("➕ ADAUGĂ CONDITIE NOUĂ:"))
        
        form_h = QHBoxLayout()
        
        self.cmb_triggers = QComboBox() 
        self.cmb_triggers.setStyleSheet("min-width: 200px;")
        
        self.cmb_operator = QComboBox()
        self.cmb_operator.addItems(["> (Mai Mare)", "< (Mai Mic)"])
        self.cmb_operator.setFixedWidth(100)
        
        self.spin_val = QSpinBox()
        self.spin_val.setRange(0, 100)
        self.spin_val.setValue(50)
        self.spin_val.setFixedWidth(60)
        
        btn_add = QPushButton("LEAGĂ")
        btn_add.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.add_rule)
        
        form_h.addWidget(self.cmb_triggers)
        form_h.addWidget(self.cmb_operator)
        form_h.addWidget(self.spin_val)
        form_h.addWidget(btn_add)
        
        add_layout.addLayout(form_h)
        right_layout.addWidget(add_box)
        right_layout.addStretch()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 950])
        main_layout.addWidget(splitter)

        # --- ZONA BUTOANE JOS (În interiorul setup_ui din tab_synergy.py) ---
        self.layout_actiuni_sinergii = QHBoxLayout()
        
        self.btn_export_rules = QPushButton("📤 EXPORTĂ REGULI PENTRU AI")
        self.btn_export_rules.setStyleSheet("background-color: #1a1a1a; color: #00e5ff; border: 1px solid #00e5ff;")
        self.btn_export_rules.clicked.connect(self.export_rules_handler)
        
        self.btn_del_rule = QPushButton("🗑️ ȘTERGE REGULA SELECTATĂ")
        self.btn_del_rule.setStyleSheet("color: #ff5252; border: 1px solid #ff5252;")
        self.btn_del_rule.clicked.connect(self.delete_rule)
        
        self.layout_actiuni_sinergii.addWidget(self.btn_export_rules)
        self.layout_actiuni_sinergii.addWidget(self.btn_del_rule)
        
        # Adăugăm rândul de butoane în layout-ul din dreapta
        right_layout.addLayout(self.layout_actiuni_sinergii)

    # ==========================
    # LOGICA DATE
    # ==========================
    def load_monsters(self):
        """Încarcă monștrii din DB și îi cacheuiește."""
        raw_data = self.manager.get_monsters() # Returns [(id, name), ...]
        
        self.all_monsters_cache = []
        for mid, name in raw_data:
            self.all_monsters_cache.append({
                "id": mid,
                "name": name
            })
            
        # Refresh lista vizuală
        self.filter_monsters_list()

    def filter_monsters_list(self):
        """Aplică sortarea și căutarea."""
        self.monsters_list.clear()
        
        text = self.search_bar.text().lower()
        sort_mode = self.cmb_sort.currentText()
        
        # 1. Filtrare
        filtered = []
        for m in self.all_monsters_cache:
            # Căutăm în nume sau ID
            content = f"{m['name']} {m['id']}".lower()
            if text and (text not in content):
                continue
            filtered.append(m)
            
        # 2. Sortare
        if "ID" in sort_mode:
            filtered.sort(key=lambda x: x["id"])
        else: # Nume A-Z
            filtered.sort(key=lambda x: x["name"])
            
        # 3. Afișare
        for m in filtered:
            # FORMATUL NOU: Nume [ID]
            display_text = f"{m['name']} [{m['id']}]"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, m['id'])
            self.monsters_list.addItem(item)

    def load_trigger_options(self):
        self.cmb_triggers.clear()
        axes = self.manager.get_all_axes_for_dropdown()
        for aid, name in axes:
            self.cmb_triggers.addItem(f"{name} [{aid}]", aid)

    def on_monster_selected(self, item):
        self.current_monster_id = item.data(Qt.UserRole)
        # Update Label Dreapta
        self.lbl_current_monster.setText(f"CONFIGURARE: {item.text()}")
        self.refresh_rules_table()

    def refresh_rules_table(self):
        if not self.current_monster_id: return
        
        self.rules_table.setRowCount(0)
        rules = self.manager.get_rules_for_monster(self.current_monster_id)
        
        for row_idx, (rid, trig_id, trig_name, op, val) in enumerate(rules):
            self.rules_table.insertRow(row_idx)
            self.rules_table.setItem(row_idx, 0, QTableWidgetItem(f"{trig_name} [{trig_id}]"))
            self.rules_table.setItem(row_idx, 1, QTableWidgetItem(op))
            self.rules_table.setItem(row_idx, 2, QTableWidgetItem(str(val)))
            self.rules_table.setItem(row_idx, 3, QTableWidgetItem(str(rid)))

    def add_rule(self):
        if not self.current_monster_id:
            QMessageBox.warning(self, "Atenție", "Selectează un monstru din stânga!")
            return
            
        trigger_id = self.cmb_triggers.currentData()
        op_text = self.cmb_operator.currentText()
        op = ">" if ">" in op_text else "<"
        val = self.spin_val.value()
        
        success = self.manager.add_rule(self.current_monster_id, trigger_id, op, val)
        if success:
            self.refresh_rules_table()
        else:
            QMessageBox.critical(self, "Eroare", "Nu s-a putut adăuga regula.")

    def delete_rule(self):
        row = self.rules_table.currentRow()
        if row < 0: return
        
        rule_id = int(self.rules_table.item(row, 3).text())
        self.manager.delete_rule(rule_id)
        self.refresh_rules_table()

    def export_rules_handler(self):
        """Metodă integrală care generează un fișier text cu logica sinergiilor pentru analiză AI."""
        from PySide6.QtWidgets import QFileDialog
        
        cale_fisier, _ = QFileDialog.getSaveFileName(
            self, "Exportă Logica Sinergiilor", "", "Text Files (*.txt);;Markdown (*.md)"
        )
        if not cale_fisier:
            return

        # Obținem datele brute de la manager
        date_reguli = self.manager.get_all_rules_with_full_metadata()
        
        if not date_reguli:
            QMessageBox.information(self, "Info", "Nu există reguli definite pentru export.")
            return

        # Construim conținutul textului
        continut = "HUNTER PROTOCOL - SYNERGY RULES & MONSTER LOGIC\n"
        continut += "="*60 + "\n"
        continut += "SCOP: Analiza conditiilor de declansare a axelor de risc (Monstri).\n"
        continut += "="*60 + "\n\n"

        monstru_curent = ""
        for r in date_reguli:
            # Structura r: id, m_name, m_source, t_name, t_source, t_left, t_right, op, val
            m_name, m_source, t_name, t_source, t_left, t_right, op, val = r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
            
            # Grupăm vizual regulile după axa Monstru
            if m_name != monstru_curent:
                continut += f"\n👹 ȚINTĂ (MONSTRU): {m_name.upper()}\n"
                continut += f"   Sursă Sistem: {m_source}\n"
                continut += f"   " + "-"*40 + "\n"
                monstru_curent = m_name
            
            # Detaliem regula
            continut += f"   Dacă Ingredientul: {t_name} [{t_source}]\n"
            continut += f"   Definiție Poli: (0 = {t_left} | 100 = {t_right})\n"
            continut += f"   CONDIȚIE: Scor {op} {val}\n"
            continut += f"   " + "."*20 + "\n"

        try:
            with open(cale_fisier, "w", encoding="utf-8") as f:
                f.write(continut)
            QMessageBox.information(self, "Succes", f"Logica sinergiilor a fost exportată în: {cale_fisier}")
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut scrie fișierul: {e}")