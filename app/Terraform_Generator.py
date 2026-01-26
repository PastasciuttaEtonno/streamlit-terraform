import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Terraform Studio", layout="wide")

initialize_session_state()
render_auth_sidebar()

# Recupero configurazione
config = st.session_state.project_config
net = config.network
ec2 = config.ec2

# --- HEADER ---
st.title("Terraform Studio")
st.markdown("### Infastracure As a Code Generator")
st.markdown("---")

# --- 1. KPI & METRICHE (CON COLORI) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Progetto", value=config.project_name, border=True)

with col2:
    st.metric(label="Regione AWS", value=config.region, border=True)

with col3:
    # Logica Colore: Verde se HA, Rosso se Singola AZ
    is_ha = net.az_count > 1
    ha_val = f"{net.az_count} Zone (HA)" if is_ha else "1 Zona (Single)"
    st.metric(
        label="Affidabilità", 
        value=ha_val, 
        delta="Ottimale" if is_ha else "A Rischio",
        delta_color="normal" if is_ha else "inverse",
        border=True
    )

with col4:
    # Stima risorse
    st.metric(label="Risorse Totali", value=f"{ec2.instance_count} Istanze", border=True)

st.markdown("<br>", unsafe_allow_html=True) # Spaziatore

# --- 2. DASHBOARD CARDS ---
c_net, c_compute = st.columns(2)

# --- CARD: RETE ---
with c_net:
    with st.container(border=True):
        st.subheader("Network Architecture")
        st.markdown(f"**VPC CIDR**: `{net.vpc_cidr}`")
        
        st.divider()
        
        # Visualizzazione Grafica Semplice
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            st.info(f"**Public Subnets**: {net.public_subnet_count}\n\nGateway Internet")
        with c_sub2:
            if net.private_subnet_count > 0:
                st.success(f"**Private Subnets**: {net.private_subnet_count}\n\nBackend Sicuro")
            else:
                st.warning("**Private Subnets**: 0\n\nNessun isolamento")
            
        # Analisi Architetturale
        if net.private_subnet_count == 0:
            st.error("**Attenzione**: Architettura 'Flat'. Database e backend sono esposti su IP pubblici.")

# --- CARD: COMPUTE ---
with c_compute:
    with st.container(border=True):
        st.subheader("Compute & Security")
        
        # Tabella Specs
        c_spec1, c_spec2 = st.columns(2)
        with c_spec1:
            st.markdown(f"**Instance**: `{ec2.instance_type}`")
            st.markdown(f"**AMI**: `{ec2.ami_id}`")
        with c_spec2:
            placement_icon = "[PUBLIC]" if ec2.subnet_type == "public" else "[PRIVATE]"
            st.markdown(f"**Placement**: {placement_icon} {ec2.subnet_type.capitalize()}")
            st.markdown(f"**IP Pubblico**: {'Yes' if ec2.subnet_type == 'public' else 'No'}")

        st.divider()
        
        # Sezione Storage & Firewall affiancata
        c_store, c_firewall = st.columns(2)
        
        with c_store:
            st.markdown("#### Storage")
            # Colore diverso se GP3 (veloce) o Standard
            disk_color = "green" if ec2.disk_type in ["gp3", "io1"] else "orange"
            st.markdown(f":{disk_color}[**{ec2.disk_size} GB**] ({ec2.disk_type})")
            
        with c_firewall:
            st.markdown("#### Firewall")
            if ec2.allowed_ports:
                # Usiamo st.code per dare l'effetto "badge" tecnico
                st.code(" ".join([str(p) for p in ec2.allowed_ports]), language="bash")
            else:
                st.error("Nessuna porta aperta")

        # User Data Alert
        if ec2.user_data_script:
            with st.expander("Script di Avvio attivo"):
                st.code(ec2.user_data_script, language="bash")

# --- 3. STATUS BAR (SEMAFORO) ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("System Readiness")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    # 1. Credenziali
    if os.getenv("AWS_ACCESS_KEY_ID"):
        st.success("**AWS Credentials**: Connesse")
    else:
        st.error("**AWS Credentials**: Mancanti")

with col_s2:
    # 2. Codice Generato
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if os.path.exists(os.path.join(base_dir, "output", "main.tf")):
        st.success("**Terraform Code**: Generato")
    else:
        st.warning("**Terraform Code**: In attesa")

with col_s3:
    # 3. Init Status
    if os.path.exists(os.path.join(base_dir, "output", ".terraform")):
        st.info("**Provider Init**: Cache Trovata")
    else:
        st.warning("**Provider Init**: Da eseguire")