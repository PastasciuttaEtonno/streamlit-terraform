import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar
from core.models import AWSProjectConfig, GCPProjectConfig, AWSNetworkConfig, AWSEC2Config, AWSRDSConfig, AWSALBConfig

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Terraform Studio", layout="wide")

initialize_session_state()
render_auth_sidebar()

# Recupero configurazione completa
config = st.session_state.project_config

# --- HEADER ---
st.title("Terraform Studio")
st.markdown("### Infrastructure As Code Generator")

# --- PROVIDER SELECTOR (SIDEBAR PRE-HEADER) ---
st.sidebar.header("Cloud Provider")
current_provider = config.provider
selected_provider = st.sidebar.selectbox("Seleziona Provider", ["aws", "gcp"], index=0 if current_provider == "aws" else 1)

# Logic to switch provider state if changed
if selected_provider != current_provider:
    if selected_provider == "gcp":
        st.session_state.project_config = GCPProjectConfig(
            project_name=config.project_name, 
            gcp_project_id="my-project-id"
        )
    else:
        # Revert to AWS Defaut
        st.session_state.project_config = AWSProjectConfig(
            project_name=config.project_name,
            region="us-east-1",
            network=AWSNetworkConfig(vpc_cidr="10.0.0.0/16", az_count=2, public_subnet_count=2, private_subnet_count=2),
            ec2=AWSEC2Config(instance_type="t3.micro", instance_count=1, ami_id="ami-x", subnet_type="public", key_name="", allowed_ports=[], disk_size=20, disk_type="gp3", user_data_script="")
        )
    st.rerun()

st.markdown("---")

# --- RENDER DASHBOARD BASED ON PROVIDER ---

if config.provider == "aws":
    # === AWS VIEW ===
    net = config.network
    ec2 = config.ec2
    alb = config.alb
    rds = config.rds

    # --- 1. KPI & METRICHE ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Progetto", value=config.project_name, border=True)

    with col2:
        st.metric(label="Regione AWS", value=config.region, border=True)

    with col3:
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
        active_resources = ec2.instance_count
        if alb.enabled: active_resources += 1
        if rds.enabled: active_resources += 1
        st.metric(label="Risorse Core Attive", value=f"{active_resources} Units", border=True)

    st.markdown("<br>", unsafe_allow_html=True) 

    # --- 2. ARCHITECTURE CARDS ---
    r1_c1, r1_c2 = st.columns(2)

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
                st.markdown(f"**Disk**: {ec2.disk_size}GB ({ec2.disk_type})")
            st.divider()
            st.markdown("**Firewall Rules (EC2):**")
            if ec2.allowed_ports:
                st.code(" ".join([str(p) for p in ec2.allowed_ports]), language="bash")
            else:
                st.caption("Nessuna porta esposta direttamente.")

    # RIGA 2: Load Balancer & Database
    r2_c1, r2_c2 = st.columns(2)

    with r2_c1:
        with st.container(border=True):
            c_head, c_status = st.columns([3, 1])
            c_head.subheader("Load Balancer")
            if alb.enabled:
                c_status.success("ACTIVE")
                st.markdown(f"**Name**: `{alb.name}`")
                c_alb1, c_alb2 = st.columns(2)
                with c_alb1: st.markdown(f"**Listener Port**: `{alb.ingress_port}`")
                with c_alb2:
                    action_icon = "📡" if alb.action_type == "forward" else "🔗" if alb.action_type == "redirect" else "🛑"
                    st.markdown(f"**Action**: {action_icon} `{alb.action_type.upper()}`")
            else:
                c_status.error("OFF")
                st.markdown("Il modulo Load Balancer è disabilitato.")

    with r2_c2:
        with st.container(border=True):
            c_head_db, c_status_db = st.columns([3, 1])
            c_head_db.subheader("Database")
            if rds.enabled:
                c_status_db.success("ACTIVE")
                st.markdown(f"**Engine**: `{rds.engine}` | **DB Name**: `{rds.db_name}`")
                st.markdown(f"**Class**: `{rds.instance_class}`")
            else:
                c_status_db.error("OFF")
                st.markdown("Il modulo Database è disabilitato.")

elif config.provider == "gcp":
    # === GCP VIEW ===
    net = config.network
    comp = config.compute

    # Allow editing the Project ID
    col_pid, col_reg, col_count = st.columns([2, 1, 1])
    with col_pid:
        new_pid = st.text_input("GCP Project ID", value=config.gcp_project_id)
        if new_pid != config.gcp_project_id:
            st.session_state.project_config.gcp_project_id = new_pid
            st.rerun()
            
    with col_reg:
        st.metric("GCP Region", config.region)

    with col_count:
        st.metric("Compute Instances", comp.instance_count)

    st.success(f"**Google Cloud Platform Mode** - Project: `{config.gcp_project_id}`")

    r1_c1, r1_c2 = st.columns(2)
    with r1_c1: 
        with st.container(border=True):
            st.subheader("VPC Network")
            st.info(f"Subnet CIDR: {net.subnet_cidr}")
            
    with r1_c2:
         with st.container(border=True):
            st.subheader("Compute Engine")
            st.write(f"Machine Type: **{comp.machine_type}**")
            st.write(f"Image: **{comp.image_project}/{comp.image_family}**")


# --- 3. SYSTEM READINESS (COMMON) ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("System Readiness")

col_s1, col_s2, col_s3 = st.columns(3)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
output_dir = os.path.join(base_dir, "output")

with col_s1:
    if config.provider == "aws" and os.getenv("AWS_ACCESS_KEY_ID"):
        st.success("**AWS Credentials**: Connesse")
    elif config.provider == "gcp" and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        st.success("**GCP Credentials**: Connesse")
    else:
        st.error(f"**{config.provider.upper()} Credentials**: Mancanti o non rilevate")

with col_s2:
    if os.path.exists(os.path.join(output_dir, "main.tf")):
        st.success("**Terraform Code**: Generato")
    else:
        st.warning("**Terraform Code**: In attesa")

with col_s3:
    if os.path.exists(os.path.join(output_dir, ".terraform")):
        st.info("**Provider Init**: Cache Trovata")
    else:
        st.warning("**Provider Init**: Da eseguire")