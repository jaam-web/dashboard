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
    st.markdown("""
        <style>
        .stApp {
            background: #0e1117;
            background-image: radial-gradient(circle at 20% 30%, #1a2a6c 0%, transparent 20%), 
                              radial-gradient(circle at 80% 70%, #b21f1f 0%, transparent 20%);
        }
        /* Tarjetas con bordes muy redondeados (semicírculos en las esquinas) */
        .metric-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 30px; /* Bordes muy suaves */
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            text-align: center;
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: #00ffcc;
        }
        .metric-label { color: #888; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { color: #00ffcc; font-size: 32px; font-weight: 800; margin: 10px 0; }
        </style>
    """, unsafe_allow_html=True)

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
