import streamlit as st
from core.models import ProjectConfig, NetworkConfig, EC2Config

def initialize_session_state():
    """
    Controlla se lo stato esiste. Se no, lo crea con i default.
    Da chiamare all'inizio di OGNI pagina.
    """
    if "project_config" not in st.session_state:
        st.session_state.project_config = ProjectConfig(
            project_name="MyTerraformProject",
            region="us-east-1",
            network=NetworkConfig(
                vpc_cidr="10.0.0.0/16",
                az_count=1,               # Default: 2 AZ
                public_subnet_count=1,    # Default: 2 Public
                private_subnet_count=1    # Default: 2 Private
            ),
            ec2=EC2Config(
                instance_type="t3.micro",
                instance_count=1,
                ami_id="ami-0c7217cdde317cfec",
                subnet_type="public",
                
                key_name="",
                allowed_ports=[22, 80], # Di base apriamo SSH e HTTP
                disk_size=8,           # 20 GB
                disk_type="gp3",        # General Purpose SSD (il nuovo standard)
                user_data_script="#!/bin/bash\necho 'Hello from Terraform' > /var/www/html/index.html"
                
            )
        )