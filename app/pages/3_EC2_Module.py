import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

initialize_session_state()
render_auth_sidebar()

config = st.session_state.project_config

if config.provider == "aws":
    st.header("3. Configurazione Compute (AWS EC2)")
    st.info("Configura istanze, rete, storage e script di avvio.")

    # Shortcut
    ec2_config = config.ec2
    net_config = config.network

    with st.form("ec2_form"):
        # --- SEZIONE BASE ---
        st.subheader("Compute & Placement")
        col1, col2 = st.columns(2)
        
        with col1:
            instance_type = st.selectbox(
                "Tipo Istanza",
                options=["t2.micro", "t3.micro", "t3.small", "t3.medium", "t3.large"],
                index=["t2.micro", "t3.micro", "t3.small", "t3.medium", "t3.large"].index(ec2_config.instance_type)
            )
            instance_count = st.number_input("Numero Istanze", 1, 5, ec2_config.instance_count)
            
            key_name = st.text_input(
                "AWS Key Pair Name",
                value=ec2_config.key_name,
                help="Inserisci il nome esatto della chiave creata nella console AWS (senza .pem)",
                placeholder="es. my-key-pair"
            )

        with col2:
            ami_id = st.text_input("AMI ID", value=ec2_config.ami_id)
            
            # Logica Placement (Public/Private) che abbiamo fatto prima
            has_public = net_config.public_subnet_count > 0
            has_private = net_config.private_subnet_count > 0
            options = []
            if has_public: options.append("public")
            if has_private: options.append("private")
            
            # Gestione fallback
            curr_sel = ec2_config.subnet_type
            if curr_sel not in options and options: curr_sel = options[0]
            
            subnet_type = st.radio(
                "Posizionamento Rete:", options=options,
                index=options.index(curr_sel) if options else 0,
                format_func=lambda x: "Public Subnet 🌐" if x == "public" else "Private Subnet 🔒"
            )

        st.divider()

        # --- NUOVO: STORAGE ---
        with st.expander("💾 Configurazione Storage (EBS)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                disk_size = st.slider("Dimensione Disco Root (GB)", 8, 100, ec2_config.disk_size)
            with c2:
                disk_type = st.selectbox(
                    "Tipo Volume", 
                    ["gp3", "gp2", "io1", "standard"], 
                    index=["gp3", "gp2", "io1", "standard"].index(ec2_config.disk_type)
                )

        # --- NUOVO: SECURITY GROUP RULES ---
        with st.expander("🛡️ Firewall & Porte (Security Group)", expanded=False):
            st.caption("Seleziona le porte TCP da aprire in ingresso (Ingress Rules).")
            
            common_ports = {
                22: "SSH (22)",
                80: "HTTP (80)",
                443: "HTTPS (443)",
                8080: "Alt-HTTP (8080)",
                3306: "MySQL (3306)",
                5432: "PostgreSQL (5432)"
            }
            
            selected_ports = st.multiselect(
                "Porte Consentite",
                options=list(common_ports.keys()),
                default=ec2_config.allowed_ports,
                format_func=lambda x: common_ports.get(x, str(x))
            )

        # --- NUOVO: USER DATA ---
        with st.expander("📜 User Data (Script di avvio)", expanded=False):
            st.caption("Script Bash eseguito al primo avvio dell'istanza (es. installazione software).")
            user_data = st.text_area(
                "Script Bash",
                value=ec2_config.user_data_script,
                height=150
            )

        submitted = st.form_submit_button("Salva Configurazione Completa", type="primary")
        
        if submitted:
            st.session_state.project_config.ec2.key_name = key_name # SALVATAGGIO
            st.session_state.project_config.ec2.instance_type = instance_type
            st.session_state.project_config.ec2.instance_count = int(instance_count)
            st.session_state.project_config.ec2.ami_id = ami_id
            st.session_state.project_config.ec2.subnet_type = subnet_type
            st.session_state.project_config.ec2.disk_size = disk_size
            st.session_state.project_config.ec2.disk_type = disk_type
            st.session_state.project_config.ec2.allowed_ports = selected_ports
            st.session_state.project_config.ec2.user_data_script = user_data
            
            if not key_name:
                st.warning("⚠️ Hai salvato senza specificare una Key Pair. Non potrai accedere via SSH!")
            else:
                st.success("Configurazione aggiornata!")
                st.toast("Configurazione EC2 salvata!", icon="💾")

elif config.provider == "gcp":
    st.header("3. Google Compute Engine (GCE)")
    
    comp_config = config.compute # GCPComputeConfig
    
    with st.form("gcp_form"):
        col1, col2 = st.columns(2)
        with col1:
            m_type = st.selectbox("Machine Type", ["e2-micro", "e2-medium", "e2-standard-2"], index=["e2-micro", "e2-medium", "e2-standard-2"].index(comp_config.machine_type) if comp_config.machine_type in ["e2-micro", "e2-medium", "e2-standard-2"] else 1)
            count = st.number_input("Count", 1, 10, comp_config.instance_count)
            
        with col2:
            img_fam = st.text_input("Image Family", value=comp_config.image_family)
            img_proj = st.text_input("Image Project", value=comp_config.image_project)
            
        zone = st.text_input("Zone", value=comp_config.zone)
        
        # GCP Public/Private Selection
        subnet_type = st.radio(
            "Access Type", 
            ["public", "private"], 
            index=0 if comp_config.subnet_type == "public" else 1,
            format_func=lambda x: "Public IP (Internet Exposed)" if x == "public" else "Private Only (Cloud NAT required for outbound)"
        )
        
        if st.form_submit_button("Save GCE Config"):
            st.session_state.project_config.compute.machine_type = m_type
            st.session_state.project_config.compute.instance_count = count
            st.session_state.project_config.compute.image_family = img_fam
            st.session_state.project_config.compute.image_project = img_proj
            st.session_state.project_config.compute.zone = zone
            st.session_state.project_config.compute.subnet_type = subnet_type
            st.success("GCP Compute Saved!")