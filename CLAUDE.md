# mio-portafoglio

App Streamlit di monitoraggio portafogli per consulenti finanziari. Repo condiviso da un amico (account GitHub `duprens`); il proprietario di questa working copy non è l'autore originale.

## Architettura dati

- **Rubrica** (foglio Google centrale, condiviso tra tutti i consulenti) = directory degli utenti app. Una riga per consulente. Colonne legacy: `Email | Link | Password`. Colonne nuove di questo branch: `Email | LinkEnc | PasswordHash` (vedi sotto).
- **Foglio "privato"** puntato dal `Link` di ogni consulente = database personale di quel consulente, contiene il worksheet `Portafogli` con tutti i suoi clienti (Cliente, Data_Inizio, Strumento, Ticker, Quantità, PMC, Asset, Area, Valuta).
- Quindi: **1 utente app = 1 consulente = 1 foglio Google = N clienti = N posizioni**.

## Branch corrente: `refactorJo` (NON `main`)

Lavoro di hardening sicurezza + refactoring modulare. Pensato per girare in **parallelo** al `main` deployato (probabilmente su Streamlit Community Cloud) — non rompere il main è un vincolo duro.

### Strategia di coabitazione sulla stessa Rubrica

Il branch `refactorJo` **non scrive mai** sulle colonne legacy `Link` / `Password`. Usa due colonne nuove:

- `LinkEnc` — URL del foglio cifrato con Fernet
- `PasswordHash` — hash bcrypt della password, a sua volta cifrato con Fernet

Quando un utente esistente sul main fa il primo login sul branch nuovo, viene messo in flusso registrazione (anche se ha già una riga in Rubrica), e popola le nuove colonne. Il main continua a leggere `Link`/`Password` come prima.

Costanti in [data.py](data.py): `LINK_COL = "LinkEnc"`, `PASS_COL = "PasswordHash"`. Se in futuro decidi di unificare (es. dopo aver migrato tutti gli utenti), parti da lì.

## Layout moduli (post-refactor)

| File | Responsabilità |
|---|---|
| [app.py](app.py) | Orchestratore: sidebar + dashboard + planner. Niente logica core. ~300 righe. |
| [security.py](security.py) | bcrypt (`hash_password`/`verify_password`), Fernet (`enc`/`dec`), regex (`is_valid_email`, `is_valid_sheets_link`, `extract_sheet_id`). |
| [styles.py](styles.py) | `set_page_config` + tutto il CSS dell'app. |
| [data.py](data.py) | I/O Google Sheets: Rubrica (`load_rubrica`, `find_user`, `get_user_password_hash`, `link_conflict`, `upsert_user`, `get_user_link`) + Portafogli (`load_portfolio`, `save_portfolio`) + yfinance (`fetch_prices`, `fetch_candele`). |
| [auth.py](auth.py) | UI login + registrazione, `gate()` che blocca finché non si è autenticati, session timeout 30 min, `logout_button()`. |
| [charts.py](charts.py) | Figure plotly: `candele_fig`, `pie_fig` (riusato per le 3 torte), `planner_fig`, helper `colora`. |

Su `main` invece tutto è in un unico `app.py` di 513 righe.

## Sicurezza — cosa è stato chiuso su `refactorJo`

1. **Password**: bcrypt cost 12 (era SHA-256 nudo, vulnerabile a hashcat).
2. **No auto-signup su errore tecnico**: prima un blip Google Sheets durante il login mandava l'utente in registrazione senza verificare nulla. Ora: errore → "Servizio non disponibile", stop.
3. **Unicità link Google Sheets**: in registrazione si rifiuta un link il cui `sheet_id` è già usato da un'altra email in Rubrica. Difesa pragmatica contro chi punta al foglio altrui.
4. **Cifratura Fernet** di `LinkEnc` e `PasswordHash`: chi legge la Rubrica non vede né URL né hash bruti.

Bonus: bottone Esci, session timeout 30 min, validazione email/link con regex, logging centralizzato (basta `except: pass`).

## Setup locale (sul Mac)

- `.venv/` con Python 3.14 di Homebrew (escluso da git via `.gitignore`)
- Dipendenze nuove installate nel venv: `bcrypt 5.0.0`, `cryptography 48.0.0`
- `.streamlit/secrets.toml` con `ENCRYPTION_KEY = "..."` (Fernet key 44 char, perms 600, **escluso da git**)
- **La chiave NON è in git**. Backup obbligatorio in password manager. Se si perde, gli utenti migrati restano fuori.

Per girare in produzione su Streamlit Community Cloud: aggiungere `ENCRYPTION_KEY` nel pannello Settings → Secrets dell'app prima di puntare il deploy a `refactorJo` (oppure prima di mergiare in `main`).

## Stack

`streamlit`, `pandas`, `plotly`, `yfinance`, `st-gsheets-connection`, `bcrypt`, `cryptography`. Versioni minime in [requirements.txt](requirements.txt) (prima erano libere → app fragile).

## Convenzioni di lavoro

- **Patch chirurgiche** per default. Niente refactoring "tanto per". Il file unico è già stato sciolto in moduli — non scioglierlo ulteriormente senza motivo.
- **Sicurezza prima**, feature dopo. Questa è un'app finanziaria.
- **Compatibilità con `main` mandatoria** finché il branch non viene mergiato. Niente scritture sulle colonne legacy della Rubrica.
- **Italiano misto** nei nomi (`salva_db_privato`, `clienti_database`) — è una scelta del codice originale, mantenerla per coerenza nei moduli condivisi con il main; nei moduli nuovi (`security`, `data`, `auth`, `charts`) si può preferire l'inglese.

## Note sull'utente

Sviluppatore **frontend senior (15+ anni)**, specializzato in **Angular** (e TypeScript/Node). Solido su frontend, componenti, routing, RxJS, build tooling. **Non** è un security engineer né un backend dev tradizionale.

- **Sicurezza / cifratura / hashing / threat modeling**: spiegare cosa fa una primitiva, cosa non fa, contro quale minaccia protegge. Non darli per scontati.
- **Backend / DB / I/O**: spiegare quando rilevante.
- **Python idiomi**: nuovo. Usa paralleli con TypeScript/Angular: `pip` ≈ `npm`, `requirements.txt` ≈ `package.json`, `venv` ≈ project-isolated `node_modules`, decoratore Python `@xxx` ≈ TS decorator tipo `@Component` (concetto familiare).
- **Streamlit**: il modello a re-run completo dello script ad ogni interazione è controintuitivo per chi viene da Angular (componenti con lifecycle persistente). Ribadirlo.
- Tono alla pari su architettura/modularità/branching/dependency management — è senior. Ma non didattico, non paternalistico.
