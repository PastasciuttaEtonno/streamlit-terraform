import streamlit as st
import sys
import os

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.terraform_runner import TerraformRunner
from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- INIT ---
initialize_session_state()
render_auth_sidebar()

st.header("5. Gestione Infrastruttura")
st.info("Esegui il Deploy o distruggi le risorse su AWS.")

# Percorsi
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Controllo codice generato
if not os.path.exists(os.path.join(OUTPUT_DIR, "main.tf")):
    st.warning("⚠️ Non hai ancora generato il codice! Vai alla pagina 4.")
    st.stop()

runner = TerraformRunner(OUTPUT_DIR)

# --- TABS PER ORGANIZZARE LE AZIONI ---
tab_plan,tab_cost, tab_apply, tab_destroy = st.tabs(["📋 Plan","💰 Costi", "🚀 Deploy", "💣 Destroy"])

# -----------------
# TAB 1: PLAN
# -----------------
with tab_plan:
    st.subheader("1. Inizializza & Pianifica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Terraform Init", type="primary"):
            with st.spinner("Scaricando provider AWS..."):
                success, output = runner.init()
                if success:
                    st.success("Init completato!")
                    st.session_state['tf_initialized'] = True
                    with st.expander("Log Init"):
                        st.code(output)
                else:
                    st.error("Init fallito")
                    st.code(output)

    with col2:
        # Abilita Plan solo se Init è fatto (controllo base) o se l'utente vuole forzare
        if st.button("📄 Terraform Plan"):
            with st.spinner("Calcolo delle modifiche..."):
                success, output = runner.plan()
                if success:
                    st.success("Plan calcolato!")
                    st.code(output, language="hcl")
                else:
                    st.error("Plan fallito")
                    st.code(output)

# -----------------
# TAB 2: COSTI (FinOps)
# -----------------
with tab_cost:
    st.subheader("3. Stima dei Costi (Infracost)")
    st.info("Ottieni una previsione di spesa mensile basata sul tuo codice Terraform.")
    
    # Input API Key (con mascheramento password)
    # Consiglio: L'utente può ottenerla gratis su dashboard.infracost.io
    api_key = st.text_input("Infracost API Key", type="password", help="Ottienila gratis su infracost.io")
    
    if st.button("Calcola Preventivo"):
        if not api_key:
            st.error("Inserisci una API Key valida per procedere.")
        else:
            with st.spinner("Analisi costi in corso (download immagine Docker...)..."):
                success, result = runner.estimate_cost(api_key)
                
                if success:
                    # Parsing del risultato JSON
                    projects = result.get('projects', [])
                    if projects:
                        summary = projects[0].get('breakdown', {})
                        resources = summary.get('resources', [])
                        
                        # Totale Mensile
                        total_monthly = result.get('totalMonthlyCost', "0.00")
                        
                        # --- VISUALIZZAZIONE ---
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            st.metric(label="Costo Mensile Stimato", value=f"${total_monthly}", delta="Pre-Tax")
                        
                        with c2:
                            if float(total_monthly) == 0:
                                st.success("🎉 Ottimo! Sembra che rientri nel Free Tier (o le risorse non hanno costi orari).")
                            else:
                                st.warning("⚠️ Attenzione: Le risorse configurate hanno un costo ricorrente.")

                        st.divider()
                        st.subheader("Dettaglio Risorse")
                        
                        # Tabella dettagliata
                        cost_data = []
                        for res in resources:
                            name = res.get('name', 'Unknown')
                            cost = res.get('monthlyCost', '0')
                            # Filtriamo risorse a costo zero per pulizia, se vuoi
                            if float(cost) > 0:
                                cost_data.append({"Risorsa": name, "Costo ($/mese)": cost})
                        
                        if cost_data:
                            st.table(cost_data)
                        else:
                            st.caption("Nessuna risorsa a pagamento rilevata esplicitamente.")
                            
                    else:
                        st.warning("Nessun progetto rilevato nell'output.")
                else:
                    st.error("Errore nella stima:")
                    st.code(result)

# -----------------
# TAB 3: APPLY
# -----------------
with tab_apply:
    st.subheader("2. Deploy su AWS")
    st.warning("⚠️ Questa azione creerà risorse reali (costi AWS).")
    
    confirm_deploy = st.checkbox("Ho controllato il Plan e confermo.")
    
    if st.button("🚀 Esegui Deploy", type="primary", disabled=not confirm_deploy):
        
        # Container per lo stato di avanzamento
        with st.status("Deploy in corso...", expanded=True) as status:
            st.write("🔹 Applicazione configurazione Terraform...")
            success, output = runner.apply()
            
            if success:
                status.update(label="Deploy Completato! ✅", state="complete", expanded=False)
                st.balloons()
                
                # --- NUOVO: RECUPERO OUTPUT ---
                st.divider()
                st.success("✅ Infrastruttura Online!")
                
                outputs = runner.get_outputs()
                
                if outputs:
                    # Recuperiamo gli IP (se esistono)
                    ips = outputs.get("ec2_public_ips", [])
                    
                    if ips:
                        st.subheader("Connection Details")
                        
                        # Creiamo una card per ogni istanza trovata
                        for i, ip in enumerate(ips):
                            with st.container(border=True):
                                c1, c2 = st.columns([1, 3])
                                
                                with c1:
                                    st.metric(label=f"Server #{i+1}", value=ip)
                                    # Link cliccabile HTTP
                                    st.markdown(f"[🌐 Apri nel Browser](http://{ip})")
                                
                                with c2:
                                    st.markdown("**Comando SSH rapido:**")
                                    # Recuperiamo il nome della chiave dallo stato
                                    key_name = st.session_state.project_config.ec2.key_name
                                    
                                    # Se l'utente ha messo "my-key", il file locale sarà probabilmente "my-key.pem"
                                    key_file = f"{key_name}.pem" if key_name else "tua-chiave.pem"
                                    
                                    ssh_cmd = f"ssh -i {key_file} ubuntu@{ip}"
                                    st.code(ssh_cmd, language="bash")
                    else:
                        st.warning("Nessun IP pubblico trovato (le istanze sono private?)")
                        
                    with st.expander("Vedi Output JSON Grezzo"):
                        st.json(outputs)
                else:
                    st.warning("Impossibile leggere gli output di Terraform.")
                    
            else:
                status.update(label="Deploy Fallito ❌", state="error")
                st.error("Errore durante il deploy.")
                st.code(output)

# -----------------
# TAB 3: DESTROY
# -----------------
with tab_destroy:
    st.subheader("3. Distruggi Risorse")
    st.error("🚨 ATTENZIONE: Questa azione cancellerà TUTTE le risorse create da Terraform. I dati saranno persi.")
    
    # Doppio check di sicurezza
    confirm_destroy = st.text_input("Scrivi 'DESTROY' per confermare:")
    
    if st.button("💣 Distruggi Tutto", type="primary", disabled=confirm_destroy != "DESTROY"):
        with st.status("Distruzione in corso...", expanded=True) as status:
            st.write("Avvio Terraform Destroy...")
            success, output = runner.destroy()
            
            if success:
                status.update(label="Pulizia Completata ✅", state="complete")
                st.success("Tutte le risorse sono state rimosse.")
            else:
                status.update(label="Errore nella distruzione ❌", state="error")
                st.code(output)