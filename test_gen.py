# test_gen.py
import os
from core.models import ProjectConfig, NetworkConfig, EC2Config
from core.template_renderer import TerraformRenderer
from rich import print # Usiamo rich come da requirements!

def run_test():
    # 1. Definiamo i percorsi
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    print(f"[bold blue]🚀 Inizio test generazione Terraform...[/bold blue]")
    print(f"📂 Template dir: {TEMPLATE_DIR}")
    print(f"📂 Output dir:   {OUTPUT_DIR}")

    # 2. Simuliamo i dati che arriverebbero da Streamlit
    # Creiamo un oggetto di configurazione completo
    mock_data = ProjectConfig(
        project_name="DemoProject",
        region="us-east-1",
        network=NetworkConfig(
            vpc_cidr="10.0.0.0/16",
            public_subnet_cidr="10.0.1.0/24",
            private_subnet_cidr="10.0.2.0/24"
        ),
        ec2=EC2Config(
            instance_type="t3.micro",
            instance_count=2,
            # Un AMI ID di esempio (Ubuntu in us-east-1)
            ami_id="ami-0c7217cdde317cfec" 
        )
    )

    print("\n[bold green]✅ Modello dati creato con successo:[/bold green]")
    print(mock_data.model_dump_json(indent=2))

    # 3. Inizializziamo il Renderer
    try:
        renderer = TerraformRenderer(TEMPLATE_DIR, OUTPUT_DIR)
        
        # 4. Generiamo i file
        # Nota: passiamo mock_data.model_dump() che converte l'oggetto Pydantic in dizionario
        renderer.render_root(mock_data.model_dump())
        
        print("\n[bold yellow]✨ Generazione completata! Controlla la cartella /output[/bold yellow]")
        
    except Exception as e:
        print(f"\n[bold red]❌ Errore durante il rendering:[/bold red] {e}")

if __name__ == "__main__":
    run_test()