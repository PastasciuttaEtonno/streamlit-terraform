import streamlit as st
import sys
import os

# Fix path per importare i moduli core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- INIT ---
initialize_session_state()
render_auth_sidebar()

config = st.session_state.project_config

if config.provider != "aws":
    st.header("5. Relational Database")
    st.warning("Il modulo Database (Cloud SQL) non è ancora disponibile per GCP in questa versione.")
    st.stop()

# --- HEADER ---
st.header("5. Relational Database (RDS) - AWS")
st.info("Configura un database gestito sicuro e persistente (Amazon RDS).")

with st.expander("ℹ️ Info Costi & Architettura (Leggi qui se vuoi risparmiare)", expanded=False):
    st.markdown("""
    **Differenza tra '2 Subnet' e 'Multi-AZ Instance':**
    - **AWS richiede** che il "Gruppo di Subnet" copra 2 Zone per motivi di ridondanza teorica. Questo è un requisito di rete **GRATUITO**.
    - **Noi creeremo** un database **Single-AZ** (non ridondato) per mantenere i costi bassi (costo x1).
    - Quindi: **Avere 2 AZ nella rete NON significa pagare doppio il database.**
    
    **Alternativa a costo zero (Docker):**
    Se preferisci non usare RDS e gestire il DB a mano dentro la EC2 (come XAMPP/Docker), vai alla pagina **3. Compute** e attiva "Deploy Docker".
    """)

# Recupero configurazioni
rds_config = config.rds
net_config = config.network

# --- ARCHITECTURE CHECK ---
# RDS richiede:
# 1. Almeno 2 Availability Zones (per coprire le requirements del DB Subnet Group)
# 2. Almeno 2 Subnet Private (una per AZ)
if net_config.az_count < 2 or net_config.private_subnet_count < 2:
    st.error("🛑 **Errore Architetturale**: Requisiti RDS non soddisfatti.")
    st.markdown(
        """
        Amazon RDS richiede che il **DB Subnet Group** copra almeno **2 Availability Zones**.
        
        **Configurazione Attuale:**
        - Availability Zones: **{az}** (Richiesto: >= 2)
        - Subnet Private: **{sub}** (Richiesto: >= 2)
        
        **Azione Richiesta:**
        È necessario abilitare almeno 2 AZ e 2 Subnet Private.
        Questo cambiamento è **GRATUITO** (nessun costo aggiuntivo per le subnet).
        """
    )
    
    col_err, col_fix = st.columns([3, 1])
    with col_err:
        st.warning("⚠️ Configurazione di rete non sufficiente per RDS.")
    with col_fix:
        if st.button("🔄 Correggi (Gratis)", type="primary", help="Imposta AZ=2 e Private Subnets=2 automaticamente"):
            st.session_state.project_config.network.az_count = 2
            # Assicuriamoci che ci siano almeno 2 subnet private
            if st.session_state.project_config.network.private_subnet_count < 2:
                st.session_state.project_config.network.private_subnet_count = 2
            
            # Se mancano subnet pubbliche per bilanciare (facoltativo ma consigliato), ne mettiamo 2
            if st.session_state.project_config.network.public_subnet_count < 2:
                st.session_state.project_config.network.public_subnet_count = 2
                
            st.rerun()

    st.stop() # Blocchiamo comunque finché l'utente non clicca Fix


# 1. Main Toggle (Aggiorna la pagina istantaneamente)
is_enabled = st.checkbox("Abilita Database RDS", value=rds_config.enabled)

st.divider()

# 2. Configurazione Hardware & Engine
c1, c2 = st.columns(2)
with c1:
    identifier = st.text_input("ID Database (Identificativo AWS)", value=rds_config.identifier, disabled=not is_enabled)
    # Logica per l'indice del selectbox
    engine_index = 0 if rds_config.engine == "mysql" else 1
    engine = st.selectbox("Motore Database", ["mysql", "postgres"], index=engine_index, disabled=not is_enabled)

with c2:
    # Opzioni limitate per il Free Tier o Low Cost
    instance_class = st.selectbox(
        "Classe Istanza (CPU/RAM)", 
        ["db.t3.micro", "db.t3.small", "db.t4g.micro"], 
        index=0, 
        disabled=not is_enabled,
        help="t3.micro è idonea per il Free Tier AWS"
    )
    storage = st.number_input("Storage Allocato (GB)", value=rds_config.allocated_storage, min_value=20, max_value=100, disabled=not is_enabled)

st.divider()

# 3. Credenziali & Sicurezza
st.markdown("#### 🔐 Credenziali & Sicurezza")
st.caption("Il database sarà posizionato nelle Subnet Private e accetterà connessioni **SOLO** dalle istanze EC2 (Security Group Chaining).")

c3, c4, c5 = st.columns(3)
with c3:
    db_name = st.text_input("Nome DB Iniziale (Schema)", value=rds_config.db_name, disabled=not is_enabled)
with c4:
    username = st.text_input("Master Username", value=rds_config.username, disabled=not is_enabled)
with c5:
    password = st.text_input("Master Password", value=rds_config.password, type="password", disabled=not is_enabled)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Bottone di Salvataggio (Normale button)
if st.button("Salva Configurazione DB", type="primary", disabled=not is_enabled and not rds_config.enabled):
    
    # Aggiornamento dello Stato Globale
    st.session_state.project_config.rds.enabled = is_enabled
    st.session_state.project_config.rds.identifier = identifier
    st.session_state.project_config.rds.engine = engine
    st.session_state.project_config.rds.instance_class = instance_class
    st.session_state.project_config.rds.allocated_storage = storage
    st.session_state.project_config.rds.db_name = db_name
    st.session_state.project_config.rds.username = username
    st.session_state.project_config.rds.password = password
    
    st.toast("Configurazione Database salvata!", icon="💾")
    st.success("Configurazione aggiornata correttamente.")

# Se l'utente disabilita il checkbox e salva, aggiorniamo lo stato a Disabled
if not is_enabled and rds_config.enabled:
    if st.button("Disabilita e Salva"):
        st.session_state.project_config.rds.enabled = False
        st.rerun()