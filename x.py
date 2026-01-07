"""
SISTEMA INTEGRAL DE VENTAS E INVENTARIO - IMPRESIÓN 3D
Interfaz completa con Streamlit + Supabase

INSTALACIÓN:
pip install streamlit supabase pandas plotly

CONFIGURACIÓN:
Crea el archivo .streamlit/secrets.toml con:
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-service-role-key"

EJECUCIÓN:
streamlit run sales_system.py
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import uuid

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

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Usa atajos de teclado para navegar más rápido")

# ============================================
# PÁGINA: DASHBOARD
# ============================================

if page == "🏠 Dashboard":
    st.title("📊 Dashboard General")
    
    # Métricas principales del día
    col1, col2, col3, col4 = st.columns(4)
    
    # Ventas del día
    try:
        hoy = datetime.now().date()
        ventas_hoy = supabase.table("ventas").select("*").gte(
            "date", hoy.isoformat()
        ).execute()
        
        df_ventas_hoy = pd.DataFrame(ventas_hoy.data) if ventas_hoy.data else pd.DataFrame()
        
        with col1:
            total_dia = df_ventas_hoy['total'].sum() if not df_ventas_hoy.empty else 0
            st.metric("💵 Ventas Hoy", f"${total_dia:,.2f}")
        
        with col2:
            num_tickets = df_ventas_hoy['ticket_id'].nunique() if not df_ventas_hoy.empty else 0
            st.metric("🎫 Tickets Hoy", num_tickets)
        
        with col3:
            productos_vendidos = df_ventas_hoy['qty'].sum() if not df_ventas_hoy.empty else 0
            st.metric("📦 Productos Vendidos", int(productos_vendidos))
        
        with col4:
            ticket_promedio = total_dia / num_tickets if num_tickets > 0 else 0
            st.metric("🧾 Ticket Promedio", f"${ticket_promedio:,.2f}")
        
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Ventas de los últimos 7 días")
        try:
            fecha_inicio = (datetime.now() - timedelta(days=7)).date()
            ventas_semana = supabase.table("ventas").select("*").gte(
                "date", fecha_inicio.isoformat()
            ).execute()
            
            if ventas_semana.data:
                df_semana = pd.DataFrame(ventas_semana.data)
                df_semana['date'] = pd.to_datetime(df_semana['date']).dt.date
                ventas_por_dia = df_semana.groupby('date')['total'].sum().reset_index()
                
                fig = px.bar(ventas_por_dia, x='date', y='total',
                           labels={'date': 'Fecha', 'total': 'Ventas ($)'},
                           color='total',
                           color_continuous_scale='Blues')
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay ventas en los últimos 7 días")
        except Exception as e:
            st.error(f"Error al cargar gráfico: {e}")
    
    with col2:
        st.subheader("🏆 Top 5 Productos Más Vendidos")
        try:
            top_productos = supabase.table("v_productos_mas_vendidos").select("*").limit(5).execute()
            
            if top_productos.data:
                df_top = pd.DataFrame(top_productos.data)
                fig = px.bar(df_top, x='name', y='total_vendido',
                           labels={'name': 'Producto', 'total_vendido': 'Cantidad Vendida'},
                           color='total_vendido',
                           color_continuous_scale='Greens')
                fig.update_layout(showlegend=False, height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de productos vendidos")
        except Exception as e:
            st.error(f"Error al cargar top productos: {e}")
    
    # Alertas de inventario
    st.markdown("---")
    st.subheader("⚠️ Alertas de Inventario")
    
    try:
        alertas = supabase.table("v_inventario_alertas").select("*").in_(
            "alerta_stock", ["Sin Stock", "Crítico", "Bajo"]
        ).execute()
        
        if alertas.data:
            df_alertas = pd.DataFrame(alertas.data)
            
            for _, item in df_alertas.iterrows():
                if item['alerta_stock'] == 'Sin Stock':
                    st.error(f"🔴 **{item['name']}** - Sin stock disponible")
                elif item['alerta_stock'] == 'Crítico':
                    st.warning(f"🟠 **{item['name']}** - Stock crítico: {item['stock_quantity']} unidades")
                else:
                    st.info(f"🟡 **{item['name']}** - Stock bajo: {item['stock_quantity']} unidades")
        else:
            st.success("✅ No hay alertas de inventario")
    except Exception as e:
        st.error(f"Error al cargar alertas: {e}")

# ============================================
# PÁGINA: NUEVA VENTA
# ============================================

elif page == "💰 Nueva Venta":
    st.title("💰 Registrar Nueva Venta")
    
    # Mostrar mensaje de éxito si existe
    if st.session_state.venta_exitosa:
        st.success("✅ ¡Venta registrada exitosamente!")
        st.session_state.venta_exitosa = False
    
    # Cargar productos
    productos_df = get_productos_activos()
    
    if productos_df.empty:
        st.warning("⚠️ No hay productos disponibles. Por favor, agrega productos primero.")
        st.stop()
    
    # Sección 1: Buscar y agregar productos al carrito
    st.subheader("🔍 Buscar Productos")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Búsqueda de producto
        busqueda = st.text_input("Buscar por nombre o código", 
                                 placeholder="Escribe el nombre o código del producto...")
        
        if busqueda:
            productos_filtrados = productos_df[
                productos_df['name'].str.contains(busqueda, case=False, na=False) |
                productos_df['product_id'].str.contains(busqueda, case=False, na=False)
            ]
        else:
            productos_filtrados = productos_df.head(10)
    
    with col2:
        categoria_filtro = st.selectbox(
            "Filtrar por categoría",
            ["Todas"] + sorted(productos_df['category'].dropna().unique().tolist())
        )
        
        if categoria_filtro != "Todas":
            productos_filtrados = productos_df[productos_df['category'] == categoria_filtro]
    
    # Mostrar productos disponibles
    st.markdown("---")
    st.subheader("📦 Productos Disponibles")
    
    # Crear columnas para mostrar productos como tarjetas
    num_cols = 3
    productos_mostrar = productos_filtrados.head(12)
    
    for i in range(0, len(productos_mostrar), num_cols):
        cols = st.columns(num_cols)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(productos_mostrar):
                producto = productos_mostrar.iloc[idx]
                
                with col:
                    with st.container():
                        st.markdown(f"**{producto['name']}**")
                        st.text(f"Código: {producto['product_id']}")
                        st.text(f"Precio: ${producto['price']:,.2f}")
                        
                        # Indicador de stock
                        if producto['stock_quantity'] <= 0:
                            st.error(f"🔴 Sin stock")
                        elif producto['stock_quantity'] <= producto['stock_min']:
                            st.warning(f"🟡 Stock: {producto['stock_quantity']}")
                        else:
                            st.success(f"🟢 Stock: {producto['stock_quantity']}")
                        
                        # Botón para agregar al carrito
                        cantidad = st.number_input(
                            "Cantidad",
                            min_value=1,
                            max_value=int(producto['stock_quantity']) if producto['stock_quantity'] > 0 else 1,
                            value=1,
                            key=f"qty_{producto['product_id']}_{idx}"
                        )
                        
                        if st.button("➕ Agregar", key=f"add_{producto['product_id']}_{idx}",
                                   disabled=producto['stock_quantity'] <= 0):
                            # Agregar al carrito
                            item_carrito = {
                                'product_id': producto['product_id'],
                                'name': producto['name'],
                                'qty': cantidad,
                                'price': float(producto['price']),
                                'subtotal': cantidad * float(producto['price'])
                            }
                            st.session_state.carrito.append(item_carrito)
                            st.rerun()
    
    # Sección 2: Carrito de compras
    st.markdown("---")
    st.subheader("🛒 Carrito de Compras")
    
    if st.session_state.carrito:
        # Mostrar items del carrito
        carrito_df = pd.DataFrame(st.session_state.carrito)
        
        # Agregar columna de acciones
        for idx, item in enumerate(st.session_state.carrito):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.text(item['name'])
            with col2:
                st.text(f"${item['price']:,.2f}")
            with col3:
                st.text(f"{item['qty']}")
            with col4:
                st.text(f"${item['subtotal']:,.2f}")
            with col5:
                if st.button("🗑️", key=f"delete_{idx}"):
                    st.session_state.carrito.pop(idx)
                    st.rerun()
        
        # Calcular totales
        subtotal = sum(item['subtotal'] for item in st.session_state.carrito)
        
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown(f"### Subtotal: ${subtotal:,.2f}")
            st.markdown(f"### **Total: ${subtotal:,.2f}**")
        
        # Sección 3: Información de la venta
        st.markdown("---")
        st.subheader("📝 Información de la Venta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            channel = st.selectbox(
                "Canal de Venta*",
                ["Tienda Física", "Online", "WhatsApp", "Instagram", "Facebook", "Otro"]
            )
            
            payment_method = st.selectbox(
                "Método de Pago*",
                ["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia", 
                 "PayPal", "Mercado Pago", "Otro"]
            )
        
        with col2:
            # Información del cliente (opcional)
            with st.expander("👤 Información del Cliente (Opcional)"):
                customer_name = st.text_input("Nombre del cliente")
                customer_phone = st.text_input("Teléfono")
                customer_email = st.text_input("Email")
        
        notas = st.text_area("Notas adicionales (opcional)")
        
        # Botones de acción
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🗑️ Vaciar Carrito", type="secondary", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        
        with col2:
            if st.button("✅ COMPLETAR VENTA", type="primary", use_container_width=True):
                # Preparar información del cliente
                customer_info = None
                if customer_name or customer_phone or customer_email:
                    customer_info = {
                        'name': customer_name,
                        'phone': customer_phone,
                        'email': customer_email
                    }
                
                # Registrar la venta
                success, result, total = registrar_venta(
                    st.session_state.carrito,
                    channel,
                    payment_method,
                    customer_info
                )
                
                if success:
                    st.session_state.carrito = []
                    st.session_state.venta_exitosa = True
                    
                    # Mostrar ticket
                    st.balloons()
                    st.success(f"✅ Venta completada exitosamente!")
                    st.info(f"🎫 Ticket ID: **{result}**")
                    st.info(f"💰 Total: **${total:,.2f}**")
                    
                    # Esperar 2 segundos y recargar
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Error al registrar la venta: {result}")
    
    else:
        st.info("🛒 El carrito está vacío. Agrega productos para continuar.")

# ============================================
# PÁGINA: HISTORIAL DE VENTAS
# ============================================

elif page == "📋 Historial de Ventas":
    st.title("📋 Historial de Ventas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=30))
    
    with col2:
        fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
    
    with col3:
        canal_filtro = st.selectbox("Canal", ["Todos", "Tienda Física", "Online", "WhatsApp", "Instagram"])
    
    # Cargar tickets
    try:
        query = supabase.table("v_tickets_resumen").select("*").gte(
            "date", fecha_desde.isoformat()
        ).lte("date", fecha_hasta.isoformat())
        
        tickets = query.execute()
        
        if tickets.data:
            df_tickets = pd.DataFrame(tickets.data)
            df_tickets['date'] = pd.to_datetime(df_tickets['date']).dt.strftime('%Y-%m-%d %H:%M')
            
            if canal_filtro != "Todos":
                df_tickets = df_tickets[df_tickets['channel'] == canal_filtro]
            
            # Mostrar resumen
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Tickets", len(df_tickets))
            with col2:
                st.metric("Venta Total", f"${df_tickets['total'].sum():,.2f}")
            with col3:
                st.metric("Ticket Promedio", f"${df_tickets['total'].mean():,.2f}")
            
            st.markdown("---")
            
            # Tabla de tickets
            st.dataframe(
                df_tickets[['ticket_id', 'date', 'customer_name', 'total', 
                           'channel', 'payment_method', 'payment_status']],
                use_container_width=True,
                hide_index=True
            )
            
            # Detalle de ticket seleccionado
            st.markdown("---")
            st.subheader("🔍 Ver Detalle de Ticket")
            
            ticket_seleccionado = st.selectbox(
                "Selecciona un ticket",
                df_tickets['ticket_id'].tolist()
            )
            
            if ticket_seleccionado:
                # Cargar detalle
                detalle = supabase.table("ventas").select("*").eq(
                    "ticket_id", ticket_seleccionado
                ).execute()
                
                if detalle.data:
                    df_detalle = pd.DataFrame(detalle.data)
                    st.dataframe(
                        df_detalle[['product_id', 'name', 'qty', 'price', 'total']],
                        use_container_width=True,
                        hide_index=True
                    )
        else:
            st.info("No hay ventas en el período seleccionado")
    
    except Exception as e:
        st.error(f"Error al cargar historial: {e}")

# ============================================
# PÁGINA: INVENTARIO
# ============================================

elif page == "📦 Inventario":
    st.title("📦 Gestión de Inventario")
    
    tab1, tab2, tab3 = st.tabs(["Ver Inventario", "Ajustar Stock", "Movimientos"])
    
    with tab1:
        st.subheader("📊 Inventario Actual")
        
        try:
            inventario = supabase.table("v_inventario_alertas").select("*").execute()
            
            if inventario.data:
                df_inventario = pd.DataFrame(inventario.data)
                
                # Filtros
                col1, col2 = st.columns(2)
                
                with col1:
                    categoria_filtro = st.multiselect(
                        "Filtrar por categoría",
                        df_inventario['category'].dropna().unique().tolist()
                    )
                
                with col2:
                    alerta_filtro = st.multiselect(
                        "Filtrar por alerta",
                        ['Normal', 'Bajo', 'Crítico', 'Sin Stock']
                    )
                
                # Aplicar filtros
                df_filtrado = df_inventario.copy()
                if categoria_filtro:
                    df_filtrado = df_filtrado[df_filtrado['category'].isin(categoria_filtro)]
                if alerta_filtro:
                    df_filtrado = df_filtrado[df_filtrado['alerta_stock'].isin(alerta_filtro)]
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Productos", len(df_filtrado))
                with col2:
                    valor_total = df_filtrado['valor_costo_stock'].sum()
                    st.metric("Valor Inventario (Costo)", f"${valor_total:,.2f}")
                with col3:
                    valor_precio = df_filtrado['valor_precio_stock'].sum()
                    st.metric("Valor Inventario (Precio)", f"${valor_precio:,.2f}")
                
                # Tabla
                st.dataframe(
                    df_filtrado[['product_id', 'name', 'category', 'stock_quantity', 
                               'stock_min', 'price', 'alerta_stock']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay productos en el inventario")
        
        except Exception as e:
            st.error(f"Error al cargar inventario: {e}")
    
    with tab2:
        st.subheader("⚙️ Ajustar Stock Manualmente")
        
        productos_df = get_productos_activos()
        
        if not productos_df.empty:
            producto_seleccionado = st.selectbox(
                "Selecciona un producto",
                productos_df['product_id'].tolist(),
                format_func=lambda x: f"{x} - {productos_df[productos_df['product_id']==x]['name'].iloc[0]}"
            )
            
            if producto_seleccionado:
                producto = get_producto_by_id(producto_seleccionado)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Stock Actual:** {producto['stock_quantity']} unidades")
                
                with col2:
                    nuevo_stock = st.number_input(
                        "Nuevo Stock",
                        min_value=0,
                        value=int(producto['stock_quantity'])
                    )
                
                motivo = st.text_area("Motivo del ajuste", placeholder="Ej: Inventario físico, producto dañado, etc.")
                
                if st.button("✅ Actualizar Stock", type="primary"):
                    if motivo:
                        success, message = actualizar_stock_manual(producto_seleccionado, nuevo_stock, motivo)
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(f"Error: {message}")
                    else:
                        st.warning("Por favor indica el motivo del ajuste")
    
    with tab3:
        st.subheader("📜 Historial de Movimientos")
        
        try:
            movimientos = supabase.table("movimientos_inventario").select("*").order(
                "created_at", desc=True
            ).limit(100).execute()
            
            if movimientos.data:
                df_movimientos = pd.DataFrame(movimientos.data)
                df_movimientos['created_at'] = pd.to_datetime(df_movimientos['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    df_movimientos[['created_at', 'product_id', 'tipo', 'cantidad', 
                                  'stock_anterior', 'stock_nuevo', 'referencia', 'motivo']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay movimientos registrados")
        
        except Exception as