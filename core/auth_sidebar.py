import streamlit as st
import os
import tempfile
import json

def clear_credentials():
    """Callback che rimuove le credenziali dalla memoria."""
    # AWS
    keys_to_remove = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for key in keys_to_remove:
        if key in os.environ:
            del os.environ[key]
    
    # GCP
    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        gcp_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        # Opzionale: cancellare il file temporaneo se creato da noi
        # In questo esempio semplice lo lasciamo, ma rimuoviamo l'ENV.
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

def render_auth_sidebar():
    """
    Gestisce l'input delle credenziali nella sidebar in base al Provider selezionato.
    """
    # Recuperiamo il provider dallo stato (default AWS)
    if "project_config" in st.session_state:
        current_provider = st.session_state.project_config.provider
    else:
        current_provider = "aws" # Fallback

    st.sidebar.subheader(f"🔐 {current_provider.upper()} Authentication")

    if current_provider == "aws":
        _render_aws_auth()
    elif current_provider == "gcp":
        _render_gcp_auth()

def _render_aws_auth():
    # Leggiamo le variabili attuali
    has_key = os.getenv("AWS_ACCESS_KEY_ID")
    has_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # Controlliamo se esiste un file .env fisico
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
    has_env_file = os.path.exists(env_path)

    if has_key and has_secret:
        # --- STATO: LOGGATO ---
        masked_key = f"*****{has_key[-4:]}" if len(has_key) > 4 else "****"
        
        if has_env_file:
            st.sidebar.success(f"Loggato via .env:\n`{masked_key}`")
            st.sidebar.caption("⚠️ Credenziali da file `.env`.")
        else:
            st.sidebar.success(f"Loggato Manualmente:\n`{masked_key}`")

        st.sidebar.button("Logout AWS", on_click=clear_credentials, type="primary")

    else:
        # --- STATO: NON LOGGATO ---
        st.sidebar.warning("Nessuna credenziale AWS attiva.")
        
        with st.sidebar.expander("🔑 Inserisci Credenziali", expanded=True):
            with st.form("aws_auth_form"):
                access_key = st.text_input("Access Key ID")
                secret_key = st.text_input("Secret Access Key", type="password")
                region = st.selectbox("Region", ["us-east-1", "eu-west-1", "eu-central-1"], index=0)
                
                if st.form_submit_button("Salva AWS Keys", type="primary"):
                    if access_key and secret_key:
                        os.environ["AWS_ACCESS_KEY_ID"] = access_key
                        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
                        os.environ["AWS_REGION"] = region
                        st.rerun()
                    else:
                        st.sidebar.error("Compila tutti i campi")

def _render_gcp_auth():
    has_gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if has_gcp_creds:
        st.sidebar.success("✅ GCP Credenziali Attive")
        st.sidebar.caption(f"Path: `{os.path.basename(has_gcp_creds)}`")
        
        st.sidebar.button("Logout GCP", on_click=clear_credentials, type="primary")
        
    else:
        st.sidebar.warning("Nessuna credenziale GCP attiva.")
        st.sidebar.info("Carica il file JSON della Service Account Key.")
        
        with st.sidebar.expander("🔑 Carica Key JSON", expanded=True):
            # Opzione 1: File Upload
            uploaded_file = st.file_uploader("Upload JSON", type="json", key="gcp_key_file")
            
            # Opzione 2: Paste JSON (utile se non si ha il file a portata di mano)
            # pasted_json = st.text_area("Oppure incolla il JSON qui")
            
            if uploaded_file is not None:
                if st.sidebar.button("Salva GCP Key", type="primary"):
                    try:
                        # Salviamo il file in una cartella temp 'secrets' nel progetto
                        # per persistenza durante la sessione
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                        secrets_dir = os.path.join(base_dir, ".secrets")
                        os.makedirs(secrets_dir, exist_ok=True)
                        
                        file_path = os.path.join(secrets_dir, "gcp_key.json")
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        # Impostiamo l'ENV VAR fondamentale per Terraform/Google Provider
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = file_path
                        st.rerun()
                        
                    except Exception as e:
                        st.sidebar.error(f"Errore salvataggio: {e}")