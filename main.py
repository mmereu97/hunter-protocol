import sys
from PySide6.QtWidgets import QApplication
from config import Config
from ui.main_window import MainWindow

# 1. Validare Configurație la pornire
# (Verifică dacă există .env și calea către baza de date)
Config.validate()

if __name__ == "__main__":
    # 2. Inițializare Aplicație Qt
    app = QApplication(sys.argv)

    # 3. Stil Global (Baseline Cyberpunk)
    # Acest CSS se aplică peste tot, inclusiv pe ferestrele de dialog (QMessageBox)
    app.setStyleSheet("""
        /* Fereastra Generală */
        QMainWindow, QDialog, QMessageBox {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        /* Font Global */
        QWidget {
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        
        /* Tab-urile de sus */
        QTabWidget::pane {
            border: 1px solid #333;
            background-color: #0b0b0b;
        }
        QTabBar::tab {
            background: #1a1a1a;
            color: #888;
            padding: 8px 20px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background: #007acc; /* Albastru electric pentru Tab Activ */
            color: white;
            border-bottom: 2px solid #00e5ff; /* Linie neon jos */
        }
        QTabBar::tab:hover {
            background: #2a2a2a;
            color: #ccc;
        }

        /* Scrollbars (Discrete și întunecate) */
        QScrollBar:vertical {
            background: #111;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #444;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #666;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        /* Tooltips */
        QToolTip {
            background-color: #222;
            color: #00e5ff;
            border: 1px solid #444;
            padding: 5px;
        }
    """)

    # 4. Lansare Fereastră Principală
    window = MainWindow()
    window.show()

    # 5. Start Bucla de Evenimente
    sys.exit(app.exec())