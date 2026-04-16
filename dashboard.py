import streamlit as st
import pandas as pd
import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Callable
from supabase import create_client

# ==========================================================
# 1. ABSTRACCIÓN Y REPOSITORIOS (Capa de Datos)
# ==========================================================

class DataRepository(ABC):
    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        pass

class SupabaseRepo(DataRepository):
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        try:
            self.client = create_client(url, key)
        except:
            self.client = None

    def fetch_data(self) -> pd.DataFrame:
        if not self.client: return pd.DataFrame()
        query = self.client.table("mediciones").select("*").order("created_at", desc=True).limit(20).execute()
        df = pd.DataFrame(query.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        return df

class MockRepo(DataRepository):
    def fetch_data(self) -> pd.DataFrame:
        tiempos = [(pd.Timestamp.now() - pd.Timedelta(seconds=i*5)).strftime('%H:%M:%S') for i in range(20)]
        data = {
            'created_at': tiempos,
            'temperatura': np.random.uniform(22, 28, 20).round(1),
            'humedad': np.random.uniform(50, 70, 20).round(1),
            'velocidad_viento': np.random.uniform(2, 12, 20).round(1),
            'punto_rocio': np.random.uniform(14, 18, 20).round(1),
            'radiacion_solar': np.random.uniform(200, 600, 20).round(0),
            'presion_atmosferica': np.random.uniform(1011, 1015, 20).round(1)
        }
        return pd.DataFrame(data)

# ==========================================================
# 2. ORQUESTADOR (La función que maneja todo)
# ==========================================================

def data_manager(primary_provider: Callable[[], pd.DataFrame], 
                 backup_provider: Callable[[], pd.DataFrame]) -> tuple[pd.DataFrame, str]:
    """
    Maneja la lógica de obtención de datos sin que el Main sepa de dónde vienen.
    """
    try:
        df = primary_provider()
        if df.empty: raise ValueError("DB Empty")
        return df, "CONNECTED"
    except:
        return backup_provider(), "SIMULATED"

# ==========================================================
# 3. INTERFAZ ESTÉTICA (Semicírculos y Glassmorphism)
# ==========================================================

def apply_pro_styles():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
                        url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
        }}

       /* Tarjetas estilo cápsula (bordes muy redondeados) */
        .metric-card {{
            background: rgba(255, 255, 255, 0.07);
            border-radius: 40px; 
            padding: 12px; 
            margin: 15px; /* <--- AGREGA ESTA LÍNEA PARA LA SEPARACIÓN */
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(12px);
            text-align: center;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            /* --- CAMBIOS PARA TAMAÑO UNIFORME --- */
           display: inline-block;
           width: 180px;      /* Esto obliga a que todos midan lo mismo de ancho */
           min-height: 100px; /* Esto asegura que todos tengan la misma altura mínima */
           vertical-align: top; /* Alinea los cuadros por la parte superior */
        }}

        .metric-card:hover {{
            border-color: #00ffcc;
            background: rgba(255, 255, 255, 0.12);
            transform: scale(1.02);
        }}

        .metric-label {{ 
            color: #ffffff; 
            font-size: 0.9rem; 
            font-weight: 500;
            margin-bottom: 5px;
        }}

        .metric-value {{ 
            color: #00ffcc; 
            font-size: 2.2rem; 
            font-weight: 800; 
            text-shadow: 0 0 10px rgba(0,255,204,0.3);
        }}

        h1, h3 {{ 
            color: white !important; 
            text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
def render_custom_metric(label, value, icon):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================================
# 4. CONFIGURACIÓN EXTERNA (Para que el Main esté limpio)
# ==========================================================

def get_data_engine():
    """
    Fábrica de funciones: Aquí se configuran las credenciales.
    El Main solo recibirá la función lista para usar.
    """
    # En producción usarías st.secrets
    URL = "https://fbwbzmlffgxnrzgvaeak.supabase.co"
    KEY = "TU_KEY_AQUI"
    
    real_repo = SupabaseRepo(URL, KEY)
    mock_repo = MockRepo()
    
    # Retornamos una función que ya sabe qué hacer
    return lambda: data_manager(real_repo.fetch_data, mock_repo.fetch_data)

# ==========================================================
# 5. MAIN (Totalmente agnóstico a la DB)
# ==========================================================

def main(engine: Callable[[], tuple[pd.DataFrame, str]]):
    """
    EL MAIN NO TIENE NADA DE SUPABASE.
    Solo recibe el 'engine' y lo ejecuta.
    """
    st.set_page_config(page_title="PROCPIC Dashboard", layout="wide")
    apply_pro_styles()
    
    st.title("🛰️ Estación Meteorológica PROCPIC")
    st.write("---")
    
    placeholder = st.empty()

    while True:
        # Aquí se ejecuta la magia sin saber de dónde vienen los datos
        df, status = engine()

        with placeholder.container():
            # Barra de estado minimalista
            st.caption(f"Status: {status} | Last Sync: {pd.Timestamp.now().strftime('%H:%M:%S')}")
            
            if not df.empty:
                actual = df.iloc[0]
                
                # Fila 1
                c1, c2, c3 = st.columns(3)
                with c1: render_custom_metric("Temperatura", f"{actual['temperatura']}°C", "🌡️")
                with c2: render_custom_metric("Humedad", f"{actual['humedad']}%", "💧")
                with c3: render_custom_metric("Viento", f"{actual['velocidad_viento']} m/s", "💨")
                
                st.write("")
                
                # Fila 2
                c4, c5, c6 = st.columns(3)
                with c4: render_custom_metric("Punto Rocío", f"{actual['punto_rocio']}°C", "🧊")
                with c5: render_custom_metric("Radiación", f"{actual['radiacion_solar']} W/m²", "☀️")
                with c6: render_custom_metric("Presión", f"{actual['presion_atmosferica']} hPa", "⏲️")

                # Gráficas
                st.markdown("### 📊 Histórico Reciente")
                df_plot = df.iloc[::-1].set_index('created_at')
                st.line_chart(df_plot[['temperatura', 'humedad']], height=250)
            
        time.sleep(5)

if __name__ == "__main__":
    # 1. Preparamos el motor de datos fuera del main
    weather_engine = get_data_engine()
    
    # 2. Iniciamos el main pasándole la función manejadora
    main(weather_engine)
