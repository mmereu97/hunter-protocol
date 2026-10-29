# Baza de date — construire și întreținere

Cea mai confuză parte a proiectului: în `database/` sunt **~120 de scripturi** care
arată similar. Acest document explică ce sunt, în ce ordine se rulează și cum se
reconstruiește baza de la zero.

## Regula de bază

**Toate scripturile `.py` din `database/` sunt unelte de construcție rulate o
singură dată.** Scriu date în `hunter_protocol.db` și apoi nu mai sunt necesare la
runtime. Aplicația citește doar fișierul `.db` finit.

Dacă ai deja un `hunter_protocol.db` funcțional, **nu trebuie să rulezi nimic** din
folderul `database/`. Scripturile contează doar când vrei să reconstruiești sau să
modifici conținutul bazei.

## Unde stă baza de date

- `database/knowledge_base.db` (în repo): baza de cunoștințe publică: axe, întrebări,
  reguli de sinergie, strategii și șabloane. **Fără pacienți, sesiuni sau rapoarte.**
- `../Data/hunter_protocol.db` (în afara repo-ului): baza de lucru, cu datele personale.
  Dacă lipsește, aplicația o creează copiind `knowledge_base.db`.

Scripturile de mai jos scriu în baza de lucru (`Config.DB_NAME`). Rulează-le pe o copie.

## Categorii de scripturi

### 1. Schema — `init_db.py`
Creează structura bazei (tabele: `questions_bank`, `question_options`, axe, reguli
etc.). **Rulat primul.**

### 2. Buildere de axe — `db_builder_NN.py` (~109 fișiere)
Fiecare populează întrebările pentru o singură axă psihometrică. `AXIS_ID` din
header spune care (ex: `AXIS_ID = 1 # Sinceritate`, `AXIS_ID = 52 # Narcisism`).

La curățenie au fost **unificate într-un singur folder**: `database/builders/`.
Înainte erau sparte fără motiv tehnic în `database/01-110/` (81 fișiere) și
`database/monsters/` (28 fișiere) — numele „monsters" inducea în eroare, conținea
buildere de axe obișnuite, nu reguli de sinergie.

Împreună acoperă **axele 1–110** (lipsește 51, probabil populat altundeva).

> Toate sunt clone ale lui `_template_builder.py` (acum tot în `database/builders/`),
> șablonul cu zona de configurare „modifică doar aici". Fiecare șterge versiunile
> vechi ale axei sale și inserează versiunile noi, deci pot fi rerulate fără să
> dubleze datele.

> ⚠️ Atenție dacă vrei să le **rerulezi**: builderele au logică de cale inconsistentă
> (unele folosesc `Config.DB_NAME`, altele un nume relativ `"hunter_protocol.db"`).
> Mutarea în `builders/` nu a schimbat asta — adâncimea față de rădăcină a rămas
> identică. Dar dacă reconstruiești baza, rulează-le din rădăcina proiectului și
> verifică pe o copie.

### 3. Migrări / seed numerotate
Se rulează în ordinea numărului:

- `01_populate_axes.py` — populează definițiile axelor
- `03_update_norms.py` — actualizează normele
- `04_populate_rules.py` / `04_populate_rules_full.py` — reguli (versiunea `_full` o
  înlocuiește probabil pe prima; vezi nota de mai jos)
- `06_add_clinical_pack.py` — pachet clinic
- `07_add_bipolar.py` — adaugă axa bipolară
- `08_add_missing_axes.py` — completează axe lipsă
- `09_fix_db.py` — fix
- `10_fix_audit.py` — fix audit

### 4. Injectoare de descrieri — `inject_desc_*.py` (7 fișiere)
Adaugă texte descriptive pe game de axe: `02`, `03-10`, `11-30`, `31-50`, `51-70`,
`71-90`, `91-110`.

## Ordinea de reconstruire (de la zero)

```
1. init_db.py                     # schema
2. 01_populate_axes.py            # definițiile axelor
3. db_builder_*.py (toate)        # întrebările pe axe 1–110 (în database/builders/)
4. 03_update_norms.py
5. 04_populate_rules_full.py      # reguli
6. 06_add_clinical_pack.py
7. 07_add_bipolar.py
8. 08_add_missing_axes.py
9. inject_desc_*.py (toate)       # descrieri
10. 09_fix_db.py / 10_fix_audit.py  # fix-uri finale
```

> Ordinea de mai sus este **dedusă** din numerotare și din ce face fiecare script,
> nu confirmată printr-o rulare. Înainte să te bazezi pe ea pentru o reconstrucție
> reală, verific-o pe o copie a bazei.

## De clarificat

- `04_populate_rules.py` vs `04_populate_rules_full.py` — care e cel valid? Dacă
  `_full` îl înlocuiește, primul e candidat de ștergere.
- Axa 51 — de ce lipsește din buildere? E populată de alt script sau a fost omisă?
