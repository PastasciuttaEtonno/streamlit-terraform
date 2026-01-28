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
    st.info("Configura istanze, rete, storage e l'applicazione Docker da lanciare.")

    # Shortcut per comodità di lettura
    ec2_config = config.ec2
    net_config = config.network

    # === NOTA: Abbiamo rimosso 'with st.form' per permettere l'interattività immediata ===

    # --- SEZIONE 1: HARDWARE & RETE ---
    st.subheader("Compute & Placement")
    col1, col2 = st.columns(2)
    
    with col1:
        instance_type = st.selectbox(
            "Tipo Istanza",
            options=["t2.micro", "t3.micro", "t3.small", "t3.medium", "t3.large"],
            index=["t2.micro", "t3.micro", "t3.small", "t3.medium", "t3.large"].index(ec2_config.instance_type)
        )
        instance_count = st.number_input("Numero Istanze", 1, 10, ec2_config.instance_count)
        
        key_name = st.text_input(
            "AWS Key Pair Name",
            value=ec2_config.key_name,
            help="Inserisci il nome esatto della chiave creata nella console AWS",
            placeholder="es. my-key-pair"
        )

    with col2:
        ami_id = st.text_input("AMI ID", value=ec2_config.ami_id, help="Lascia default o inserisci un ID specifico")
        
        # Logica Placement
        has_public = net_config.public_subnet_count > 0
        has_private = net_config.private_subnet_count > 0
        options = []
        if has_public: options.append("public")
        if has_private: options.append("private")
        
        # Fallback selezione
        curr_sel = ec2_config.subnet_type
        if curr_sel not in options and options: curr_sel = options[0]
        
        subnet_type = st.radio(
            "Posizionamento Rete:", options=options,
            index=options.index(curr_sel) if options else 0,
            format_func=lambda x: "Public Subnet 🌐" if x == "public" else "Private Subnet 🔒"
        )

    st.divider()

    # --- SEZIONE 2: DOCKER APP DEPLOYMENT (INTERATTIVA) ---
    st.subheader("Application Deployment 🐳")
    
    # Recuperiamo i valori attuali dallo stato
    default_docker_enabled = getattr(ec2_config, 'docker_enabled', False)
    default_docker_image = getattr(ec2_config, 'docker_image', 'nginx:latest')
    default_docker_port = getattr(ec2_config, 'container_port', 80)
    default_db_gui = getattr(ec2_config, 'include_db_gui', False)

    # CHECKBOX FUORI DAL FORM: Cliccando qui, la pagina si ricarica SUBITO
    docker_enabled = st.checkbox("Attiva Deploy Docker all'avvio", value=default_docker_enabled)

    # Inizializziamo variabili per evitare errori se l'if non viene eseguito
    docker_image = default_docker_image
    container_port = default_docker_port
    include_db_gui = default_db_gui

    if docker_enabled:
        st.markdown("""
        <div style='background-color: #f0f2f6; color: #31333F; padding: 15px; border-radius: 10px; border-left: 5px solid #ffbd45; margin-bottom: 10px;'>
            <strong style='color: #000000;'>Modalità Docker Attiva:</strong> L'istanza installerà Docker e lancerà la tua immagine.
        </div>
        """, unsafe_allow_html=True)
        
        d_col1, d_col2 = st.columns([2, 1])
        with d_col1:
            docker_image = st.text_input("Docker Image Name", value=default_docker_image, placeholder="es. nginx:latest")
        with d_col2:
            container_port = st.number_input("Container Port", value=default_docker_port, min_value=1, max_value=65535)

        include_db_gui = st.checkbox("Installa GUI Database (phpMyAdmin/Adminer)", value=default_db_gui)
        
        if include_db_gui:
            st.caption("ℹ️ Sarà accessibile via browser sulla porta **8080**.")

    st.divider()

    # --- SEZIONE 3: STORAGE & SECURITY ---
    with st.expander("⚙️ Configurazioni Avanzate (Storage & Firewall)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Storage (EBS)**")
            disk_size = st.slider("Dimensione Disco Root (GB)", 8, 100, ec2_config.disk_size)
            disk_type = st.selectbox("Tipo Volume", ["gp3", "gp2", "io1", "standard"], index=["gp3", "gp2", "io1", "standard"].index(ec2_config.disk_type))
        
        with c2:
            st.markdown("**Security Group (Firewall)**")
            common_ports = {22: "SSH (22)", 80: "HTTP (80)", 443: "HTTPS (443)", 8080: "Alt-HTTP (8080)", 3306: "MySQL", 5432: "PostgreSQL"}
            
            # Calcolo porte default dinamico
            current_allowed = ec2_config.allowed_ports
            # Se attivi Docker GUI, suggeriamo visivamente la 8080
            if docker_enabled and include_db_gui and 8080 not in current_allowed:
                current_allowed.append(8080)

            selected_ports = st.multiselect(
                "Porte Ingress Consentite",
                options=list(common_ports.keys()),
                default=current_allowed,
                format_func=lambda x: common_ports.get(x, str(x))
            )

    # --- SEZIONE 4: USER DATA CUSTOM ---
    # Mostriamo questo campo solo se Docker è spento, altrimenti useremo il template automatico
    user_data = ec2_config.user_data_script
    
    if not docker_enabled:
        with st.expander("📜 Custom User Data (Script manuale)", expanded=False):
            user_data = st.text_area("Script Bash", value=ec2_config.user_data_script, height=100)
    else:
        # Se Docker è attivo, ignoriamo visivamente questo campo (verrà sovrascritto dal generatore)
        pass

    st.divider()

    # --- SALVATAGGIO (Pulsante normale, non form_submit) ---
    # Questo pulsante serve a persistere le modifiche nel Session State globale
    if st.button("💾 Salva Configurazione", type="primary"):
        
        # Aggiornamento dello Stato Globale
        ec2_config.instance_type = instance_type
        ec2_config.instance_count = int(instance_count)
        ec2_config.key_name = key_name
        ec2_config.ami_id = ami_id
        ec2_config.subnet_type = subnet_type
        
        ec2_config.disk_size = disk_size
        ec2_config.disk_type = disk_type
        ec2_config.allowed_ports = selected_ports
        
        # Salviamo la configurazione Docker
        ec2_config.docker_enabled = docker_enabled
        ec2_config.docker_image = docker_image
        ec2_config.container_port = int(container_port)
        ec2_config.include_db_gui = include_db_gui
        
        # Gestione User Data
        if not docker_enabled:
             ec2_config.user_data_script = user_data
        
        # Feedback Utente
        st.success("Configurazione salvata con successo!")
        st.toast("Settings updated!", icon="✅")
        
        if not key_name:
            st.warning("⚠️ Ricorda: Senza Key Pair non potrai accedere in SSH.")

