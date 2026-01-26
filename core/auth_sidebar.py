import streamlit as st
import os

def clear_credentials():
    """Callback che rimuove le credenziali dalla memoria."""
    keys_to_remove = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for key in keys_to_remove:
        if key in os.environ:
            del os.environ[key]
    
    # Opzionale: Puliamo anche eventuali stati di sessione se li usiamo
    # st.session_state.pop('manual_auth', None)

def render_auth_sidebar():
    """
    Gestisce l'input delle credenziali AWS nella sidebar.
    """
    st.sidebar.subheader("🔐 AWS Authentication")

    # Leggiamo le variabili attuali
    has_key = os.getenv("AWS_ACCESS_KEY_ID")
    has_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Controlliamo se esiste un file .env fisico (per dare un warning all'utente)
    # Assumiamo che il .env sia nella root (due livelli sopra questo file)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
    has_env_file = os.path.exists(env_path)

    if has_key and has_secret:
        # --- STATO: LOGGATO ---
        masked_key = f"*****{has_key[-4:]}" if len(has_key) > 4 else "****"
        
        # Mostriamo un'icona diversa se è da file o manuale
        if has_env_file:
            st.sidebar.success(f"Loggato via .env:\n`{masked_key}`")
            st.sidebar.caption("⚠️ Le credenziali sono nel file `.env`. Il logout le rimuove solo temporaneamente finché non ricarichi la pagina.")
        else:
            st.sidebar.success(f"Loggato Manualmente:\n`{masked_key}`")

        # Bottone LOGOUT con Callback
        # L'uso di on_click garantisce che l'azione avvenga PRIMA del rerun
        st.sidebar.button("Logout / Cambia", on_click=clear_credentials, type="primary")

    else:
        # --- STATO: NON LOGGATO ---
        st.sidebar.warning("Nessuna credenziale attiva.")
        
        with st.sidebar.expander("🔑 Inserisci Credenziali", expanded=True):
            with st.form("aws_auth_form"):
                access_key = st.text_input("Access Key ID")
                secret_key = st.text_input("Secret Access Key", type="password")
                region = st.selectbox("Region", ["us-east-1", "eu-west-1", "eu-central-1"], index=0)
                
                submitted = st.form_submit_button("Salva Credenziali", type="primary")
                
                if submitted:
                    if access_key and secret_key:
                        os.environ["AWS_ACCESS_KEY_ID"] = access_key
                        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
                        os.environ["AWS_REGION"] = region
                        st.rerun()
                    else:
                        st.sidebar.error("Compila tutti i campi")