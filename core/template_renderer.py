import os
import shutil
from jinja2 import Environment, FileSystemLoader

class TerraformRenderer:
    def __init__(self, template_dir: str, output_dir: str):
        self.template_dir = os.path.abspath(template_dir)
        self.output_dir = os.path.abspath(output_dir)
        
        # Debug paths
        print(f"🔧 Init Renderer:")
        print(f"   Template Dir: {self.template_dir}")
        print(f"   Output Dir:   {self.output_dir}")
        
        if not os.path.exists(self.template_dir):
            raise FileNotFoundError(f"❌ Errore critico: La cartella template non esiste: {self.template_dir}")

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

    def _clean_output(self):
            """
            Pulisce la cartella di output preservando la cache di Terraform (.terraform).
            """
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
                return

            print(f"🧹 Pulizia output in corso (preservando .terraform)...")

            # Itera su tutti i file/cartelle in output
            for item in os.listdir(self.output_dir):
                # Questo evita l'errore WinError 32 e velocizza i run successivi.
                if item in [".terraform", ".terraform.lock.hcl"]:
                    continue
                
                item_path = os.path.join(self.output_dir, item)
                
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path) # Cancella file
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path) # Cancella cartelle (es. modules)
                except Exception as e:
                    print(f"⚠️ Warning: impossibile cancellare {item}: {e}")
                
    def _copy_static_modules(self):
        """Copia i moduli e lancia errore se non li trova"""
        src_modules = os.path.join(self.template_dir, "modules")
        dst_modules = os.path.join(self.output_dir, "modules")
        
        print(f"📂 Cerco moduli in: {src_modules}")
        
        if os.path.exists(src_modules):
            # shutil.copytree richiede che la destinazione NON esista
            if os.path.exists(dst_modules):
                shutil.rmtree(dst_modules)
            shutil.copytree(src_modules, dst_modules)
            print(f"✅ Moduli copiati correttamente in: {dst_modules}")
        else:
            # Qui è dove probabilmente falliva prima silenziosamente
            raise FileNotFoundError(f"❌ ERRORE: Non trovo la cartella 'modules' in {src_modules}. Controlla la struttura del progetto!")

    def render_root(self, context: dict):
        self._clean_output()
        self._copy_static_modules() # <--- Ora questa chiamata è sorvegliata

        root_template_path = os.path.join(self.template_dir, "root")
        if not os.path.exists(root_template_path):
             raise FileNotFoundError(f"❌ Errore: Manca la cartella 'root' dentro templates!")

        for filename in os.listdir(root_template_path):
            src_path = os.path.join(root_template_path, filename)
            
            if filename.endswith(".j2"):
                template_name = f"root/{filename}"
                template = self.env.get_template(template_name)
                content = template.render(context)
                
                final_filename = filename.replace(".j2", "")
                dst_path = os.path.join(self.output_dir, final_filename)
                
                with open(dst_path, "w") as f:
                    f.write(content)

            elif filename.endswith(".tf"):
                dst_path = os.path.join(self.output_dir, filename)
                shutil.copy(src_path, dst_path)