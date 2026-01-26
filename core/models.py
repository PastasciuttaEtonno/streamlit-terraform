from pydantic import BaseModel, field_validator
import re
from typing import List

class NetworkConfig(BaseModel):
    vpc_cidr: str
    az_count: int
    public_subnet_count: int
    private_subnet_count: int

    # --- VALIDATORE CIDR ---
    @field_validator('vpc_cidr')
    def validate_cidr(cls, v):
        # Regex standard per IPv4 CIDR
        cidr_pattern = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$')
        if not cidr_pattern.match(v):
            raise ValueError('Formato CIDR non valido. Esempio corretto: 10.0.0.0/16')
        return v

class EC2Config(BaseModel):
    instance_type: str
    instance_count: int
    ami_id: str
    subnet_type: str
    
    key_name: str  # Nome della chiave SSH su AWS
    
    # 1. Network Rules
    allowed_ports: List[int] # Lista di porte da aprire (es. [22, 80])
    
    # 2. Storage
    disk_size: int           # Dimensione in GB
    disk_type: str           # Tipo disco (gp3, io1, standard)
    
    # 3. User Data
    user_data_script: str    # Script Bash di avvio
    
class ALBConfig(BaseModel):
    enabled: bool = False
    name: str = "my-alb"
    ingress_port: int = 80
    
    # Opzioni: "forward", "redirect", "fixed-response"
    action_type: str = "forward" 
    
    # Parametri per Redirect
    redirect_protocol: str = "HTTPS"
    redirect_port: str = "443"
    redirect_status_code: str = "HTTP_301" 
    
    # Parametri per Fixed Response
    fixed_response_body: str = "Sito in manutenzione"
    fixed_response_code: str = "503"
    fixed_response_content_type: str = "text/plain"

class RDSConfig(BaseModel):
    enabled: bool = False
    identifier: str = "my-app-db"
    engine: str = "mysql" # mysql o postgres
    instance_class: str = "db.t3.micro"
    allocated_storage: int = 20 # GB
    username: str = "adminuser"
    password: str = "ChangeMe123!" # In produzione useremmo Secrets Manager!
    db_name: str = "appdb"

class ProjectConfig(BaseModel):
    project_name: str
    region: str
    network: NetworkConfig
    ec2: EC2Config
    # Aggiungi il nuovo campo inizializzato di default
    alb: ALBConfig = ALBConfig()
    rds: RDSConfig = RDSConfig()