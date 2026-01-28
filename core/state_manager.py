import streamlit as st
from core.models import (
    ProjectConfig, 
    AWSProjectConfig, 
    AWSNetworkConfig, 
    AWSEC2Config, 
    AWSALBConfig, 
    AWSRDSConfig,
    AWSALBConfig, 
    AWSRDSConfig,
    GCPProjectConfig,
    SecurityGroupRule
)

def initialize_session_state():
    """
    Controlla se lo stato esiste. Se no, lo crea con i default (AWS).
    Da chiamare all'inizio di OGNI pagina.
    """
    if "project_config" not in st.session_state:
        # Default initialize to AWS
        st.session_state.project_config = AWSProjectConfig(
            project_name="MyTerraformProject",
            region="us-east-1",
            network=AWSNetworkConfig(
                vpc_cidr="10.0.0.0/16",
                az_count=1,               # Default: 2 AZ
                public_subnet_count=1,    # Default: 2 Public
                private_subnet_count=1    # Default: 2 Private
            ),
            ec2=AWSEC2Config(
                instance_type="t3.micro",
                instance_count=1,
                ami_id="ami-0c7217cdde317cfec",
                subnet_type="public",
                
                key_name="",
                security_group_rules=[
                    SecurityGroupRule(direction="ingress", from_port=22, to_port=22, protocol="tcp", cidr_blocks=["0.0.0.0/0"]),
                    SecurityGroupRule(direction="ingress", from_port=80, to_port=80, protocol="tcp", cidr_blocks=["0.0.0.0/0"])
                ], 
                # allowed_ports=[22, 80], # Di base apriamo SSH e HTTP
                disk_size=8,           # 20 GB
                disk_type="gp3",        # General Purpose SSD (il nuovo standard)
                user_data_script="#!/bin/bash\necho 'Hello from Terraform' > /var/www/html/index.html"
            ),
            alb=AWSALBConfig(enabled=False, name="app-load-balancer", ingress_port=80),
            rds=AWSRDSConfig()
        )
    
    # --- State Migration / Hotfix ---
    # Rimuoviamo la patch per RDS se non necessaria o aggiorniamola per AWS
    if hasattr(st.session_state, 'project_config'):
        config = st.session_state.project_config
        # Controllo provider per evitare errori su GCP config che non ha RDS
        if config.provider == "aws" and not hasattr(config, 'rds'):
             config.rds = AWSRDSConfig()