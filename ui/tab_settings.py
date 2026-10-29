from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QComboBox, QFrame, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from logic.settings_manager import SettingsManager

# ==========================================
# 🎨 STIL CYBERPUNK DEDICAT SETĂRILOR
# ==========================================
SETTINGS_STYLE = """
    QWidget {
        background-color: #0b0b0b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    
    /* TITLURI ȘI ETICHETE */
    QLabel {
        color: #e0e0e0; /* Forțăm alb/gri deschis */
        background: transparent;
    }
    
    QLabel#TitleLabel {
        color: #00e5ff; /* Cyan pentru titlu */
        font-size: 22px;
        font-weight: bold;
    }
    
    QLabel#SubLabel {
        color: #888888;
        font-size: 11px;
    }

    /* ZONELE DE GRUPARE (FRAMES) */
    QFrame#SectionBox {
        border: 1px solid #333;
        background-color: #111;
        border-radius: 10px;
    }

    /* INPUTS (SPINBOX & COMBOBOX) */
    QSpinBox, QComboBox {
        background-color: #050505;
        border: 1px solid #444;
        color: #00ff69; /* Verde Neon pentru cifre și selecții */
        padding: 5px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    QSpinBox:focus, QComboBox:focus {
        border: 1px solid #00e5ff;
    }

    /* BUTOANE */
    QPushButton#SaveBtn {
        background-color: #004d40;
        color: #00ff69;
        font-weight: bold;
        padding: 15px;
        border: 1px solid #00ff69;
        border-radius: 5px;
    }
    
    QPushButton#SaveBtn:hover {
        background-color: #00695c;
        color: white;
    }

    /* Stil pentru interiorul listei ComboBox */
    QComboBox QAbstractItemView {
        background-color: #111;
        color: #00ff69;
        selection-background-color: #00e5ff;
        selection-color: black;
        border: 1px solid #444;
    }
"""

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        # Încărcăm setările curente din JSON
        self.settings_data = SettingsManager.load_settings()
        
        # Aplicăm stilul Cyberpunk reparat
        self.setStyleSheet(SETTINGS_STYLE)
        
        # Construim interfața
        self.setup_ui()

    def setup_ui(self):
        # Layout principal cu margini generoase
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(50, 50, 50, 50)
        self.layout_principal.setSpacing(20)
        
        # --- TITLU ---
        self.lbl_main_title = QLabel("⚙️ SETĂRI GLOBALE HUNTER PROTOCOL")
        self.lbl_main_title.setObjectName("TitleLabel")
        self.layout_principal.addWidget(self.lbl_main_title)

        # =====================================================================
        # SECȚIUNEA 1: RECURENȚĂ ÎNTREBĂRI (SMART SKIP)
        # =====================================================================
        self.box_memorie = QFrame()
        self.box_memorie.setObjectName("SectionBox")
        self.layout_memorie = QVBoxLayout(self.box_memorie)
        self.layout_memorie.setContentsMargins(20, 20, 20, 20)
        self.layout_memorie.setSpacing(10)
        
        # Explicații
        self.layout_memorie.addWidget(QLabel("🔄 REGULĂ RECURENȚĂ ÎNTREBĂRI:"))
        self.lbl_help = QLabel("Dacă un pacient a răspuns deja la o întrebare, sistemul o va sări și va folosi vechiul răspuns.")
        self.lbl_help.setObjectName("SubLabel")
        self.layout_memorie.addWidget(self.lbl_help)
        
        # Rândul de control
        self.layout_rand_control = QHBoxLayout()
        
        self.label_instructiune = QLabel("Nu repeta aceeași întrebare timp de:")
        self.layout_rand_control.addWidget(self.label_instructiune)
        
        # SpinBox pentru cifră (ex: 6)
        self.spin_recurrence_value = QSpinBox()
        self.spin_recurrence_value.setRange(0, 999)
        self.spin_recurrence_value.setFixedWidth(80)
        self.spin_recurrence_value.setValue(self.settings_data.get("question_recurrence_value", 6))
        self.layout_rand_control.addWidget(self.spin_recurrence_value)
        
        # ComboBox pentru unitate (Zile/Luni/Ani)
        self.cmb_recurrence_unit = QComboBox()
        self.cmb_recurrence_unit.addItems(["Zile", "Săptămâni", "Luni", "Ani"])
        self.cmb_recurrence_unit.setFixedWidth(120)
        unitatea_salvata = self.settings_data.get("question_recurrence_unit", "Luni")
        self.cmb_recurrence_unit.setCurrentText(unitatea_salvata)
        self.layout_rand_control.addWidget(self.cmb_recurrence_unit)
        
        self.layout_rand_control.addStretch() # Împinge elementele la stânga
        self.layout_memorie.addLayout(self.layout_rand_control)
        
        self.layout_principal.addWidget(self.box_memorie)

        # --- SPAȚIU PENTRU ALTE SETĂRI VIITOARE ---
        # (Aici poți adăuga secțiuni similare pentru DB Export sau Security)

        # =====================================================================
        # BUTON SALVARE FINALĂ
        # =====================================================================
        self.btn_save_all = QPushButton("💾 SALVEAZĂ TOATE SETĂRILE")
        self.btn_save_all.setObjectName("SaveBtn")
        self.btn_save_all.setCursor(Qt.PointingHandCursor)
        self.btn_save_all.clicked.connect(self.save_settings_logic)
        self.layout_principal.addWidget(self.btn_save_all)
        
        # Stretch final pentru a ține totul sus
        self.layout_principal.addStretch()

    def save_settings_logic(self):
        """Metodă integrală pentru salvarea permanentă a noilor parametri."""
        valoare = self.spin_recurrence_value.value()
        unitate = self.cmb_recurrence_unit.currentText()
        
        # Salvăm în fișierul JSON prin intermediul Managerului
        SettingsManager.update_key("question_recurrence_value", valoare)
        SettingsManager.update_key("question_recurrence_unit", unitate)
        
        QMessageBox.information(self, "Succes", f"Configurația a fost salvată:\nSmart Skip activat pentru {valoare} {unitate.lower()}.")