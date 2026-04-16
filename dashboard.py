import streamlit as st
import pandas as pd
import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Callable
from supabase import create_client

# ==========================================================
# 1. CAPA DE DATOS (SOLID)
# ==========================================================

class RepositorioDatos(ABC):
    @abstractmethod
    def obtener_datos(self) -> pd.DataFrame:
        pass

class RepositorioSupabase(RepositorioDatos):
    def __init__(self, url: str, clave: str):
        try:
            self.cliente = create_client(url, clave)
        except:
            self.cliente = None

    def obtener_datos(self) -> pd.DataFrame:
        if not self.cliente: return pd.DataFrame()
        consulta = self.cliente.table("mediciones").select("*").order("created_at", desc=True).limit(20).execute()
        df = pd.DataFrame(consulta.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        return df

class RepositorioPrueba(RepositorioDatos):
    def obtener_datos(self) -> pd.DataFrame:
        tiempos = [(pd.Timestamp.now() - pd.Timedelta(seconds=i*5)).strftime('%H:%M:%S') for i in range(20)]
        datos = {
            'created_at': tiempos,
            'temperatura': np.random.uniform(22, 28, 20).round(1),
            'humedad': np.random.uniform(50, 70, 20).round(1),
            'velocidad_viento': np.random.uniform(2, 12, 20).round(1),
            'punto_rocio': np.random.uniform(14, 18, 20).round(1),
            'radiacion_solar': np.random.uniform(200, 600, 20).round(0),
            'presion_atmosferica': np.random.uniform(1011, 1015, 20).round(1)
        }
        return pd.DataFrame(datos)

# ==========================================================
# 2. ORQUESTADOR
# ==========================================================

def gestor_de_datos(proveedor_principal: Callable[[], pd.DataFrame], 
                    proveedor_respaldo: Callable[[], pd.DataFrame]) -> tuple[pd.DataFrame, str]:
    try:
        df = proveedor_principal()
        if df.empty: raise ValueError("Sin datos")
        return df, "📡 CONECTADO"
    except:
        return proveedor_respaldo(), "⚠️ SIMULACIÓN"

# ==========================================================
# 3. INTERFAZ RESPONSIVA Y ESTÉTICA
# ==========================================================

def aplicar_estilos_profesionales():
    st.markdown(
        """
        <style>
        /* Fondo con imagen y filtro */
        .stApp {
            background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)),
                        url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
        }

        /* Contenedor Flex para evitar solapamiento en móviles */
        .contenedor-metricas {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }

        /* Tarjetas estilo cápsula responsivas */
        .tarjeta-metrica {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(15px);
            text-align: center;
            min-width: 160px;
            flex: 1; /* Esto hace que se ajusten al ancho disponible */
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .etiqueta-metrica { color: #ddd; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; }
        .valor-metrica { color: #00ffcc; font-size: 1.8rem; font-weight: 800; margin-top: 5px; }

        /* Mejora para el área de gráficas */
        .stChart {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def renderizar_metrica(etiqueta, valor, icono):
    """Crea un bloque HTML para cada métrica que se adapta a la pantalla"""
    return f"""
        <div class="tarjeta-metrica">
            <div class="etiqueta-metrica">{icono} {etiqueta}</div>
            <div class="valor-metrica">{valor}</div>
        </div>
    """

# ==========================================================
# 4. FÁBRICA DE MOTOR DE DATOS (Encapsulamiento)
# ==========================================================

def configurar_motor_datos():
    # Credenciales encapsuladas
    URL_SUPABASE = "https://fbwbzmlffgxnrzgvaeak.supabase.co"
    KEY_SUPABASE = "TU_KEY_AQUI"
    
    repo_real = RepositorioSupabase(URL_SUPABASE, KEY_SUPABASE)
    repo_falso = RepositorioPrueba()
    
    return lambda: gestor_de_datos(repo_real.obtener_datos, repo_falso.obtener_datos)

# ==========================================================
# 5. PUNTO DE ENTRADA (Main) - SIN REFERENCIAS A DB
# ==========================================================

def main(motor: Callable[[], tuple[pd.DataFrame, str]]):
    st.set_page_config(page_title="Estación PROCPIC", layout="wide")
    aplicar_estilos_profesionales()
    
    st.title("🛰️ Estación Meteorológica PROCPIC")
    
    espacio_dinamico = st.empty()

    while True:
        datos, estado = motor()

        with espacio_dinamico.container():
            st.caption(f"ESTADO: {estado} | 🕒 {pd.Timestamp.now().strftime('%H:%M:%S')}")
            
            if not datos.empty:
                actual = datos.iloc[0]
                
                # Renderizado con HTML personalizado para evitar solapamiento
                st.markdown(f"""
                    <div class="contenedor-metricas">
                        {renderizar_metrica("Temperatura", f"{actual['temperatura']}°C", "🌡️")}
                        {renderizar_metrica("Humedad", f"{actual['humedad']}%", "💧")}
                        {renderizar_metrica("Viento", f"{actual['velocidad_viento']}m/s", "💨")}
                        {renderizar_metrica("Presión", f"{actual['presion_atmosferica']}hPa", "⏲️")}
                    </div>
                """, unsafe_allow_html=True)
                
                st.write("") # Espacio

                # Sección de Gráficas mejorada
                st.subheader("📊 Tendencia Temporal")
                df_grafica = datos.iloc[::-1].set_index('created_at')
                
                # Usamos Area Chart para que se vea más moderno que una simple línea
                st.area_chart(df_grafica[['temperatura', 'humedad']], height=250, use_container_width=True)
            
        time.sleep(5)

if __name__ == "__main__":
    motor_climatico = configurar_motor_datos()
    main(motor_climatico)
