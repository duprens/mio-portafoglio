# mio-portafoglio

App Streamlit di monitoraggio portafogli per consulenti finanziari. 

## Architettura Dati

- **Rubrica** (Google Sheets centrale): Directory degli utenti.
    - Colonne: `Email | LinkEnc | PasswordHash`.
    - `LinkEnc`: URL del foglio personale, cifrato con Fernet.
    - `PasswordHash`: Hash bcrypt della password, cifrato con Fernet.
- **Foglio Privato**: Database personale di ogni consulente.
    - Worksheet `Portafogli`: Contiene le posizioni dei clienti (Cliente, Data_Inizio, Strumento, Ticker, Quantità, PMC, Asset, Area, Valuta).
- **Relazione**: 1 Utente = 1 Consulente = 1 Foglio Google = N Clienti = N Posizioni.

## Layout dei Moduli

| File | Responsabilità |
|---|---|
| `app.py` | Orchestratore: sidebar, dashboard, planner. Gestisce il flusso principale di Streamlit. |
| `auth.py` | UI Login e Registrazione, gestione sessione (timeout 30 min), funzione `gate()`. |
| `data.py` | I/O Google Sheets (Rubrica, Portafogli) e integrazione `yfinance`. |
| `security.py` | Logica di sicurezza: bcrypt (cost 12), Fernet (cifratura simmetrica), validazione regex. |
| `charts.py` | Generazione grafici Plotly (candele, torte, planner). |
| `styles.py` | Configurazione pagina e CSS personalizzato. |

## Standard di Sicurezza

1. **Password**: Hashing con bcrypt (costo 12).
2. **Cifratura**: Dati sensibili in Rubrica (`Link`, `PasswordHash`) cifrati con Fernet.
3. **Validazione**: Controllo rigoroso di email e link Google Sheets.
4. **Sessioni**: Timeout di 30 minuti gestito in `auth.py`.

## Convenzioni di Sviluppo

- **Patch Chirurgiche**: Evitare refactoring massivi non necessari.
- **Sicurezza Prioritaria**: Ogni nuova feature deve essere analizzata sotto il profilo della sicurezza dei dati finanziari.
- **Naming**: Mantenere il mix Italiano/Inglese esistente. 
    - Italiano nei nomi legati al dominio business (`salva_db_privato`, `clienti_database`).
    - Inglese per i moduli tecnici (`security`, `data`, `auth`).
- **Streamlit Re-run**: Ricordare che Streamlit riesegue l'intero script ad ogni interazione. Utilizzare `st.session_state` per persistere i dati tra i re-run.

## Setup Locale

- **Python**: Utilizzare un virtual environment (`.venv`).
- **Secrets**: Richiede `.streamlit/secrets.toml` con `ENCRYPTION_KEY` (Fernet key a 44 caratteri). **MAI** committare questo file.
- **Dipendenze**: Gestite tramite `requirements.txt`.
