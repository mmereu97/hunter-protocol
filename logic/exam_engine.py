import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from config import Config
from logger import log, log_error

class ExamEngine:
    def __init__(self):
        self.db_path = Config.DB_NAME
        self.patient_id = None
        self.template_id = None
        self.strategy_id = None  # ID-ul strategiei Hunter Protocol v3
        self.session_id = None
        self.queue = []
        self.answers_log = {}     
        self.triggered_monsters = set()
        self.current_question = None
        self.asked_hashes = set()
        self.cutoff_date = None
        
        # Flag-uri pentru controlul tranzitiei intre valuri
        self.wave_2_planned = False
        self.wave_3_planned = False
        
        # Tracking progres pentru UI (pentru pauză/reluare)
        self.total_questions_planned = 0  # Câte întrebări au fost planificate la început
        self.questions_answered = 0       # Câte întrebări au fost răspunse până acum

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def start_new_session(self, patient_id, template_id, strategy_id=None):
        """Inițializează sesiunea și încarcă coada de Screening (Val 1)."""
        from logger import log
        
        self.patient_id = patient_id
        self.template_id = template_id
        self.strategy_id = strategy_id  # Salvăm strategy_id pentru folosire ulterioară
        self.answers_log = {}
        self.asked_hashes = set()
        self.triggered_monsters = set()
        self.wave_2_planned = False
        self.wave_3_planned = False
        
        log("strategy_debug", "═══════════════════════════════════════════════════════════════")
        log("strategy_debug", f"🚀 PORNIRE SESIUNE NOUĂ")
        log("strategy_debug", f"  Patient ID: {patient_id}")
        log("strategy_debug", f"  Template ID: {template_id}")
        log("strategy_debug", f"  Strategy ID (primit): {strategy_id}")
        log("strategy_debug", "═══════════════════════════════════════════════════════════════")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"\n\033[94m[ENGINE] >>> PORNIRE SESIUNE (Subiect ID: {patient_id})\033[0m")

            # 1. Încărcăm Template-ul
            log("strategy_debug", f"📋 ÎNCĂRCARE TEMPLATE (ID={template_id})")
            cursor.execute("SELECT config_json, strategy_id FROM test_templates WHERE id=?", (template_id,))
            row = cursor.fetchone()
            if not row: 
                log("strategy_debug", "❌ Template invalid!")
                return False, "Template invalid."
            
            config = json.loads(row[0])
            id_strategie_din_template = row[1]
            wave1_axes = config.get("axes", config.get("wave1", {}).get("axes", []))
            
            # PRIORITATE: strategy_id primit din Tab 5 > strategy_id din template
            if strategy_id:
                id_strategie = strategy_id
                log("strategy_debug", f"  ✅ Template încărcat")
                log("strategy_debug", f"  Strategy ID (din template): {id_strategie_din_template}")
                log("strategy_debug", f"  Strategy ID (primit din Tab 5): {strategy_id}")
                log("strategy_debug", f"  ✅ PRIORITATE: Folosesc strategy_id={id_strategie} din Tab 5!")
            else:
                id_strategie = id_strategie_din_template
                log("strategy_debug", f"  ✅ Template încărcat")
                log("strategy_debug", f"  Strategy ID (din template): {id_strategie_din_template}")
                log("strategy_debug", f"  Strategy ID (primit din Tab 5): None")
                log("strategy_debug", f"  ⚠️  Folosesc strategy_id={id_strategie} din template (fallback)")
            
            log("strategy_debug", f"  Axe în Wave 1: {len(wave1_axes)} axe")
            log("strategy_debug", f"  Lista axe: {wave1_axes}")
            
            # 2. Încărcăm Parametrii Strategiei
            log("strategy_debug", f"\n🎯 ÎNCĂRCARE STRATEGIE (ID={id_strategie})")
            if id_strategie:
                cursor.execute("""
                    SELECT name, w1_base_qty, yellow_extra_qty, red_extra_qty, 
                           dev_threshold_minor, dev_threshold_major, monster_trigger_timing 
                    FROM exam_strategies WHERE id=?
                """, (id_strategie,))
                rs = cursor.fetchone()
                if rs:
                    strategy_name = rs[0]
                    self.strat_w1_qty, self.strat_yellow_qty, self.strat_red_qty = rs[1], rs[2], rs[3]
                    self.strat_dev_minor_threshold, self.strat_dev_major_threshold = rs[4], rs[5]
                    self.strat_monster_timing = rs[6]
                    
                    log("strategy_debug", f"  ✅ Strategie găsită: '{strategy_name}'")
                    log("strategy_debug", f"  📊 PARAMETRI STRATEGIEI:")
                    log("strategy_debug", f"     Wave 1 întrebări per axă: {self.strat_w1_qty}")
                    log("strategy_debug", f"     Galben (extra întrebări): {self.strat_yellow_qty}")
                    log("strategy_debug", f"     Roșu (extra întrebări): {self.strat_red_qty}")
                    log("strategy_debug", f"     Threshold minor (galben): {self.strat_dev_minor_threshold}%")
                    log("strategy_debug", f"     Threshold major (roșu): {self.strat_dev_major_threshold}%")
                    log("strategy_debug", f"     Monster timing: {self.strat_monster_timing}")
                else:
                    log("strategy_debug", f"  ⚠️  Strategy ID {id_strategie} nu găsit în DB!")
                    log("strategy_debug", f"  🔄 Folosesc parametri DEFAULT")
                    self._set_default_strategy_params()
            else:
                log("strategy_debug", f"  ⚠️  Nicio strategie specificată")
                log("strategy_debug", f"  🔄 Folosesc parametri DEFAULT")
                self._set_default_strategy_params()

            # 3. Regulă Recurență (Tab 7)
            from logic.settings_manager import SettingsManager
            settings = SettingsManager.load_settings()
            val_t = settings.get("question_recurrence_value", 6)
            unit_t = settings.get("question_recurrence_unit", "Luni")
            days_map = {"Zile": 1, "Săptămâni": 7, "Luni": 30, "Ani": 365}
            self.cutoff_date = datetime.now() - timedelta(days=val_t * days_map.get(unit_t, 30))

            # 4. Creăm Sesiunea
            # MIGRARE: Verificăm dacă există coloana strategy_id
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [col[1] for col in cursor.fetchall()]
            if "strategy_id" not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN strategy_id INTEGER")
                conn.commit()
                print("✅ DB Migration: Adăugat strategy_id în sessions")
            
            cursor.execute("INSERT INTO sessions (patient_id, template_id, strategy_id, status) VALUES (?, ?, ?, 'In Progress')", 
                          (patient_id, template_id, self.strategy_id))
            self.session_id = cursor.lastrowid
            conn.commit()

            # 5. Construim coada Wave 1
            log("strategy_debug", f"\n🌊 CONSTRUIRE COADĂ WAVE 1")
            log("strategy_debug", f"  Planificare: {len(wave1_axes)} axe × {self.strat_w1_qty} întrebări = {len(wave1_axes) * self.strat_w1_qty} întrebări TOTAL (maxim)")
            
            self.queue = []
            for idx, id_axa in enumerate(wave1_axes):
                log("strategy_debug", f"  [{idx+1}/{len(wave1_axes)}] Procesez axa ID {id_axa}...")
                # Folosim noua logica de fetch (GHOST/LIVE)
                self._fetch_and_process_logic(cursor, id_axa, wave_target=1, limit=self.strat_w1_qty)
            
            log("strategy_debug", f"\n✅ COADĂ FINALIZATĂ")
            log("strategy_debug", f"  Total întrebări LIVE în coadă: {len(self.queue)}")
            log("strategy_debug", "═══════════════════════════════════════════════════════════════")
            
            # Salvăm progresul pentru UI (pauză/reluare)
            self.total_questions_planned = len(self.queue)
            self.questions_answered = 0
            
            print(f"\033[94m[ENGINE] Coadă W1 pregătită: {len(self.queue)} itemi LIVE.\033[0m")
            return True, "Sesiune începută."
        except Exception as e:
            log_error("Start Session Error", e)
            return False, str(e)
        finally:
            conn.close()

    def save_session_state(self):
        """Salvează starea curentă a sesiunii pentru reluare ulterioară."""
        from logger import log
        
        if not self.session_id:
            log_error("Salvare stare", "Nicio sesiune activă")
            return False
        
        try:
            log("strategy_debug", "💾 SALVARE PAUZĂ")
            log("strategy_debug", f"  Session {self.session_id}: {len(self.queue)} întrebări rămase")
            if self.current_question:
                log("strategy_debug", f"  Întrebare CURENTĂ (afișată): ID {self.current_question.get('id')}")
            
            # Construim starea completă
            state = {
                "patient_id": self.patient_id,
                "template_id": self.template_id,
                "strategy_id": self.strategy_id,
                "queue": self.queue,
                "current_question": self.current_question,
                "answers_log": self.answers_log,
                "asked_hashes": list(self.asked_hashes),
                "triggered_monsters": list(self.triggered_monsters),
                "wave_2_planned": self.wave_2_planned,
                "wave_3_planned": self.wave_3_planned,
                "cutoff_date": self.cutoff_date.isoformat() if self.cutoff_date else None,
                # Progres pentru UI
                "total_questions_planned": self.total_questions_planned,
                "questions_answered": self.questions_answered,
                # Parametri strategiei
                "strat_w1_qty": getattr(self, 'strat_w1_qty', 3),
                "strat_yellow_qty": getattr(self, 'strat_yellow_qty', 3),
                "strat_red_qty": getattr(self, 'strat_red_qty', 7),
                "strat_dev_minor_threshold": getattr(self, 'strat_dev_minor_threshold', 20.0),
                "strat_dev_major_threshold": getattr(self, 'strat_dev_major_threshold', 30.0),
                "strat_monster_timing": getattr(self, 'strat_monster_timing', "Dupa Val 2 (Stabilizare)")
            }
            
            state_json = json.dumps(state)
            
            conn = self.get_connection()
            try:
                c = conn.cursor()
                
                # MIGRARE: Verificăm dacă există coloana session_state
                c.execute("PRAGMA table_info(sessions)")
                columns = [col[1] for col in c.fetchall()]
                if "session_state" not in columns:
                    c.execute("ALTER TABLE sessions ADD COLUMN session_state TEXT")
                    conn.commit()
                
                c.execute("""
                    UPDATE sessions 
                    SET session_state = ?, status = 'Paused'
                    WHERE id = ?
                """, (state_json, self.session_id))
                
                conn.commit()
                log("strategy_debug", "  ✅ Stare salvată!")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            log_error("Eroare salvare stare sesiune", e)
            return False

    def load_session_state(self, session_id):
        """Încarcă o sesiune salvată și restaurează starea exactă."""
        from logger import log
        from datetime import datetime
        
        try:
            log("strategy_debug", f"📂 RELUARE sesiune {session_id}")
            
            conn = self.get_connection()
            try:
                c = conn.cursor()
                
                c.execute("""
                    SELECT session_state, status, patient_id, template_id, strategy_id
                    FROM sessions 
                    WHERE id = ?
                """, (session_id,))
                
                row = c.fetchone()
                if not row:
                    return False, "Sesiune negăsită"
                
                state_json, status, patient_id, template_id, strategy_id = row
                
                if not state_json:
                    return False, "Sesiune fără stare salvată"
                
                # Restaurăm starea
                state = json.loads(state_json)
                
                self.session_id = session_id
                self.patient_id = state["patient_id"]
                self.template_id = state["template_id"]
                self.strategy_id = state.get("strategy_id")
                self.queue = state["queue"]
                self.current_question = state.get("current_question")
                self.answers_log = {int(k): v for k, v in state["answers_log"].items()}
                self.asked_hashes = set(state["asked_hashes"])
                self.triggered_monsters = set(state["triggered_monsters"])
                self.wave_2_planned = state.get("wave_2_planned", False)
                self.wave_3_planned = state.get("wave_3_planned", False)
                self.cutoff_date = datetime.fromisoformat(state["cutoff_date"]) if state.get("cutoff_date") else None
                
                # Progres pentru UI
                self.total_questions_planned = state.get("total_questions_planned", len(self.queue))
                self.questions_answered = state.get("questions_answered", 0)
                
                # Parametri strategiei
                self.strat_w1_qty = state.get("strat_w1_qty", 3)
                self.strat_yellow_qty = state.get("strat_yellow_qty", 3)
                self.strat_red_qty = state.get("strat_red_qty", 7)
                self.strat_dev_minor_threshold = state.get("strat_dev_minor_threshold", 20.0)
                self.strat_dev_major_threshold = state.get("strat_dev_major_threshold", 30.0)
                self.strat_monster_timing = state.get("strat_monster_timing", "Dupa Val 2 (Stabilizare)")
                
                # Schimbăm status înapoi în 'In Progress'
                c.execute("UPDATE sessions SET status = 'In Progress' WHERE id = ?", (session_id,))
                conn.commit()
                
                log("strategy_debug", f"  ✅ Restaurat: {len(self.queue)} întrebări în coadă")
                if self.current_question:
                    log("strategy_debug", f"  ⚠️  Întrebare CURENTĂ: ID {self.current_question.get('id')} (va fi afișată)")
                
                return True, "Sesiune restaurată cu succes"
                
            finally:
                conn.close()
                
        except Exception as e:
            log_error("Eroare încărcare stare sesiune", e)
            return False, str(e)

    def _set_default_strategy_params(self):
        self.strat_w1_qty, self.strat_yellow_qty, self.strat_red_qty = 3, 3, 7
        self.strat_dev_minor_threshold, self.strat_dev_major_threshold = 20.0, 30.0
        self.strat_monster_timing = "Dupa Val 2 (Stabilizare)"

    def _fetch_and_process_logic(self, cursor, axis_id, wave_target, limit):
        """Aduce întrebări. Dacă găsește răspunsuri în istoric (GHOST), le procesează imediat în fundal."""
        from logger import log
        
        log("strategy_debug", f"    🔍 Axa {axis_id}: Caut {limit} întrebări (wave_target={wave_target})...")
        
        hashes_str = "('" + "','".join(self.asked_hashes) + "')" if self.asked_hashes else "('')"
        cursor.execute(f"""
            SELECT id, text_content, version_hash, wave_target 
            FROM questions_bank 
            WHERE axis_id=? AND is_active=1 AND version_hash NOT IN {hashes_str}
            ORDER BY wave_target ASC LIMIT ?
        """, (axis_id, limit))
        candidates = cursor.fetchall()
        
        log("strategy_debug", f"    📦 Găsite {len(candidates)} întrebări candidate")
        
        ghosts_count = 0
        live_count = 0
        
        for q_id, q_text, v_hash, w_prio in candidates:
            cursor.execute("""
                SELECT sr.score_snapshot, s.date_taken, s.id
                FROM session_responses sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE s.patient_id = ? AND sr.question_hash = ? AND s.date_taken > ?
                ORDER BY s.date_taken DESC LIMIT 1
            """, (self.patient_id, v_hash, self.cutoff_date.strftime("%Y-%m-%d %H:%M:%S")))
            past = cursor.fetchone()
            
            if past:
                score, date_str, old_sid = past
                if axis_id not in self.answers_log: self.answers_log[axis_id] = []
                self.answers_log[axis_id].append(score)
                self.asked_hashes.add(v_hash)
                ghosts_count += 1
                print(f"\033[92m[GHOST] Axa {axis_id}: Importat item din Sesiunea {old_sid}\033[0m")
                self._log_audit_decision(axis_id, wave_target, "Smart Skip", f"Preluat din istoric (Sesiunea {old_sid})", q_text)
            else:
                self.asked_hashes.add(v_hash)
                cursor.execute("SELECT option_index, text_content, score_value FROM question_options WHERE question_hash=? ORDER BY option_index", (v_hash,))
                self.queue.append({
                    "id": q_id, "axis_id": axis_id, "text": q_text, "hash": v_hash, 
                    "priority": w_prio, "wave": wave_target, "options": cursor.fetchall()
                })
                live_count += 1
        
        log("strategy_debug", f"    ✅ Rezultat: {ghosts_count} GHOST (din istoric) + {live_count} LIVE (în coadă)")

    def submit_answer(self, option_index, score_value, answer_text):
        """Salvează răspunsul fără a declanșa rigoarea. Valul se termină natural."""
        from logger import log
        
        if not self.current_question: return
        q = self.current_question
        
        log("strategy_debug", f"\n💾 SALVARE RĂSPUNS pentru întrebarea ID {q.get('id')}")
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("INSERT INTO session_responses (session_id, question_hash, axis_id, answer_chosen, score_snapshot) VALUES (?,?,?,?,?)",
                      (self.session_id, q['hash'], q['axis_id'], option_index, score_value))
            conn.commit()
            log("strategy_debug", f"  ✅ Răspuns salvat în DB")
        finally:
            conn.close()

        if q['axis_id'] not in self.answers_log: self.answers_log[q['axis_id']] = []
        self.answers_log[q['axis_id']].append(score_value)
        
        # Incrementăm progresul
        self.questions_answered += 1
        
        # IMPORTANT: Golim current_question după răspuns
        self.current_question = None
        log("strategy_debug", f"  ✅ Progres: {self.questions_answered}/{self.total_questions_planned}")
        log("strategy_debug", f"  ✅ current_question golit (gata pentru următoarea)")


    def get_next_question(self):
        """Managerul de tranziție între straturile de testare (Screening -> Clarificare -> Monștri)."""
        from logger import log
        
        # PRIORITATE: Dacă avem current_question (din reluare), returnăm pe aceea
        if self.current_question:
            log("strategy_debug", f"  ⚠️  Returnez current_question salvată: ID {self.current_question.get('id')}")
            return self.current_question
        
        if self.queue:
            self.current_question = self.queue.pop(0)
            return self.current_question

        # Tranziție către VAL 2 (Clarificare)
        if not self.wave_2_planned:
            self.wave_2_planned = True
            print(f"\033[95m[SYSTEM] >>> Val 1 terminat. Planific Valul 2 (Rigoare)...\033[0m")
            self._plan_wave_2()
            if self.queue: 
                return self.get_next_question()

        # Tranziție către VAL 3 (Monștri)
        if not self.wave_3_planned:
            self.wave_3_planned = True
            print(f"\033[95m[SYSTEM] >>> Val 2 terminat. Planific Valul 3 (Monștri)...\033[0m")
            self._check_monster_triggers()
            if self.queue:
                return self.get_next_question()

        return None

    def _plan_wave_2(self):
        """Analizează toate axele testate în W1 și injectează itemi extra unde este cazul."""
        conn = self.get_connection()
        cursor = conn.cursor()
        for aid in list(self.answers_log.keys()):
            self._analyze_axis_consistency_recursive(cursor, aid)
        conn.commit()
        conn.close()

    def _analyze_axis_consistency_recursive(self, cursor, axis_id):
        """Calculează penalizarea bazată pe logica duală (Contradicție/Abatere)."""
        scores = self.answers_log.get(axis_id, [])
        if len(scores) < 2: return
        
        avg = statistics.mean(scores)
        diff = max(scores) - min(scores)
        n_mean, n_sd = self._get_axis_norms_from_db(axis_id)
        dist = abs(avg - n_mean)

        prio_contra = self.strat_red_qty if diff >= 100 else (self.strat_yellow_qty if diff >= 66 else 0)
        prio_dev = self.strat_red_qty if dist >= self.strat_dev_major_threshold else (self.strat_yellow_qty if dist >= self.strat_dev_minor_threshold else 0)
        
        final_qty = max(prio_contra, prio_dev)
        if final_qty > 0:
            decision = "Integritate" if prio_contra >= prio_dev else "Abatere"
            expl = f"{decision}: Salt {diff} / Dist {dist:.1f}. Injectez +{final_qty}."
            self._log_audit_decision(axis_id, 2, decision, expl)
            # Fetch batch pentru Valul 2 (care poate fi si el Smart Skip-uit)
            self._fetch_and_process_logic(cursor, axis_id, wave_target=2, limit=final_qty)

    def _check_monster_triggers(self):
        """Verifică sinergiile și injectează întrebările de risc (Val 3)."""
        averages = {aid: statistics.mean(vals) for aid, vals in self.answers_log.items()}
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id, monster_axis_id, trigger_axis_id, operator, threshold FROM synergy_rules")
        rules = c.fetchall()
        
        potential = {}
        for rid, mid, tid, op, thresh in rules:
            if mid in self.triggered_monsters or tid not in averages: continue
            score = averages[tid]
            is_met = (op == ">" and score > thresh) or (op == "<" and score < thresh)
            if mid not in potential: potential[mid] = []
            potential[mid].append(is_met)

        for mid, conditions in potential.items():
            if all(conditions) and conditions:
                print(f"\033[91m[MONSTER] TREZIRE: ID {mid}.\033[0m")
                self.triggered_monsters.add(mid)
                self._fetch_and_process_logic(c, mid, wave_target=3, limit=10)
        conn.close()

    def finish_session(self):
        """Calculează rezultatele și face Lustrația Monștrilor."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE sessions SET status='Completed' WHERE id=?", (self.session_id,))
        for aid, scores in self.answers_log.items():
            avg = int(statistics.mean(scores))
            dev = statistics.stdev(scores) if len(scores) > 1 else 0
            conf = max(0, 100 - int(dev))
            c.execute("INSERT INTO session_results (session_id, axis_id, final_score, confidence) VALUES (?,?,?,?)", (self.session_id, aid, avg, conf))
            
            # CALCULEZ: Câte întrebări din această axă a răspuns în toate sesiunile
            # session_responses DEJA ARE axis_id direct!
            c.execute("""
                SELECT COUNT(*)
                FROM session_responses resp
                JOIN sessions s ON resp.session_id = s.id
                WHERE s.patient_id = ? AND resp.axis_id = ?
            """, (self.patient_id, aid))
            questions_used = c.fetchone()[0] or 0
            
            c.execute("INSERT OR REPLACE INTO holistic_knowledge (patient_id, axis_id, latest_score, confidence, last_updated_at, source_session_id, questions_used) VALUES (?,?,?,?,datetime('now'),?,?)",
                      (self.patient_id, aid, avg, conf, self.session_id, questions_used))
        conn.commit()
        conn.close()
        print(f"\033[94m[ENGINE] Sesiune finalizată.\033[0m")
        return True

    def _get_axis_norms_from_db(self, axis_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT norm_mean, norm_std_dev FROM axes WHERE id=?", (axis_id,))
        row = c.fetchone()
        conn.close()
        return (row[0] if row and row[0] is not None else 50.0, row[1] if row and row[1] is not None else 15.0)

    def _log_audit_decision(self, axis_id, wave, decision_type, explanation, q_text=None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO session_audit (session_id, axis_id, wave, decision_type, explanation, question_text) VALUES (?,?,?,?,?,?)",
                  (self.session_id, axis_id, wave, decision_type, explanation, q_text))
        conn.commit()
        conn.close()