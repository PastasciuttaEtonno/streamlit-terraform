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

# Recupero configurazione completa
config = st.session_state.project_config
net = config.network
ec2 = config.ec2
alb = config.alb
rds = config.rds

# --- HEADER ---
st.title("Terraform Studio")
st.markdown("### Infrastructure As Code Generator")
st.markdown("---")

# --- 1. KPI & METRICHE (CON COLORI) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Progetto", value=config.project_name, border=True)

with col2:
    st.metric(label="Regione AWS", value=config.region, border=True)

with col3:
    # Logica Colore: Verde se HA (più zone), Rosso se Singola AZ
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
    # Conteggio Risorse Attive
    active_resources = ec2.instance_count
    if alb.enabled: active_resources += 1 # Load Balancer
    if rds.enabled: active_resources += 1 # Database Instance
    
    st.metric(label="Risorse Core Attive", value=f"{active_resources} Units", border=True)

st.markdown("<br>", unsafe_allow_html=True) # Spaziatore

# --- 2. ARCHITECTURE CARDS (GRID 2x2) ---

# RIGA 1: Network & Compute
r1_c1, r1_c2 = st.columns(2)

# --- CARD: RETE ---
with r1_c1:
    with st.container(border=True):
        st.subheader("Network Layer")
        st.markdown(f"**VPC CIDR**: `{net.vpc_cidr}`")
        st.divider()
        
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            st.info(f"**Public Subnets**: {net.public_subnet_count}\n\nIngress Point")
        with c_sub2:
            if net.private_subnet_count > 0:
                st.success(f"**Private Subnets**: {net.private_subnet_count}\n\nSecure Backend")
            else:
                st.warning("**Private Subnets**: 0\n\nNo Isolation")

# --- CARD: COMPUTE ---
with r1_c2:
    with st.container(border=True):
        st.subheader("Compute Layer")
        
        c_spec1, c_spec2 = st.columns(2)
        with c_spec1:
            st.markdown(f"**Count**: `{ec2.instance_count}` x `{ec2.instance_type}`")
            st.markdown(f"**AMI**: `{ec2.ami_id[:12]}...`")
        with c_spec2:
            placement_color = "orange" if ec2.subnet_type == "public" else "green"
            st.markdown(f"**Zone**: :{placement_color}[{ec2.subnet_type.upper()}]")
            
            # Storage info
            st.markdown(f"**Disk**: {ec2.disk_size}GB ({ec2.disk_type})")

        st.divider()
        
        # Logica porte aperte
        st.markdown("**Firewall Rules (EC2):**")
        if ec2.allowed_ports:
            st.code(" ".join([str(p) for p in ec2.allowed_ports]), language="bash")
        else:
            st.caption("Nessuna porta esposta direttamente (Accesso via Internal/SSH).")

# RIGA 2: Load Balancer & Database
r2_c1, r2_c2 = st.columns(2)

# --- CARD: LOAD BALANCER ---
with r2_c1:
    with st.container(border=True):
        c_head, c_status = st.columns([3, 1])
        c_head.subheader("Load Balancer")
        
        if alb.enabled:
            c_status.success("ACTIVE")
            
            st.markdown(f"**Name**: `{alb.name}`")
            
            c_alb1, c_alb2 = st.columns(2)
            with c_alb1:
                st.markdown(f"**Listener Port**: `{alb.ingress_port}`")
            with c_alb2:
                # Icona azione
                action_icon = "📡" if alb.action_type == "forward" else "🔗" if alb.action_type == "redirect" else "🛑"
                st.markdown(f"**Action**: {action_icon} `{alb.action_type.upper()}`")
            
            # Dettagli Routing
            if alb.action_type == "redirect":
                st.caption(f"Redirects to {alb.redirect_protocol}:{alb.redirect_port}")
            elif alb.action_type == "fixed-response":
                st.caption(f"Responds with {alb.fixed_response_code}")
                
        else:
            c_status.error("OFF")
            st.markdown("Il modulo Load Balancer è disabilitato.")
            st.caption("Il traffico raggiunge direttamente le istanze EC2.")

# --- CARD: DATABASE ---
with r2_c2:
    with st.container(border=True):
        c_head_db, c_status_db = st.columns([3, 1])
        c_head_db.subheader("Database")
        
        if rds.enabled:
            c_status_db.success("ACTIVE")
            
            c_db1, c_db2 = st.columns(2)
            with c_db1:
                engine_icon = "🐬" if rds.engine == "mysql" else "🐘"
                st.markdown(f"**Engine**: {engine_icon} `{rds.engine}`")
                st.markdown(f"**DB Name**: `{rds.db_name}`")
            with c_db2:
                st.markdown(f"**Class**: `{rds.instance_class}`")
                st.markdown(f"**Storage**: `{rds.allocated_storage} GB`")
            
            st.divider()
            st.markdown(f"**Security**: 🔒 Private Access Only")
            st.caption(f"User: `{rds.username}`")
            
        else:
            c_status_db.error("OFF")
            st.markdown("Il modulo Database è disabilitato.")
            st.caption("Nessuna persistenza dei dati configurata.")

# --- 3. SYSTEM READINESS ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("System Readiness")

col_s1, col_s2, col_s3 = st.columns(3)

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
output_dir = os.path.join(base_dir, "output")

with col_s1:
    # 1. Credenziali
    if os.getenv("AWS_ACCESS_KEY_ID"):
        st.success("**AWS Credentials**: Connesse")
    else:
        st.error("**AWS Credentials**: Mancanti")

with col_s2:
    # 2. Codice Generato
    if os.path.exists(os.path.join(output_dir, "main.tf")):
        st.success("**Terraform Code**: Generato")
    else:
        st.warning("**Terraform Code**: In attesa")

with col_s3:
    # 3. Init Status
    if os.path.exists(os.path.join(output_dir, ".terraform")):
        st.info("**Provider Init**: Cache Trovata")
    else:
        st.warning("**Provider Init**: Da eseguire")