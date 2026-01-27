import subprocess
import os
import platform
import json
import docker

class TerraformRunner:
    def __init__(self, working_dir: str):
        self.working_dir = os.path.abspath(working_dir)
        
        # --- FIX PER WINDOWS + DOCKER ---
        # Docker su Windows preferisce i percorsi con "/" (C:/Users/...)
        # invece dei backslash standard di Windows (C:\Users\...)
        if platform.system() == "Windows":
            self.working_dir = self.working_dir.replace("\\", "/")
            
        self.docker_image = "hashicorp/terraform:latest"

    def _run_docker_command(self, tf_args):
        """
        Esegue terraform dentro un container Docker effimero.
        """
        # 1. Costruiamo il comando Docker base
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.working_dir}:/workspace",
            "-w", "/workspace",
        ]

        # 3. Passiamo le credenziali AWS (se presenti)
        aws_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION"]
        for var in aws_vars:
            value = os.getenv(var)
            if value:
                cmd.extend(["-e", f"{var}={value}"])

        # 4. Passiamo le credenziali GCP (se presenti)
        gcp_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gcp_creds_path:
            # Dobbiamo montare il file delle credenziali dentro il container
            # Assumiamo che il file esista sull'host.
            # Lo montiamo come /gcp_key.json e settiamo la variabile d'ambiente
            
            # Normalizziamo path per Docker Windows
            host_key_path = os.path.abspath(gcp_creds_path)
            if platform.system() == "Windows":
                 host_key_path = host_key_path.replace("\\", "/")

            # Aggiungiamo il volume mount per la chiave
            # Nota: --volume host_path:container_path
            cmd.extend(["-v", f"{host_key_path}:/gcp_key.json"])
            
            # Passiamo l'env var puntando al percorso INTERNO al container
            cmd.extend(["-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json"])

        # 5. Aggiungiamo immagine e argomenti
        cmd.append(self.docker_image)
        cmd.extend(tf_args)

        # DEBUG: Stampa il comando (utile per capire cosa sta succedendo)
        # print(f"🐳 Docker Cmd: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
            
        except subprocess.CalledProcessError as e:
            # Se Terraform fallisce, restituiamo l'errore standard e output
            return False, e.stderr + "\n" + e.stdout
            
        except FileNotFoundError:
            return False, "❌ Errore: Docker non sembra installato o nel PATH."

    def debug_ls(self):
        """
        Metodo di debug per vedere se Docker monta correttamente i file.
        Esegue 'ls -R' dentro il container.
        """
        # Sovrascriviamo temporaneamente l'entrypoint per usare 'ls' invece di 'terraform'
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.working_dir}:/workspace",
            "-w", "/workspace",
            "--entrypoint", "sh", # Usiamo shell
            self.docker_image,
            "-c", "ls -R" # Comando ricorsivo
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.stdout
        except Exception as e:
            return str(e)

    def get_outputs(self):
            """
            Esegue 'terraform output -json' per recuperare IP e dati utili.
            Restituisce un dizionario Python pulito.
            """
            success, stdout = self._run_docker_command(["output", "-json"])
            
            if success and stdout:
                try:
                    # Terraform restituisce un JSON tipo:
                    # { "ec2_public_ips": { "sensitive": false, "type": "list", "value": ["1.2.3.4"] } }
                    raw_data = json.loads(stdout)
                    
                    # Puliamo il dizionario per restituire solo i valori
                    clean_data = {key: val['value'] for key, val in raw_data.items()}
                    return clean_data
                except json.JSONDecodeError:
                    return None
            return None
        
    def estimate_cost(self, api_key):
            """
            Esegue Infracost tramite Docker e pulisce l'output dai log per estrarre il JSON.
            """
            try:
                print("💰 Avvio stima costi con Infracost...")
                client = docker.from_env()
                
                # Lanciamo il container
                raw_bytes = client.containers.run(
                    image="infracost/infracost:latest",
                    command="breakdown --path /code --format json",
                    volumes={
                        self.working_dir: {'bind': '/code', 'mode': 'rw'}
                    },
                    environment={
                        "INFRACOST_API_KEY": api_key,
                        "INFRACOST_SKIP_UPDATE_CHECK": "true"
                    },
                    remove=True,
                    stderr=True 
                )
                
                # Decodifica l'output completo (Log + JSON)
                full_output = raw_bytes.decode('utf-8').strip()
                
                # --- LOGICA DI PULIZIA ---
                # Cerchiamo dove inizia il vero JSON (la prima parentesi graffa aperta)
                json_start_index = full_output.find('{')
                
                if json_start_index == -1:
                    return False, f"Errore: Nessun JSON trovato nell'output.\nOutput grezzo: {full_output}"
                
                # Prendiamo tutto da quella parentesi in poi
                json_str = full_output[json_start_index:]
                
                try:
                    output_json = json.loads(json_str)
                    return True, output_json
                except json.JSONDecodeError as e:
                    return False, f"Errore nel parsing del JSON estratto: {e}"
                
            except docker.errors.ImageNotFound:
                return False, "Immagine Docker 'infracost/infracost' non trovata. Il download potrebbe richiedere tempo."
            except docker.errors.ContainerError as e:
                return False, f"Il container è andato in errore: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
            except Exception as e:
                return False, f"Errore generico Python: {str(e)}"
        
    def init(self):
        return self._run_docker_command(["init"])

    def validate(self):
        return self._run_docker_command(["validate"])

    def plan(self):
        return self._run_docker_command(["plan", "-no-color"])
    
    def apply(self):
        # -auto-approve evita che Terraform chieda "sei sicuro?" (che bloccherebbe Docker)
        return self._run_docker_command(["apply", "-auto-approve", "-no-color"])

    def destroy(self):
        # Distrugge tutto senza chiedere conferma
        return self._run_docker_command(["destroy", "-auto-approve", "-no-color"])