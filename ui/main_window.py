import sys
from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtCore import Qt

# Importuri Logică și Utilitare
from logic.settings_manager import SettingsManager
from logger import log

# Importuri Tab-uri Interfață
from ui.tab_patients import PatientsTab
from ui.tab_knowledge import KnowledgeTab
from ui.tab_synergy import SynergyTab
from ui.tab_architect import ArchitectTab
from ui.tab_strategies import StrategyTab
from ui.tab_exam import ExamTab
from ui.tab_results import ResultsTab
from ui.tab_settings import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HUNTER PROTOCOL v3 - Enterprise Edition")
        self.settings = SettingsManager.load_settings()
        
        saved_geometry = self.settings.get("window_geometry")
        if saved_geometry and len(saved_geometry) == 4:
            self.resize(saved_geometry[0], saved_geometry[1])
            self.move(saved_geometry[2], saved_geometry[3])
        else:
            self.resize(1300, 850)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.setCentralWidget(self.tabs)
        
        # --- TAB-URI ---
        self.tab_patients = PatientsTab()
        self.tabs.addTab(self.tab_patients, "👥 1. Pacienți")

        self.tab_knowledge = KnowledgeTab()
        self.tabs.addTab(self.tab_knowledge, "🧠 2. Cunoștințe (Vault)")

        self.tab_synergy = SynergyTab()
        self.tabs.addTab(self.tab_synergy, "👹 3. Sinergii")

        self.tab_architect = ArchitectTab()
        self.tabs.addTab(self.tab_architect, "📐 4. Architect")

        self.tab_strategies = StrategyTab()
        self.tabs.addTab(self.tab_strategies, "📐 4.2. Strategii Protocol")

        self.tab_exam = ExamTab()
        self.tabs.addTab(self.tab_exam, "📝 5. Examen")

        self.tab_results = ResultsTab()
        self.tabs.addTab(self.tab_results, "📊 6. Rezultate")

        self.tab_settings = SettingsTab()
        self.tabs.addTab(self.tab_settings, "⚙️ 7. Setări")

        last_tab_index = self.settings.get("last_active_tab_index", 0)
        if last_tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab_index)
            
        # --- SINCRONIZARE TAB-URI (NOU) ---
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """Metodă integrală care sincronizează contextul pacientului între tab-uri."""
        
        # Indexul 6 este Tab-ul "Rezultate" în ierarhia noastră actuală:
        # 0:Pacienți, 1:Vault, 2:Sinergii, 3:Architect, 4:Strategii, 5:Examen, 6:Rezultate
        if index == 6:
            # Luăm ID-ul pacientului selectat în Tab-ul 1
            id_pacient_curent = self.tab_patients.current_patient_id
            
            if id_pacient_curent:
                # Transmitem ID-ul către Tab-ul 6 pentru încărcare automată
                log("sys", f"🔄 Sincronizare: Transfer subiect ID {id_pacient_curent} către modulul Rezultate.")
                
                # Apelăm metoda de setare din tabul de rezultate
                self.tab_results.set_active_patient(id_pacient_curent)
            else:
                log("sys", "ℹ️ Info Sincronizare: Niciun pacient selectat în Tab-ul 1. Rezultatele vor rămâne libere.")

    def closeEvent(self, event):
        current_geometry = [self.width(), self.height(), self.x(), self.y()]
        SettingsManager.update_key("window_geometry", current_geometry)
        SettingsManager.update_key("last_active_tab_index", self.tabs.currentIndex())
        event.accept()
    def sync_patient_selection(self, patient_id, source_tab):
        """
        SINCRONIZARE GLOBALĂ: Actualizează selecția pacientului în TOATE tab-urile
        @param patient_id: ID-ul pacientului selectat
        @param source_tab: Tab-ul care a inițiat sincronizarea ('tab_patients', 'tab_exam', 'tab_results')
        """
        print(f"\n[SYNC] Patient {patient_id} selected from {source_tab}")
        
        # Sincronizăm Tab 1 (Pacienți) - dacă nu e sursa
        if source_tab != 'tab_patients' and hasattr(self, 'tab_patients'):
            print(f"[SYNC] Updating tab_patients...")
            self.tab_patients.set_selected_patient(patient_id, from_sync=True)
        
        # Sincronizăm Tab 5 (Examen) - dacă nu e sursa  
        if source_tab != 'tab_exam' and hasattr(self, 'tab_exam'):
            print(f"[SYNC] Updating tab_exam...")
            self.tab_exam.set_selected_patient(patient_id, from_sync=True)
        
        # Sincronizăm Tab 6 (Rezultate) - dacă nu e sursa
        if source_tab != 'tab_results' and hasattr(self, 'tab_results'):
            print(f"[SYNC] Updating tab_results...")
            self.tab_results.set_active_patient(patient_id, from_sync=True)
        
        print(f"[SYNC] Complete!\n")
