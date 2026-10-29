# Hunter Protocol v3 — Arhitectură

Hartă a proiectului pentru cineva care revine după o pauză. Răspunde la întrebarea:
*„Ce face fiecare fișier și de ce am nevoie ca să pornesc aplicația?"*

## Ce este aplicația

Aplicație desktop (Python + PySide6) pentru evaluare psihometrică. Datele
(întrebări, axe, reguli) stau într-o bază SQLite. Există și agenți AI (Google
Gemini) pentru generare de rapoarte și asistență la construirea testelor.

## Punctul de pornire

```
main.py  →  config.py (validează .env + calea DB)  →  ui/main_window.py
```

`main.py` pornește aplicația Qt, aplică stilul global (temă „cyberpunk" întunecată)
și deschide fereastra principală. Fereastra principală încarcă tab-urile din `ui/`.

## Ce are nevoie aplicația ca să ruleze (runtime)

Acestea sunt fișierele de care depinde aplicația când pornește. **Doar acestea.**

| Componentă | Rol |
| --- | --- |
| `main.py` | Punct de intrare, stil global Qt |
| `config.py` | Citește `.env`, definește calea bazei de date și a prompturilor |
| `logger.py` | Logging |
| `ai_agents/` | 3 fișiere: conector LLM + agenți (architect, profiler) |
| `logic/` | 7 „manageri" — logica de business (vezi mai jos) |
| `ui/` | Fereastra principală + 8 tab-uri |
| `prompts/` | 6 fișiere `.txt` cu prompturi, încărcate la runtime via `PROMPTS_DIR` |
| `../Data/hunter_protocol.db` | Baza de date de lucru (în afara repo-ului; creată la prima pornire din `database/knowledge_base.db`) |
| `requirements.txt` | Dependențe pip |

### Modulul `logic/` (logica de business)

Fiecare manager deschide singur conexiunea la `Config.DB_NAME`:

- `exam_engine.py` — motorul de examinare (cel mai mare, ~26 KB); fluxul de întrebări Wave 1/2/3
- `patient_manager.py` — gestiune pacienți
- `knowledge_manager.py` — baza de cunoștințe (axe, întrebări)
- `architect_manager.py` — construirea de teste/șabloane
- `strategy_manager.py` — strategii de testare și scoring
- `synergy_manager.py` — reguli încrucișate între axe („Monsters")
- `settings_manager.py` — setări persistente

### Modulul `ui/` (interfața)

`main_window.py` adună 8 tab-uri:

`tab_patients` · `tab_knowledge` · `tab_architect` · `tab_strategies` ·
`tab_synergy` · `tab_exam` · `tab_results` · `tab_settings`

> Notă de mărime: `tab_results.py` (~81 KB) și `tab_patients.py` (~61 KB) sunt cele
> mai mari fișiere din proiect. Nu e o problemă în sine, dar dacă vrei vreodată să
> spargi ceva în fișiere mai mici, de aici ai începe.

## Ce NU are nevoie aplicația ca să ruleze

Folderul `database/` conține, pe lângă fișierul `.db`, **scripturi Python care se
rulează o singură dată** ca să *construiască* baza de date (migrările numerotate și
injectoarele de descrieri la rădăcina lui `database/`, plus cele ~110 buildere de axe
unificate în `database/builders/`). După ce baza e construită, aplicația nu le mai
atinge. Detalii complete în `BAZA_DE_DATE.md`.

Pe scurt: **codul aplicației nu importă niciodată un `db_builder`, un `inject_desc`
sau un `populate`.** Sunt unelte de construcție, nu cod de runtime.

## Unelte separate

- `standalone_exam.py` (rădăcină) — examinator independent care rulează pe un
  `exam_package.db` exportat din aplicație. **Nu** e importat de aplicație; e o unealtă
  de sine stătătoare. E menționat doar într-un mesaj către utilizator în `tab_exam.py`.

## Configurare necesară

Datele personale stau în folderul `Data/` de **lângă** `Project/`, nu în repo:

```
<rădăcină>/
├── Project/   codul (GitHub)
└── Data/      hunter_protocol.db, pacienti/, user_settings.json, .env
```

1. `Data/.env` cu `GOOGLE_API_KEY="..."` (pentru funcțiile Gemini; opțional).
2. Baza de date: dacă `Data/hunter_protocol.db` lipsește, aplicația o creează din
   `database/knowledge_base.db` (110 axe, 1.101 întrebări, 74 de reguli, fără date personale).

```bash
pip install -r requirements.txt
python main.py
```
