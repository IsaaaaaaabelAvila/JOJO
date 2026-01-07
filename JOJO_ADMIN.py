"""
SISTEMA INTEGRAL DE VENTAS E INVENTARIO - IMPRESIÓN 3D
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import uuid
from dotenv import load_dotenv
import os
import psycopg2

#python -m streamlit run JOJO_ADMIN.py

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================

st.set_page_config(
    page_title="Sistema de Ventas - Impresión 3D",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("JOJO 3D LAB")

# ============================================
# INICIALIZAR SESSION STATE
# ============================================

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

if 'venta_exitosa' not in st.session_state:
    st.session_state.venta_exitosa = False

# ============================================
# SIDEBAR - NAVEGACIÓN
# ============================================

st.sidebar.title("🛒 Sistema de Ventas")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegación Principal",
    ["🏠 Dashboard",
     "💰 Nueva Venta",
     "📋 Historial de Ventas",
     "📦 Inventario",
     "📊 Reportes",
     "➕ Agregar Producto"]
)

@st.cache_resource
def init_connection():
    # Load environment variables from .env
    load_dotenv()

    # Fetch variables
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    # Connect to the database
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect: {e}")
a = init_connection()

icon_container = st.container()
with icon_container:
    cols = st.columns(4)
    
    with cols[0]:
        st.page_link("pages/➕ Agregar Nuevo Producto.py", label="New Product", icon="➕", 
                    help="Agregar nuevo producto")