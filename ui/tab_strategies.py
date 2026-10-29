from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QListWidget, QListWidgetItem, 
    QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, 
    QSplitter, QMessageBox
)
from PySide6.QtCore import Qt
from logic.strategy_manager import StrategyManager

STRAT_STYLE = """
    QWidget { background-color: #0b0b0b; color: #e0e0e0; font-family: 'Segoe UI'; }
    QFrame#FormBox { border: 1px solid #333; background-color: #111; border-radius: 8px; }
    QLabel#SectionTitle { color: #00e5ff; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    
    QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QTextEdit {
        background-color: #050505; border: 1px solid #444; color: #00ff69; padding: 5px;
    }
    
    QPushButton#SaveBtn { background-color: #2e7d32; color: white; font-weight: bold; padding: 10px; }
    QPushButton#DelBtn { background-color: #b71c1c; color: white; padding: 5px; }
    
    QLabel#HelpTxt { color: #888; font-style: italic; font-size: 11px; }
"""

class StrategyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = StrategyManager()
        self.current_strategy_id = None
        self.setStyleSheet(STRAT_STYLE)
        self.setup_ui()
        self.load_strategies()

    def setup_ui(self):
        # Layout principal al tabului
        self.layout_principal_orizontal = QHBoxLayout(self)
        self.layout_principal_orizontal.setContentsMargins(5, 5, 5, 5)
        self.layout_principal_orizontal.setSpacing(10)
        
        self.splitter_principal = QSplitter(Qt.Horizontal)

        # =====================================================================
        # PANOU STÂNGA: LISTĂ PROTOCOALE (STRATEGII)
        # =====================================================================
        self.panou_stanga = QFrame()
        self.layout_stanga = QVBoxLayout(self.panou_stanga)
        
        self.label_titlu_lista = QLabel("📖 PROTOCOALE DE EXECUȚIE (STRATEGII):")
        self.layout_stanga.addWidget(self.label_titlu_lista)
        
        self.list_strategies = QListWidget()
        self.list_strategies.itemClicked.connect(self.on_strategy_selected)
        self.layout_stanga.addWidget(self.list_strategies)
        
        self.layout_rand_admin_liste = QHBoxLayout()
        self.btn_new = QPushButton("📄 NOU")
        self.btn_new.clicked.connect(self.reset_form)
        
        self.btn_delete_strat = QPushButton("🗑️ ȘTERGE")
        self.btn_delete_strat.setObjectName("DelBtn")
        self.btn_delete_strat.clicked.connect(self.delete_strategy_handler)
        
        self.layout_rand_admin_liste.addWidget(self.btn_new)
        self.layout_rand_admin_liste.addWidget(self.btn_delete_strat)
        self.layout_stanga.addLayout(self.layout_rand_admin_liste)

        # =====================================================================
        # PANOU DREAPTA: EDITOR ALGORITM
        # =====================================================================
        self.panou_dreapta = QFrame()
        self.panou_dreapta.setObjectName("FormBox")
        self.layout_dreapta = QVBoxLayout(self.panou_dreapta)
        self.layout_dreapta.setContentsMargins(15, 15, 15, 15)
        
        self.label_header_editor = QLabel("📐 CONFIGURARE INTELIGENȚĂ EXAMEN (FILTRU DUAL)")
        self.layout_dreapta.addWidget(self.label_header_editor)
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Nume Protocol")
        self.layout_dreapta.addWidget(QLabel("NUME PROTOCOL:"))
        self.layout_dreapta.addWidget(self.inp_name)
        
        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(60)
        self.layout_dreapta.addWidget(QLabel("DESCRIERE LOGICĂ:"))
        self.layout_dreapta.addWidget(self.txt_desc)

        # ZONA DE PARAMETRI
        self.algo_box = QFrame()
        self.algo_box.setStyleSheet("border: 1px solid #333; padding: 10px; background: #050505; border-radius: 5px;")
        self.layout_algo = QVBoxLayout(self.algo_box)

        # 1. Start
        row_w1 = QHBoxLayout()
        self.spin_w1_qty = QSpinBox()
        self.spin_w1_qty.setRange(1, 10)
        self.spin_w1_qty.setValue(3)
        row_w1.addWidget(QLabel("VAL 1: NR. ÎNTREBĂRI START:"))
        row_w1.addWidget(self.spin_w1_qty)
        self.layout_algo.addLayout(row_w1)

        # 2. Galben
        row_y = QHBoxLayout()
        self.spin_yellow_jump = QSpinBox()
        self.spin_yellow_jump.setValue(3)
        lbl_y = QLabel("🟨 EXTRA PT. BILA GALBENA / SALT 1 NIVEL:")
        lbl_y.setStyleSheet("color: #ffcc00;")
        row_y.addWidget(lbl_y); row_y.addWidget(self.spin_yellow_jump)
        self.layout_algo.addLayout(row_y)

        # 3. Roșu
        row_r = QHBoxLayout()
        self.spin_red_jump = QSpinBox()
        self.spin_red_jump.setValue(7)
        lbl_r = QLabel("🟥 EXTRA PT. BILA ROSIE / SALT 2+ NIVELE:")
        lbl_r.setStyleSheet("color: #ff5252;")
        row_r.addWidget(lbl_r); row_r.addWidget(self.spin_red_jump)
        self.layout_algo.addLayout(row_r)

        # 4. Praguri Abatere
        row_dev = QHBoxLayout()
        self.spin_dev_minor_thresh = QSpinBox(); self.spin_dev_minor_thresh.setValue(20)
        self.spin_dev_major_thresh = QSpinBox(); self.spin_dev_major_thresh.setValue(30)
        row_dev.addWidget(QLabel("Prag Galben (>):")); row_dev.addWidget(self.spin_dev_minor_thresh)
        row_dev.addWidget(QLabel("Prag Roșu (>):")); row_dev.addWidget(self.spin_dev_major_thresh)
        self.layout_algo.addLayout(row_dev)

        # 5. DECLANȘARE MONȘTRI (REPARAT ȘI STANDARDIZAT)
        row_time = QHBoxLayout()
        self.cmb_timing = QComboBox()
        self.cmb_timing.addItems([
            "Dupa Val 1 (Screening)", 
            "Dupa Val 2 (Stabilizare)", 
            "La Finalul Testului"
        ])
        row_time.addWidget(QLabel("⏰ DECLANȘARE MONȘTRI:"))
        row_time.addWidget(self.cmb_timing)
        self.layout_algo.addLayout(row_time)
        
        # 6. ÎNTREBĂRI INJECTATE PER MONSTRU
        row_monster_qty = QHBoxLayout()
        self.spin_monster_qty = QSpinBox()
        self.spin_monster_qty.setRange(1, 10)
        self.spin_monster_qty.setValue(3)  # Default 3
        self.spin_monster_qty.setFixedWidth(70)
        row_monster_qty.addWidget(QLabel("💉 ÎNTREBĂRI INJECTATE / MONSTRU:"))
        row_monster_qty.addWidget(self.spin_monster_qty)
        row_monster_qty.addStretch()
        self.layout_algo.addLayout(row_monster_qty)

        self.layout_dreapta.addWidget(self.algo_box)

        # Buton Salvare
        self.btn_save = QPushButton("💾 SALVEAZĂ ALGORITMUL PROTOCOLULUI")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.clicked.connect(self.save_strategy)
        
        self.layout_dreapta.addStretch()
        self.layout_dreapta.addWidget(self.btn_save)

        self.splitter_principal.addWidget(self.panou_stanga)
        self.splitter_principal.addWidget(self.panou_dreapta)
        self.splitter_principal.setSizes([350, 750])
        self.layout_principal_orizontal.addWidget(self.splitter_principal)

    def load_strategies(self):
        """Metodă integrală care încarcă toate strategiile disponibile din baza de date."""
        self.list_strategies.clear()
        
        lista_bruta = self.manager.get_all_strategies()
        
        for strategie in lista_bruta:
            # Structura tuple din DB: (id, name, description, w1, yellow, red, timing, is_active, dev_minor_t, dev_major_t, dev_minor_q, dev_major_q, monster_qty)
            nume_afisat = strategie[1]
            item = QListWidgetItem(nume_afisat)
            
            # Atașăm obiectul complet datelor item-ului pentru acces rapid la click
            item.setData(Qt.UserRole, strategie)
            self.list_strategies.addItem(item)
            
        # Deselectăm orice element pentru a menține starea curată
        self.list_strategies.clearSelection()

    def on_strategy_selected(self, item):
        """Metodă integrală care încarcă profilul și identifică inteligent poziția meniului."""
        date_strategie = item.data(Qt.UserRole)
        # Indexuri: 0:id, 1:name, 2:desc, 3:w1, 4:yellow, 5:red, 6:timing, 8:dev_minor_t, 9:dev_major_t, 12:monster_qty
        
        self.current_strategy_id = date_strategie[0]
        self.inp_name.setText(str(date_strategie[1]))
        self.txt_desc.setPlainText(str(date_strategie[2]))
        self.spin_w1_qty.setValue(date_strategie[3])
        self.spin_yellow_jump.setValue(date_strategie[4])
        self.spin_red_jump.setValue(date_strategie[5])
        
        if len(date_strategie) > 9:
            self.spin_dev_minor_thresh.setValue(date_strategie[8])
            self.spin_dev_major_thresh.setValue(date_strategie[9])
        
        # Încărcăm monster_qty (indexul 12)
        if len(date_strategie) > 12:
            self.spin_monster_qty.setValue(date_strategie[12])

        # --- LOGICĂ BLINDATĂ DE SELECȚIE TIMING ---
        text_din_db = str(date_strategie[6])
        
        index_final = 0 # Default pe Val 1
        
        # Căutăm prin toate opțiunile din meniu
        for i in range(self.cmb_timing.count()):
            text_optiune = self.cmb_timing.itemText(i)
            
            # Verificăm dacă textul din DB se regăsește în opțiune sau invers
            # Folosim keywords pentru a evita problemele cu diacriticele (După vs Dupa)
            if "Val 2" in text_din_db or "Stabilizare" in text_din_db:
                index_final = 1
                break
            elif "Final" in text_din_db:
                index_final = 2
                break
            elif "Val 1" in text_din_db or "Screening" in text_din_db:
                index_final = 0
                break

        self.cmb_timing.setCurrentIndex(index_final)



    def save_strategy(self):
        """Metodă integrală care salvează setările asigurând formatul corect de text."""
        nume_protocol = self.inp_name.text().strip()
        if not nume_protocol:
            QMessageBox.warning(self, "Atenție", "Numele este obligatoriu.")
            return

        # Salvăm textul exact din ComboBox pentru a asigura consistența viitoare
        text_timing_ales = self.cmb_timing.currentText()

        success = self.manager.save_strategy(
            nume_protocol,
            self.txt_desc.toPlainText(),
            self.spin_w1_qty.value(),
            self.spin_yellow_jump.value(),
            self.spin_red_jump.value(),
            self.spin_dev_minor_thresh.value(),
            self.spin_yellow_jump.value(), # dev_minor_qty
            self.spin_dev_major_thresh.value(),
            self.spin_red_jump.value(), # dev_major_qty
            text_timing_ales,
            self.spin_monster_qty.value(),  # NEW: monster_qty
            self.current_strategy_id
        )

        if success:
            QMessageBox.information(self, "Succes", "Algoritmul a fost salvat.")
            self.load_strategies()
        else:
            QMessageBox.critical(self, "Eroare", "Eșec la salvare.")

            
    def delete_strategy(self):
        if not self.current_strategy_id: return
        if QMessageBox.question(self, "Confirmare", "Ștergi acest protocol?") == QMessageBox.Yes:
            self.manager.delete_strategy(self.current_strategy_id)
            self.reset_form()
            self.load_strategies()

    def reset_form(self):
        """Metodă integrală care resetează formularul și impune regula ta de aur."""
        self.current_strategy_id = None
        self.inp_name.clear()
        self.txt_desc.clear()
        self.spin_w1_qty.setValue(3)
        self.spin_yellow_jump.setValue(3)
        self.spin_red_jump.setValue(7)
        self.spin_dev_minor_thresh.setValue(20)
        self.spin_dev_major_thresh.setValue(30)
        self.spin_monster_qty.setValue(3)  # NEW: reset monster_qty
        
        # IMPUNEM REGULA TA: Monștrii se declanșează după Valul 2
        # Indexul 1 corespunde cu "Dupa Val 2 (Stabilizare)"
        self.cmb_timing.setCurrentIndex(1)
        
        self.list_strategies.clearSelection()
        self.inp_name.setFocus()

    def delete_strategy_handler(self):
        """Metodă integrală care șterge protocolul de strategie selectat cu confirmare."""
        # Verificăm dacă avem ceva selectat în listă
        element_selectat = self.list_strategies.currentItem()
        
        if not element_selectat:
            QMessageBox.warning(self, "Atenție", "Selectați un protocol din lista din stânga pentru a-l șterge.")
            return

        id_strategie = self.current_strategy_id
        nume_strategie = self.inp_name.text()

        # Barieră de securitate: Confirmare ștergere
        confirmare = QMessageBox.question(
            self, 
            "Confirmare Ștergere", 
            f"Sunteți sigur că doriți să ștergeți protocolul: '{nume_strategie}'?\n\n"
            "Această acțiune este definitivă.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirmare == QMessageBox.Yes:
            # Apelăm managerul pentru a șterge din baza de date
            self.manager.delete_strategy(id_strategie)
            
            # Resetăm formularul și reîncărcăm lista vizuală
            self.reset_form()
            self.load_strategies()
            
            QMessageBox.information(self, "Succes", f"Protocolul '{nume_strategie}' a fost șters.")