elif config.provider == "gcp":
    st.header("3. Google Compute Engine (GCE)")
    st.info("Configura le macchine virtuali, il sistema operativo e il posizionamento di rete.")
    
    # Shortcut al modello di configurazione GCP
    comp_config = config.compute 
    
    # --- SEZIONE 1: HARDWARE ---
    st.subheader("Hardware & Capacity")
    col1, col2 = st.columns(2)
    
    with col1:
        # Tipi di macchine comuni
        available_types = ["e2-micro", "e2-medium", "e2-standard-2", "n1-standard-1", "n2-standard-2"]
        
        # Gestione index sicuro (se il valore salvato non è nella lista, usa default)
        current_idx = 1 # Default e2-medium
        if comp_config.machine_type in available_types:
            current_idx = available_types.index(comp_config.machine_type)
            
        m_type = st.selectbox(
            "Machine Type", 
            available_types, 
            index=current_idx,
            help="Scegli la dimensione della VM (CPU/RAM)"
        )
        
    with col2:
        count = st.number_input("Numero Istanze", min_value=1, max_value=10, value=comp_config.instance_count)

    st.divider()
    
    # --- SEZIONE 2: SISTEMA OPERATIVO ---
    st.subheader("Sistema Operativo (Boot Image)")
    c1, c2 = st.columns(2)
    
    with c1:
        img_proj = st.text_input(
            "Image Project", 
            value=comp_config.image_project,
            help="Progetto GCP che ospita l'immagine (es. 'debian-cloud', 'ubuntu-os-cloud')"
        )
    with c2:
        img_fam = st.text_input(
            "Image Family", 
            value=comp_config.image_family,
            help="Famiglia dell'immagine (es. 'debian-11', 'ubuntu-2004-lts')"
        )
        
    st.caption("ℹ️ Default: Debian 11. Cambia 'Project' e 'Family' per usare Ubuntu, CentOS, ecc.")

    st.divider()

    # --- SEZIONE 3: RETE E ZONA ---
    st.subheader("Placement & Network")
    c1, c2 = st.columns(2)
    
    with c1:
        zone = st.text_input(
            "GCP Zone", 
            value=comp_config.zone,
            placeholder="es. us-central1-a",
            help="La zona specifica dove lanciare le istanze."
        )
    
    with c2:
        # Selezione Accesso (Public vs Private)
        subnet_type = st.radio(
            "Tipo Accesso", 
            ["public", "private"], 
            index=0 if comp_config.subnet_type == "public" else 1,
            format_func=lambda x: "Public IP 🌐 (Internet Exposed)" if x == "public" else "Private Only 🔒 (Richiede Cloud NAT)"
        )

    st.divider()

    # --- SALVATAGGIO ---
    if st.button("💾 Salva Configurazione GCE", type="primary"):
        # Aggiornamento dello stato
        comp_config.machine_type = m_type
        comp_config.instance_count = int(count)
        comp_config.image_family = img_fam
        comp_config.image_project = img_proj
        comp_config.zone = zone
        comp_config.subnet_type = subnet_type
        
        st.success("Configurazione Google Compute Engine aggiornata!")
        st.toast("GCP Settings saved!", icon="✅")