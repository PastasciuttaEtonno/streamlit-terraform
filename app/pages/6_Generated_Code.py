import streamlit as st
import sys
import os
import shutil

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.template_renderer import TerraformRenderer
from core.auth_sidebar import render_auth_sidebar

render_auth_sidebar()

st.header("4. Generazione Codice")
st.info("Qui trasformiamo la tua configurazione in file Terraform reali (.tf).")

# Percorsi
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Recuperiamo la config
config = st.session_state.project_config

# Mostriamo un riepilogo JSON
with st.expander("Vedi configurazione JSON completa"):
    st.json(config.model_dump())

# --- BOTTONE GENERAZIONE ---
if st.button("🚀 Genera Terraform Code", type="primary"):
    try:
        # 1. Inizializza Render
        renderer = TerraformRenderer(TEMPLATE_DIR, OUTPUT_DIR, provider=config.provider)
        
        # 1-BIS: Se Docker abilitato, pre-renderizziamo user_data.sh
        if config.provider == "aws" and config.ec2.docker_enabled:
            # Render manuale del template user_data
            # NOTA: Usiamo "renderer.env" per riutilizzare l'ambiente Jinja già configurato
            # Ma il path del template user_data è in "modules/ec2/user_data.sh.j2"
            # Se renderer.provider == "aws", la root è "templates/aws" (o fallback a "templates")
            # Dobbiamo capire se "modules" è dentro "templates/aws" o "templates"
            
            # Proviamo a recuperare il template dal loader
            try:
                # Path relativo alla root dei template configurata nel renderer
                ud_template_name = "modules/ec2/user_data.sh.j2" 
                ud_template = renderer.env.get_template(ud_template_name)
                
                # Context per il rendering (appiattiamo un po' per comodità nel template)
                ud_context = {
                    "docker_image": config.ec2.docker_image,
                    "container_port": config.ec2.container_port,
                    "db_engine": config.rds.engine if config.rds.enabled else "none",
                    # Passiamo le credenziali statiche ("Clean" values, not Terraform vars)
                    "db_user": config.rds.username,
                    "db_password": config.rds.password,
                    "db_name": config.rds.db_name,
                }
                
                # Renderizziamo lo script
                script_content = ud_template.render(ud_context)
                
                # Iniettiamo lo script nella configurazione che andrà a main.tf
                config.ec2.user_data_script = script_content
                st.toast("Docker User Data generato e iniettato!", icon="🐳")
                
            except Exception as e:
                st.warning(f"Impossibile generare User Data Docker: {e}")

        # 2. Renderizza usando i dati dello stato (ora aggiornati con lo script)
        renderer.render_root(config.model_dump())
        
        # 3. Pulizia opzionale: rimuovi il vecchio variables.tf se esiste ancora
        old_vars = os.path.join(OUTPUT_DIR, "variables.tf")
        if os.path.exists(old_vars):
            os.remove(old_vars)

        st.success(f"✅ Codice generato con successo in: {OUTPUT_DIR}")
        st.session_state['code_generated'] = True

    except Exception as e:
        st.error(f"Errore durante la generazione: {e}")

# --- VISUALIZZATORE & EXPORT ---
# Se il codice è stato generato (o la cartella esiste e contiene il main)
if os.path.exists(os.path.join(OUTPUT_DIR, "main.tf")):
    
    st.divider()
    
    # -- 1. SEZIONE DOWNLOAD (NUOVA) --
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📦 Download Pacchetto")
        st.caption("Scarica l'intero progetto (inclusi i moduli) per condividerlo o usarlo altrove.")
        
    with col2:
        # Creiamo lo ZIP al volo
        # base_name="terraform_bundle" -> crea terraform_bundle.zip
        # root_dir=OUTPUT_DIR -> zippa il contenuto della cartella output
        zip_path = shutil.make_archive("terraform_bundle", 'zip', OUTPUT_DIR)
        
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📥 Scarica .ZIP",
                data=f,
                file_name="terraform_project.zip",
                mime="application/zip",
                type="primary"
            )

    st.divider()
    
    # -- 2. ANTEPRIMA FILE --
    st.subheader("👀 Anteprima Codice")

    # Creiamo i tab per i file principali
    tab1, tab2, tab3 = st.tabs(["main.tf", "provider.tf", "outputs.tf"])

    def read_file(filename):
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
        return "# File non trovato"

    with tab1:
        st.code(read_file("main.tf"), language="hcl")
        
    with tab2:
        st.code(read_file("provider.tf"), language="hcl")

    with tab3:
        # outputs.tf potrebbe non esistere nella root se non lo abbiamo creato esplicitamente,
        # ma controlliamo per sicurezza
        content = read_file("outputs.tf")
        if "File non trovato" in content:
            st.info("Questo progetto usa gli output dei moduli (vedi tab 5 per il Plan).")
        else:
            st.code(content, language="hcl")