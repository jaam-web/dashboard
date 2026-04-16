import streamlit as st
import pandas as pd
import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Callable
from supabase import create_client

# ==========================================================
# 1. ABSTRACCIÓN (Principio de Inversión de Dependencias)
# ==========================================================

class DataRepository(ABC):
    """
    Define el contrato. Cualquier fuente de datos (SQL, NoSQL, Mock)
    debe implementar el método fetch_weather_data.
    """
    @abstractmethod
    def fetch_weather_data(self) -> pd.DataFrame:
        pass

# ==========================================================
# 2. IMPLEMENTACIONES (Single Responsibility)
# ==========================================================

class SupabaseRepository(DataRepository):
    """Maneja la conexión real con Supabase."""
    def __init__(self, url: str, key: str):
        try:
            self.client = create_client(url, key)
        except Exception:
            self.client = None

    def fetch_weather_data(self) -> pd.DataFrame:
        if not self.client:
            return pd.DataFrame() # Devuelve vacío si no hay cliente
            
        query = self.client.table("mediciones").select("*").order("created_at", desc=True).limit(20).execute()
        df = pd.DataFrame(query.data)
        
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        return df

class MockRepository(DataRepository):
    """Genera datos aleatorios si la base de datos falla."""
    def fetch_weather_data(self) -> pd.DataFrame:
        # Generar timestamps de los últimos 20 pasos
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
# 3. LÓGICA DE NEGOCIO (Recibe una función/metodo)
# ==========================================================

def get_live_metrics(fetch_func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """
    Esta función cumple tu requisito: recibe una función como parámetro.
    Permite cambiar la fuente de datos sin tocar la lógica de la UI.
    """
    return fetch_func()

# ==========================================================
# 4. CAPA DE PRESENTACIÓN (UI)
# ==========================================================

def apply_custom_styles():
    """Inyecta el CSS para el look industrial/tecnológico."""
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
                        url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920");
            background-size: cover;
            background-attachment: fixed;
        }
        [data-testid="stMetricValue"] {
            font-weight: 800 !important;
            color: #00ffcc !important;
            text-shadow: 0 0 10px rgba(0,255,204,0.5);
        }
        div[data-testid="column"] {
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px);
        }
        h1, h2, h3 { color: white !important; font-family: 'Segoe UI', Roboto, sans-serif; }
        </style>
        """,
        unsafe_allow_html=True
    )

def display_dashboard(df: pd.DataFrame):
    """Renderiza los componentes visuales del dashboard."""
    if df.empty:
        st.error("No se pudieron cargar datos.")
        return

    actual = df.iloc[0]
    
    # Fila 1: Métricas Principales
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Temperatura", f"{actual['temperatura']} °C")
    col2.metric("💧 Humedad", f"{actual['humedad']} %")
    col3.metric("💨 Viento", f"{actual['velocidad_viento']} m/s")

    st.write("") # Espaciador

    # Fila 2: Métricas Secundarias
    col4, col5, col6 = st.columns(3)
    col4.metric("🧊 Punto Rocío", f"{actual['punto_rocio']} °C")
    col5.metric("☀️ Radiación", f"{actual['radiacion_solar']} W/m²")
    col6.metric("⏲️ Presión", f"{actual['presion_atmosferica']} hPa")

    st.markdown("---")
    st.subheader("📊 Tendencias de la última hora")
    
    # Preparar datos para gráficas (invertir para orden cronológico)
    df_chart = df.iloc[::-1].set_index('created_at')
    
    t1, t2 = st.tabs(["📈 Análisis Térmico", "📉 Condiciones Ambientales"])
    with t1:
        st.line_chart(df_chart[['temperatura', 'punto_rocio']], height=250)
    with t2:
        st.area_chart(df_chart[['humedad', 'velocidad_viento']], height=250)

# ==========================================================
# 5. PUNTO DE ENTRADA (Main Loop)
# ==========================================================

def main():
    st.set_page_config(page_title="PROCPIC Weather Station", layout="wide")
    apply_custom_styles()
    
    # Credenciales (Sustituye por las tuyas o usa st.secrets)
    SUPABASE_URL = "https://fbwbzmlffgxnrzgvaeak.supabase.co"
    SUPABASE_KEY = "Sustituye_Esta_Key_Por_La_Tuya" 
    
    # Inicialización de repositorios
    real_repo = SupabaseRepository(SUPABASE_URL, SUPABASE_KEY)
    mock_repo = MockRepository()

    st.title("🛰️ Estación Meteorológica PROCPIC")
    st.markdown("_Monitoreo de telemetría en tiempo real_")

    placeholder = st.empty()

    while True:
        try:
            # Intentamos con la fuente real primero
            data = get_live_metrics(real_repo.fetch_weather_data)
            if data.empty: raise ValueError("Sin datos")
            status_text = "📡 Conectado a Supabase"
        except Exception:
            # Fallback automático a datos falsos
            data = get_live_metrics(mock_repo.fetch_weather_data)
            status_text = "⚠️ Modo Simulación (Offline)"

        with placeholder.container():
            st.caption(status_text)
            display_dashboard(data)
            
        time.sleep(5)

if __name__ == "__main__":
    main()
