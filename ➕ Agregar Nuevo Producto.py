import streamlit as st
from utils.functions import obtener_siguiente_product_id, agregar_producto

st.title("➕ Agregar Nuevo Producto")

siguiente_id = obtener_siguiente_product_id()

with st.form("form_nuevo_producto"):
    col1, col2 = st.columns(2)
        
    with col1:
        product_id = st.text_input("Código del Producto (SKU) *", value=siguiente_id,disabled=True)
        name = st.text_input("Nombre del Producto *", placeholder="Ej: Figura Batman 15cm")
        category = st.selectbox("Categoría*",["Figuras", "Fidgets", "Decoración", "Llaveros", "Otro"])
        
    with col2:
        price = st.number_input("Precio de Venta *", min_value=0.0, step=1.0)
        cost = st.number_input("Costo de Producción", min_value=0.0, step=1.0)
        stock_quantity = st.number_input("Stock Inicial *", min_value=0, value=0)
        stock_min = st.number_input("Stock Mínimo", min_value=0, value=5)
        
        #image_url = st.text_input("URL de Imagen (Opcional)",placeholder="https://ejemplo.com/imagen.jpg")
        
    submitted = st.form_submit_button("✅ Agregar Producto", type="primary", use_container_width=True)
        
    if submitted:
        if product_id and name and price > 0:
            product_data = {
                "product_id": product_id,
                "name": name,
                "category": category,
                "price": float(price),
                "cost": float(cost),
                "stock_quantity": stock_quantity,
                "stock_min": stock_min,
                #"image_url": image_url if image_url else None,
                "is_active": True
            }
                
            success, message = agregar_producto(product_data)
                
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ Error: {message}")
        else:
            st.error("⚠️ Por favor completa todos los campos obligatorios (*)")