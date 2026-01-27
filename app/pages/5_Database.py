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

# Recupero configurazioni
rds_config = config.rds
net_config = config.network

# --- ARCHITECTURE CHECK ---
# Un database DEVE stare in subnet private. Se non ci sono, blocchiamo tutto.
if net_config.private_subnet_count == 0:
    st.error("🛑 **Errore Architetturale**: Nessuna Subnet Privata rilevata.")
    st.markdown(
        """
        Per motivi di sicurezza, i database RDS non devono mai essere esposti direttamente su Internet.
        
        **Azione Richiesta:**
        1. Vai alla pagina **1. Network**.
        2. Imposta "Numero Subnet Private" ad almeno **1** (meglio 2 per l'Alta Disponibilità).
        3. Torna qui.
        """
    )
    st.stop() # Ferma l'esecuzione della pagina qui


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