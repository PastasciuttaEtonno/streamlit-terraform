from pydantic import BaseModel, field_validator, Field
import re
from typing import List, Literal, Union, Optional

# ==========================================
#               AWS MODELS
# ==========================================

class AWSNetworkConfig(BaseModel):
    vpc_cidr: str
    az_count: int
    public_subnet_count: int
    private_subnet_count: int

    @field_validator('vpc_cidr')
    def validate_cidr(cls, v):
        cidr_pattern = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$')
        if not cidr_pattern.match(v):
            raise ValueError('Formato CIDR non valido. Esempio corretto: 10.0.0.0/16')
        return v

class AWSEC2Config(BaseModel):
    instance_type: str
    instance_count: int
    ami_id: str
    subnet_type: str
    key_name: str
    allowed_ports: List[int]
    disk_size: int
    disk_type: str
    user_data_script: str

class AWSALBConfig(BaseModel):
    enabled: bool = False
    name: str = "my-alb"
    ingress_port: int = 80
    action_type: str = "forward"
    redirect_protocol: str = "HTTPS"
    redirect_port: str = "443"
    redirect_status_code: str = "HTTP_301"
    fixed_response_body: str = "Sito in manutenzione"
    fixed_response_code: str = "503"
    fixed_response_content_type: str = "text/plain"

class AWSRDSConfig(BaseModel):
    enabled: bool = False
    identifier: str = "my-app-db"
    engine: str = "mysql"
    instance_class: str = "db.t3.micro"
    allocated_storage: int = 20
    username: str = "adminuser"
    password: str = "ChangeMe123!"
    db_name: str = "appdb"

class AWSProjectConfig(BaseModel):
    provider: Literal["aws"] = "aws"
    project_name: str
    region: str
    network: AWSNetworkConfig
    ec2: AWSEC2Config
    alb: AWSALBConfig = AWSALBConfig()
    rds: AWSRDSConfig = AWSRDSConfig()


# ==========================================
#               GCP MODELS
# ==========================================

class GCPNetworkConfig(BaseModel):
    subnet_cidr: str = "10.0.1.0/24"
    # GCP networks are global, subnets are regional.
    # Simplifying for MVP.

class GCPComputeConfig(BaseModel):
    machine_type: str = "e2-medium"
    instance_count: int = 1
    image_family: str = "debian-11"
    image_project: str = "debian-cloud"
    zone: str = "us-central1-a"
    tags: List[str] = ["http-server", "https-server"]
    subnet_type: Literal["public", "private"] = "public"

class GCPProjectConfig(BaseModel):
    provider: Literal["gcp"] = "gcp"
    project_name: str
    gcp_project_id: str # ID univoco del progetto GCP
    region: str = "us-central1"
    network: GCPNetworkConfig = GCPNetworkConfig()
    compute: GCPComputeConfig = GCPComputeConfig()

# ==========================================
#             GLOBAL CONFIG
# ==========================================

# This Union allows the UI to instantiate the correct class based on logic
# or holding a generic reference.
ProjectConfig = Union[AWSProjectConfig, GCPProjectConfig]