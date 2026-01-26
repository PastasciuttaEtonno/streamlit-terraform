import streamlit as st
import sys
import os

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- INIT ---
initialize_session_state()
render_auth_sidebar()

# --- HEADER ---
st.header("4. Application Load Balancer (ALB)")
st.info("Distribuisci il traffico in entrata su più istanze per aumentare l'affidabilità e gestire il routing.")

# Recupero configurazioni
alb_config = st.session_state.project_config.alb
ec2_config = st.session_state.project_config.ec2

# --- LOGICA SUGGERIMENTI ---
if ec2_config.instance_count > 1 and not alb_config.enabled:
    st.warning(f"💡 Suggerimento: Hai configurato {ec2_config.instance_count} istanze. Un Load Balancer è fortemente raccomandato.")

# ------------------------------------------------------------------
# INTERFACCIA REATTIVA (Senza st.form)
# ------------------------------------------------------------------

# 1. Main Toggle (Ora aggiorna la pagina istantaneamente!)
is_enabled = st.checkbox("Abilita Load Balancer", value=alb_config.enabled)

# Warning immediato per singola istanza
if ec2_config.instance_count == 1 and is_enabled:
    st.caption("⚠️ Nota: Stai abilitando un Load Balancer per una sola istanza. Utile per HTTPS gestito o architetture private.")    

st.divider()

# 2. Configurazione Base
c1, c2 = st.columns(2)
with c1:
    name = st.text_input("Nome Load Balancer", value=alb_config.name, disabled=not is_enabled)
with c2:
    port = st.number_input("Porta di Ascolto (Listener)", value=alb_config.ingress_port, min_value=1, max_value=65535, disabled=not is_enabled)
    st.caption("Porta su cui l'ALB accetta traffico dall'esterno (es. 80).")

st.divider()

# 3. Listener Routing (Dinamico)
st.markdown("### 🔀 Listener Routing")
st.caption("Definisci cosa succede quando arriva traffico sulla porta specificata.")

action_options = ["forward", "redirect", "fixed-response"]
action_labels = [
    "Forward to Target Group (Standard - Inoltra alle EC2)", 
    "Redirect to URL (es. HTTP -> HTTPS)", 
    "Return Fixed Response (es. Pagina Manutenzione)"
]

try:
    current_index = action_options.index(alb_config.action_type)
except ValueError:
    current_index = 0

# Radio button reattivo: cambia subito i campi sotto!
action_type = st.radio(
    "Azione Default Listener",
    options=action_options,
    format_func=lambda x: action_labels[action_options.index(x)],
    index=current_index,
    disabled=not is_enabled
)

st.markdown("<br>", unsafe_allow_html=True)

# Inizializziamo le variabili con i valori attuali per non perderli
redir_proto, redir_port, redir_code = alb_config.redirect_protocol, alb_config.redirect_port, alb_config.redirect_status_code
fixed_body, fixed_code, fixed_type = alb_config.fixed_response_body, alb_config.fixed_response_code, alb_config.fixed_response_content_type

# --- UI DINAMICA (Compare subito in base alla scelta sopra) ---
if action_type == "forward":
    if is_enabled:
        st.info("✅ **Comportamento:** Il traffico verrà bilanciato e inoltrato alle istanze EC2 sane.", icon="📡")

elif action_type == "redirect":
    if is_enabled:
        st.info("↪️ **Comportamento:** L'utente verrà reindirizzato immediatamente a un altro URL/Porta.", icon="🔗")
    c_red1, c_red2, c_red3 = st.columns(3)
    with c_red1:
        redir_proto = st.selectbox("Protocollo Destinazione", ["HTTPS", "HTTP"], index=0 if alb_config.redirect_protocol=="HTTPS" else 1, disabled=not is_enabled)
    with c_red2:
        redir_port = st.text_input("Porta Destinazione", value=alb_config.redirect_port, disabled=not is_enabled)
    with c_red3:
        redir_code = st.selectbox("Status Code", ["HTTP_301", "HTTP_302"], index=0, help="301=Permanente, 302=Temporaneo", disabled=not is_enabled)

elif action_type == "fixed-response":
    if is_enabled:
        st.info("🛑 **Comportamento:** L'ALB risponderà direttamente al client.", icon="🚧")
    fixed_body = st.text_area("Corpo Risposta (Body)", value=alb_config.fixed_response_body, placeholder="<h1>Sito in manutenzione</h1>", disabled=not is_enabled)
    c_fix1, c_fix2 = st.columns(2)
    with c_fix1:
        fixed_code = st.text_input("Status Code (es. 503)", value=alb_config.fixed_response_code, disabled=not is_enabled)
    with c_fix2:
        fixed_type = st.selectbox("Content Type", ["text/plain", "text/html", "application/json"], index=0, disabled=not is_enabled)

# 4. Security Checks (Real-time)
if is_enabled and action_type == "forward":
    st.divider()
    st.markdown("#### 🛡️ Security Check")
    
    if ec2_config.subnet_type == "private":
        st.success("🔒 **Architettura Ottimale**: ALB Pubblico -> Istanze Private.", icon="✅")
    else:
        st.warning("⚠️ **Attenzione**: Le tue istanze sono in Subnet Pubbliche.")

    if 80 in ec2_config.allowed_ports:
        st.error("🚨 **RISCHIO SICUREZZA CRITICO**")
        st.markdown("**La porta 80 è aperta a tutti nelle impostazioni EC2.**")
        st.caption("Rimuovi la porta 80 dal modulo EC2 per forzare il traffico a passare dall'ALB.")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Bottone di Salvataggio (Normale button, non form_submit_button)
if st.button("Salva Configurazione ALB", type="primary"):
    
    # Aggiornamento dello Stato Globale
    st.session_state.project_config.alb.enabled = is_enabled
    st.session_state.project_config.alb.name = name
    st.session_state.project_config.alb.ingress_port = port
    st.session_state.project_config.alb.action_type = action_type
    
    # Salvataggio parametri routing
    if action_type == "redirect":
        st.session_state.project_config.alb.redirect_protocol = redir_proto
        st.session_state.project_config.alb.redirect_port = redir_port
        st.session_state.project_config.alb.redirect_status_code = redir_code
        
    if action_type == "fixed-response":
        st.session_state.project_config.alb.fixed_response_body = fixed_body
        st.session_state.project_config.alb.fixed_response_code = fixed_code
        st.session_state.project_config.alb.fixed_response_content_type = fixed_type
        
    st.toast("Configurazione salvata!", icon="💾")
    st.success("Configurazione aggiornata correttamente.")