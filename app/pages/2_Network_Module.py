import streamlit as st
import sys
import os

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- INIZIALIZZAZIONE ---
initialize_session_state()
render_auth_sidebar()

config = st.session_state.project_config

if config.provider == "aws":
    st.header("2. Configurazione Network Avanzata (AWS)")
    st.info("Configura Availability Zones e Subnetting (Simmetrico HA).")

    # Shortcut allo stato attuale
    net_config = config.network

    # --- 1. VPC CIDR ---
    st.subheader("1. Spazio di Indirizzamento")
    vpc_cidr = st.text_input(
        "VPC CIDR Block", 
        value=net_config.vpc_cidr,
        help="Es: 10.0.0.0/16"
    )

    st.divider()

    # --- 2. AVAILABILITY ZONES (AZs) ---
    # Togliendo st.form, questo widget ora triggera un RERUN immediato quando cambiato
    st.subheader("2. Availability Zones (AZs)")
    st.caption("Scegli su quante zone fisiche distribuire l'infrastruttura.")
    st.info("ℹ️ **Nota sui Costi**: Selezionare più zone crea solo le sottoreti. **Non** lancia istanze extra e **non** ha costi aggiuntivi di per sé.")

    az_options = [1, 2, 3]

    # Calcoliamo l'index per il widget
    try:
        # Cerchiamo il valore attuale (dallo stato) nelle opzioni
        default_az_idx = az_options.index(net_config.az_count)
    except ValueError:
        default_az_idx = 1 # Default a 2 AZ (index 1) se c'è un valore strano

    # Widget interattivo (fuori dal form!)
    az_count = st.radio(
        "Numero di AZs:",
        options=az_options,
        index=default_az_idx,
        horizontal=True,
        key="az_selector"
    )

    st.divider()

    # --- 3. SUBNET CALCOLATE DINAMICAMENTE ---
    # Ora che siamo fuori dal form, az_count è aggiornato INSTANTANEAMENTE
    st.subheader("3. Allocazione Subnet")

    # Logica di calcolo opzioni (Simmetria AWS)
    # Se AZ=3 -> Opzioni Public: [0, 3]
    pub_options = [0, az_count]
    priv_options = [0, az_count, az_count * 2]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Public Subnets**")
        st.caption("Accessibili da Internet")
        
        # --- LOGICA ANTI-CRASH ---
        # Se passo da AZ=1 (valore 1) a AZ=3 (opzioni 0, 3), il valore "1" non esiste più.
        # Dobbiamo correggere 'value' prima di creare il widget, altrimenti Streamlit dà errore.
        current_pub = net_config.public_subnet_count
        
        # Se il valore salvato non è valido per la nuova configurazione AZ...
        if current_pub not in pub_options:
            # ...lo adattiamo intelligentemente.
            # Se era > 0, selezioniamo il massimo disponibile (es. 3), altrimenti 0.
            safe_pub_index = 1 if current_pub > 0 else 0
        else:
            safe_pub_index = pub_options.index(current_pub)

        public_count = st.radio(
            "Quantità Public:",
            options=pub_options,
            index=safe_pub_index, # Usiamo l'indice sicuro calcolato
            horizontal=True,
            key="pub_radio"
        )

    with col2:
        st.markdown("**Private Subnets**")
        st.caption("Backend isolati")
        
        # --- LOGICA ANTI-CRASH PRIVATE ---
        current_priv = net_config.private_subnet_count
        
        if current_priv not in priv_options:
            # Logica di adattamento: cerchiamo l'opzione più vicina o sensata
            if current_priv >= (az_count * 2):
                    # Se ne avevi tante, prendi il massimo (es. 6)
                safe_priv_index = 2 
            elif current_priv > 0:
                    # Se ne avevi qualcuna, prendi la media (es. 3)
                safe_priv_index = 1
            else:
                safe_priv_index = 0
        else:
            safe_priv_index = priv_options.index(current_priv)

        private_count = st.radio(
            "Quantità Private:",
            options=priv_options,
            index=safe_priv_index,
            horizontal=True,
            key="priv_radio"
        )

    st.divider()

    # --- SAVE BUTTON ---
    # Ora è un bottone normale, non form_submit_button
    if st.button("Salva Configurazione Rete", type="primary"):
        try:
            # Aggiorniamo lo stato globale con i valori attuali dei widget
            st.session_state.project_config.network.vpc_cidr = vpc_cidr
            st.session_state.project_config.network.az_count = az_count
            st.session_state.project_config.network.public_subnet_count = public_count
            st.session_state.project_config.network.private_subnet_count = private_count
            
            st.success("Configurazione aggiornata con successo!")
            st.toast("Configurazione Rete salvata!", icon="💾")
            
            # Recap immediato
            st.info(f"""
            **Nuova Architettura:**
            🔹 {az_count} Zone (HA)
            🔹 {public_count} Subnet Pubbliche
            🔹 {private_count} Subnet Private
            """)
            
        except ValueError as e:
            st.error(f"Errore di Validazione: {e}")

elif config.provider == "gcp":
    st.header("2. Google Cloud Network")
    st.info("Configurazione VPC semplificata per GCP (Global VPC).")
    
    net_config = config.network
    
    st.subheader("VPC Subnet")
    subnet_cidr = st.text_input("Subnet CIDR", value=net_config.subnet_cidr, help="Es: 10.0.1.0/24")
    
    if st.button("Salva GCP Network", type="primary"):
        st.session_state.project_config.network.subnet_cidr = subnet_cidr
        st.success("Configurazione aggiornata!")
        st.toast("GCP Network Saved!", icon="💾")