import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import sys
import os
import math

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.state_manager import initialize_session_state
from core.auth_sidebar import render_auth_sidebar

# --- INIT ---
st.set_page_config(layout="wide", page_title="AWS Topology")
initialize_session_state()
render_auth_sidebar()

st.title("7. AWS Infrastructure Topology")
st.info("Visualizzazione Clean: Nomi dei container rimossi per evitare sovrapposizioni con le istanze.")

# Recupero configurazioni
config = st.session_state.project_config
net_config = config.network
ec2_config = config.ec2
alb_config = config.alb
rds_config = config.rds

# ==================== CONFIGURAZIONE PYVIS ====================
net = Network(height="900px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
net.toggle_physics(False)

# ==================== FUNZIONI DI DISEGNO ====================

def add_box(id_name, label, x, y, w, h, color, border="#999999"):
    """
    Disegna un container. 
    Se label è vuota/None, rendiamo il testo TRASPARENTE per evitare che appaia l'ID (es. PUB_1).
    """
    if not label:
        # TRUCCO: Font dimensione 0 e colore trasparente
        font_settings = {"size": 0, "color": "rgba(0,0,0,0)"} 
        final_label = " " # Spazio vuoto per evitare fallback su ID
    else:
        font_settings = {"size": 14, "vadjust": (h/2) - 20, "color": "#555555"}
        final_label = label
    
    net.add_node(
        id_name,
        label=final_label,
        shape="box",
        x=x,
        y=y,
        fixed=True,
        physics=False,
        color={'background': color, 'border': border},
        widthConstraint=w,
        heightConstraint=h,
        font=font_settings, 
        borderWidth=2,
        shapeProperties={"borderRadius": 0} 
    )

def add_text_node(id_name, text, x, y, size=18, color="#333333"):
    """Nodo di testo puro (per le etichette sotto i box)"""
    net.add_node(
        id_name, label=text, shape="text", x=x, y=y, fixed=True, physics=False,
        font={"size": size, "color": color, "face": "verdana"}
    )

def add_icon(id_name, label, x, y, shape, color, size=30, label_offset=40):
    net.add_node(
        id_name, label=label, shape=shape, x=x, y=y, fixed=True, physics=False,
        color=color, size=size,
        font={"size": 14, "color": "black", "vadjust": label_offset}
    )

def add_link(src, dst, label="", color="black", dashed=False, show_arrow=True):
    arrows_config = {'to': {'enabled': show_arrow, 'scaleFactor': 0.5}}
    net.add_edge(src, dst, label=label, color=color, dashes=dashed, arrows=arrows_config)


# ==================== CALCOLO DINAMICO ALTEZZA ====================
num_public_zones = min(net_config.public_subnet_count, 3)
num_private_zones = min(net_config.private_subnet_count, 6)
has_private = net_config.private_subnet_count > 0

if ec2_config.subnet_type == "public":
    active_zones = num_public_zones
else:
    active_zones = num_private_zones if has_private else num_public_zones

# Calcolo altezza necessaria
max_instances_in_column = math.ceil(ec2_config.instance_count / max(1, active_zones))
PIXELS_PER_INSTANCE = 110
BASE_PADDING = 300 
RDS_SPACE = 100 if rds_config.enabled else 0

calculated_content_height = (max_instances_in_column * PIXELS_PER_INSTANCE) + BASE_PADDING + RDS_SPACE

DYNAMIC_VPC_H = max(650, calculated_content_height)
DYNAMIC_SUBNET_H = DYNAMIC_VPC_H - 120 

# ==================== LAYOUT DISEGNO ====================

CENTER_X, CENTER_Y = 0, 0
VPC_W = 1400 

# 1. VPC Box (Label vuota -> Trasparente)
add_box("VPC", "", CENTER_X, CENTER_Y, VPC_W, DYNAMIC_VPC_H, "#F5F7FA")

# 2. Etichetta VPC Sotto
VPC_LABEL_Y = CENTER_Y + (DYNAMIC_VPC_H / 2) + 40 
add_text_node("VPC_LABEL", f"VPC Network: {net_config.vpc_cidr}", CENTER_X, VPC_LABEL_Y, size=24)

AREA_PUB_WIDTH = 400
AREA_PUB_CENTER_X = -450 
AREA_PRIV_WIDTH = 800 
AREA_PRIV_CENTER_X = 250 

# --- GENERATORE SUBNET ---
def generate_n_subnets(prefix, count, center_x, center_y, max_width, h, color, border_color, label_base):
    box_ids = []
    coords_x = []
    gap = 15 
    total_gaps_width = gap * (count - 1) if count > 1 else 0
    calculated_w = (max_width - total_gaps_width) / count
    single_box_w = min(calculated_w, 350) 
    
    actual_total_width = (single_box_w * count) + total_gaps_width
    start_x = center_x - (actual_total_width / 2) + (single_box_w / 2)
    
    for i in range(count):
        current_x = start_x + (i * (single_box_w + gap))
        box_id = f"{prefix}_{i+1}"
        az_letter = chr(65 + i) 
        
        # 1. Box Sfondo: Passiamo stringa vuota ""
        # La funzione add_box ora renderà il testo TRASPARENTE e INVISIBILE
        add_box(box_id, "", current_x, center_y, single_box_w, h, color, border_color)
        
        # 2. Etichetta Esterna (Sotto)
        label_y = center_y + (h / 2) + 25
        label_text = f"{label_base}\n(Zone {az_letter})"
        add_text_node(f"{box_id}_LBL", label_text, current_x, label_y, size=16, color="#555555")
        
        box_ids.append(box_id)
        coords_x.append(current_x)
    return coords_x

# Disegno Subnets
pub_coords_x = generate_n_subnets(
    "PUB", num_public_zones, AREA_PUB_CENTER_X, CENTER_Y, AREA_PUB_WIDTH, 
    DYNAMIC_SUBNET_H, "#E6FFFA", "#38B2AC", "Public"
)

priv_coords_x = []
if has_private:
    priv_coords_x = generate_n_subnets(
        "PRIV", num_private_zones, AREA_PRIV_CENTER_X, CENTER_Y, AREA_PRIV_WIDTH, 
        DYNAMIC_SUBNET_H, "#FFF5F5", "#F56565", "Private"
    )

# ==================== POSIZIONAMENTO RISORSE ====================

subnet_top_edge = CENTER_Y - (DYNAMIC_SUBNET_H / 2)

# -- INTERNET & GATEWAY --
IGW_X = AREA_PUB_CENTER_X
IGW_Y = subnet_top_edge - 60 
USER_Y = subnet_top_edge - 250 

add_icon("User", "☁️ Internet / Users", IGW_X, USER_Y, "dot", "#E2E8F0", size=50, label_offset=60)
add_icon("IGW", "Internet Gateway", IGW_X, IGW_Y, "triangle", "orange")
add_link("User", "IGW", "Traffico Web", show_arrow=True) 

# -- LOAD BALANCER --
alb_node_id = None
if alb_config.enabled:
    alb_node_id = "ALB"
    alb_y = subnet_top_edge + 80 
    add_icon(alb_node_id, f"ALB\n({alb_config.name})", AREA_PUB_CENTER_X, alb_y, "hexagon", "#63B3ED")
    add_link("IGW", alb_node_id, f"Port {alb_config.ingress_port}", show_arrow=True)


# -- ISTANZE EC2 --
ec2_nodes = []
if ec2_config.subnet_type == "public":
    target_x_coords = pub_coords_x
    box_color = "#F6E05E" 
else:
    target_x_coords = priv_coords_x if has_private else pub_coords_x
    box_color = "#ECC94B"

start_ec2_y = subnet_top_edge + 200 if alb_config.enabled else subnet_top_edge + 100

display_count = min(ec2_config.instance_count, 18) 

for i in range(display_count):
    node_id = f"EC2_{i}"
    label = f"EC2-{i+1}"
    subnet_idx = i % len(target_x_coords)
    target_x_center = target_x_coords[subnet_idx]
    
    same_zone_instances = [k for k in range(i) if k % len(target_x_coords) == subnet_idx]
    
    vertical_shift = len(same_zone_instances) * 110 
    
    final_x = target_x_center
    final_y = start_ec2_y + vertical_shift
    
    add_icon(node_id, label, final_x, final_y, "square", box_color)
    ec2_nodes.append(node_id)

    if alb_config.enabled:
        add_link(alb_node_id, node_id, "", show_arrow=False)
    elif ec2_config.subnet_type == "public":
        add_link("IGW", node_id, "Direct", show_arrow=False)

if ec2_config.instance_count > 18:
    net.add_node("More", label=f"+ more...", x=AREA_PUB_CENTER_X, y=start_ec2_y + vertical_shift + 100, shape="text")


# -- DATABASE RDS --
if rds_config.enabled:
    # Posizione DB relativa al fondo dinamico
    db_y = (CENTER_Y + (DYNAMIC_SUBNET_H / 2)) - 100
    
    if has_private:
        db_x = priv_coords_x[0] 
        add_icon("RDS", f"RDS Primary\n({rds_config.engine})", db_x, db_y, "database", "#4FD1C5", size=35)
        
        if len(priv_coords_x) > 1:
             add_icon("RDS_Rep1", "Replica", priv_coords_x[1], db_y, "database", "#cbd5e0", size=25)
             add_link("RDS", "RDS_Rep1", "Sync", dashed=True, show_arrow=False)
             
        if len(priv_coords_x) > 2:
             add_icon("RDS_Rep2", "Replica", priv_coords_x[2], db_y, "database", "#cbd5e0", size=25)
             add_link("RDS", "RDS_Rep2", "Sync", dashed=True, show_arrow=False)

    else:
        db_x = pub_coords_x[0] 
        add_icon("RDS", f"RDS\n({rds_config.engine})", db_x, db_y, "database", "#4FD1C5", size=35)
    
    for ec2_id in ec2_nodes:
        add_link(ec2_id, "RDS", "", color="gray", dashed=True, show_arrow=False)


# ==================== RENDER ====================
try:
    path = "topology.html"
    net.save_graph(path)
    with open(path, 'r', encoding='utf-8') as f:
        html_string = f.read()
    components.html(html_string, height=DYNAMIC_VPC_H + 250, scrolling=False)
except Exception as e:
    st.error(f"Errore grafico: {e}")

st.divider()
cols = st.columns(3)
cols[0].info(f"**Public Zones:** {len(pub_coords_x)}")
cols[1].error(f"**Private Zones:** {len(priv_coords_x)}")
cols[2].success(f"**EC2 Nodes:** {ec2_config.instance_count}")