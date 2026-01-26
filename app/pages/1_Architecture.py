import streamlit as st

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar
render_auth_sidebar()
initialize_session_state()

st.header("1. Definizione Architettura")

# Recuperiamo la config dallo stato
# (Usiamo una variabile locale per comodità, ma punta allo stesso oggetto in memoria)
config = st.session_state.project_config

st.info("In questa sezione definiamo i metadati globali del progetto.")

# --- FORM ---
with st.form("arch_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        new_name = st.text_input(
            "Nome Progetto", 
            value=config.project_name,
            help="Questo nome verrà usato come prefisso per tutte le risorse"
        )
        
    with col2:
        new_region = st.selectbox(
            "Regione AWS",
            options=["us-east-1", "eu-west-1", "eu-central-1"],
            index=0 if config.region == "us-east-1" else 1 # Semplificazione per l'index
        )
        
    submitted = st.form_submit_button("Salva e Prosegui",type="primary")
    
    if submitted:
        # Aggiorniamo lo stato
        st.session_state.project_config.project_name = new_name
        st.session_state.project_config.region = new_region
        
        st.success(f"✅ Progetto '{new_name}' impostato su {new_region}!")
        st.toast("Dati salvati!", icon="💾")