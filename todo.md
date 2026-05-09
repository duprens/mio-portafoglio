 Cosa resta da fare (da te / dal tuo amico)
Decidere quando deployare il branch: aprire una PR refactorJo → main, oppure fare un secondo deploy su Streamlit Cloud che punta direttamente a refactorJo per A/B test.
Su Streamlit Cloud: aggiungere ENCRYPTION_KEY nel pannello Secrets dell'app prima di accendere il branch nuovo (altrimenti l'app si rifiuta di partire).
Backup della chiave in un password manager: se la perdi, gli utenti migrati restano fuori.
