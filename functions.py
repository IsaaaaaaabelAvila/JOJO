import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
from typing import List, Dict
import uuid


# ============================================
# FUNCIONES DE BASE DE DATOS
# ============================================

def get_productos_activos():
    """Obtiene todos los productos activos"""
    try:
        response = supabase.table("productos").select("*").eq("is_active", True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")
        return pd.DataFrame()

def get_producto_by_id(product_id):
    """Obtiene un producto específico por su ID"""
    try:
        response = supabase.table("productos").select("*").eq("product_id", product_id).single().execute()
        return response.data
    except:
        return None

def generar_ticket_id():
    """Genera un ID único para el ticket"""
    fecha = datetime.now().strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:8].upper()
    return f"TKT-{fecha}-{unique}"

def registrar_venta(items: List[Dict], channel: str, payment_method: str, 
                   customer_info: Dict = None):
    """
    Registra una venta completa con múltiples productos
    
    Args:
        items: Lista de productos [{product_id, qty, price}, ...]
        channel: Canal de venta
        payment_method: Método de pago
    """
    try:
        ticket_id = generar_ticket_id()
        fecha_actual = datetime.now().isoformat()
        
        # Calcular totales
        subtotal = sum(item['qty'] * item['price'] for item in items)
        discount = 0
        total = subtotal - discount
        
        # 1. Crear el ticket (resumen de la venta)
        ticket_data = {
            "ticket_id": ticket_id,
            "date": fecha_actual,
            "subtotal": float(subtotal),
            "discount": float(discount),
            "total": float(total),
            "channel": channel,
            "payment_method": payment_method,
            "payment_status": "completed",
        }
        
        supabase.table("tickets").insert(ticket_data).execute()
        
        # 2. Crear los registros de venta (uno por producto)
        ventas_data = []
        for item in items:
            producto = get_producto_by_id(item['product_id'])
            if producto:
                venta = {
                    "ticket_id": ticket_id,
                    "date": fecha_actual,
                    "product_id": item['product_id'],
                    "name": producto['name'],
                    "qty": float(item['qty']),
                    "price": float(item['price']),
                    "total": float(item['qty'] * item['price']),
                    "channel": channel,
                    "payment_method": payment_method
                }
                ventas_data.append(venta)
        
        if ventas_data:
            supabase.table("ventas").insert(ventas_data).execute()
        
        return True, ticket_id, total
    
    except Exception as e:
        return False, str(e), 0

def actualizar_stock_manual(product_id, nueva_cantidad, motivo="Ajuste manual"):
    """Actualiza el stock de un producto manualmente"""
    try:
        # Obtener stock actual
        producto = get_producto_by_id(product_id)
        if not producto:
            return False, "Producto no encontrado"
        
        stock_anterior = producto['stock_quantity']
        
        # Actualizar stock
        supabase.table("productos").update({
            "stock_quantity": nueva_cantidad
        }).eq("product_id", product_id).execute()
        
        # Registrar movimiento
        movimiento = {
            "product_id": product_id,
            "tipo": "ajuste",
            "cantidad": nueva_cantidad - stock_anterior,
            "stock_anterior": stock_anterior,
            "stock_nuevo": nueva_cantidad,
            "motivo": motivo
        }
        supabase.table("movimientos_inventario").insert(movimiento).execute()
        
        return True, "Stock actualizado correctamente"
    
    except Exception as e:
        return False, str(e)
    
def obtener_siguiente_product_id():
    """
    Obtiene el siguiente ID consecutivo disponible
    """
    try:
        # Obtener todos los product_ids existentes
        response = a.table("productos").select("product_id").execute()
        
        if not response.data:
            return "PROD-0001"
        
        # Extraer los números de los product_ids existentes
        numeros = []
        for item in response.data:
            product_id = item['product_id']
            # Buscar patrón PROD-XXXX
            if product_id.startswith("PROD-"):
                try:
                    numero = int(product_id.split("-")[1])
                    numeros.append(numero)
                except (IndexError, ValueError):
                    continue
        
        if numeros:
            # Obtener el siguiente número consecutivo
            siguiente_numero = max(numeros) + 1
        else:
            # Si no hay productos con formato PROD-XXXX, empezar desde 1
            siguiente_numero = 1
        
        # Formatear con ceros a la izquierda (4 dígitos)
        return f"PROD-{siguiente_numero:04d}"
    
    except Exception as e:
        st.error(f"Error al generar ID: {e}")
        return None

def agregar_producto(product_data):
    """Agrega un nuevo producto al inventario"""
    try:
        a.table("inv_prod").insert(product_data).execute()
        return True, "Producto agregado exitosamente"
    except Exception as e:
        return False, str(e)