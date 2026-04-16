import streamlit as st
from supabase import create_client
import pandas as pd
import time
from abc import ABC, abstractmethod
from typing import Callable

# ==========================================================
# 1. CAPA DE ABSTRACCIÓN (Principio de Inversión de Dependencia)
# ==========================================================

class DataRepository(ABC):
    """
    Esta es una Interface. Define QUÉ debe hacer cualquier repositorio
    de datos, pero no CÓMO. Así, si cambias de DB, solo creas una nueva clase.
    """
    @abstractmethod
    def fetch_weather_data(self) -> pd.DataFrame:
        pass

# ==========================================================
# 2. IMPLEMENTACIONES ESPECÍFICAS (Single Responsibility)
# ==========================================================

class SupabaseRepository(DataRepository):
    """Clase encargada ÚNICAMENTE de la comunicación con Supabase."""
    def __init__(self, url: str, key: str):
        self.client = create_client(url, key)

    def fetch_weather_data(self) -> pd.DataFrame:
        # Lógica específica de Supabase
        query = self.client.table("mediciones").select("*").order("created_at", desc=True).limit(20).execute()
        df = pd.DataFrame(query.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
        return df

# Ejemplo de cómo sería otra base de datos en el futuro:
# class MySQLRepository(DataRepository):
#     def fetch_weather_data(self): ... lógica de mysql ...

# ==========================================================
# 3. LÓGICA DE NEGOCIO / SERVICIO
# ==========================================================

def get_dashboard_data(repository_func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """
    Esta es la función que pediste. Recibe una FUNCIÓN (o método) 
    como argumento. No sabe si los datos vienen de Supabase o Marte.
    """
    return repository_func()

# ==========================================================
# 4. INTERFAZ DE USUARIO (UI)
# ==========================================================

def setup_ui():
    """Configuración estética separada de la lógica de datos."""
    st.set_page_config(page_title="Estación Meteorológica", layout="wide")
    
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)),
                        url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
        }
        [data-testid="stMetricValue"] { font-weight: 800 !important; color: #00ffcc !important; }
        div[data-testid="column"] {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        h1, h2, h3 { color: white !important; text-shadow: 2px 2px 4px #000; }
        </style>
    """, unsafe_allow_html=True)

def render_metrics(actual_data):
    """Renderiza las tarjetas de métricas."""
    c1, c2, c3 = st.columns(3)
    c1.metric("🌡️ Temperatura", f"{actual_data['temperatura']} °C")
    c2.metric("💧 Humedad", f"{actual_data['humedad']} %")
    c3.metric("💨 Viento", f"{actual_data['velocidad_viento']} m/s")

    st.write("") 

    c4, c5, c6 = st.columns(3)
    c4.metric("🧊 Punto Rocío", f"{actual_data['punto_rocio']} °C")
    c5.metric("☀️ Radiación", f"{actual_data['radiacion_solar']} W/m²")
    c6.metric("⏲️ Presión", f"{actual_data['presion_atmosferica']} hPa")

# ==========================================================
# 5. EJECUCIÓN PRINCIPAL (Main Loop)
# ==========================================================

def main():
    setup_ui()
    
    # Configuración de credenciales (Podrían venir de un .env)
    URL = "https://fbwbzmlffgxnrzgvaeak.supabase.co"
    KEY = "tu_key_aqui" # Por seguridad, usa st.secrets en producción
    
    # Instanciamos el repositorio (Aquí es donde decides qué DB usar)
    repo = SupabaseRepository(URL, KEY)
    
    st.title("🛰️ Estación Meteorológica PROCPIC")
    st.markdown("### Datos procesados en tiempo real")
    
    placeholder = st.empty()

    while True:
        # PASO CLAVE: Pasamos la FUNCIÓN del repositorio a nuestra lógica
        # Si mañana cambias repo por 'MySQLRepository', esta línea no cambia.
        df = get_dashboard_data(repo.fetch_weather_data)

        with placeholder.container():
            if not df.empty:
                actual = df.iloc[0]
                render_metrics(actual)

                st.markdown("---")
                st.markdown("### 📊 Tendencias Recientes")
                
                df_plot = df.iloc[::-1].set_index('created_at')
                tab1, tab2 = st.tabs(["🔥 Térmico", "🌊 Ambiente"])

                with tab1:
                    st.line_chart(df_plot[['temperatura', 'punto_rocio']], height=300)
                with tab2:
                    st.area_chart(df_plot[['humedad', 'velocidad_viento']], height=300)
            else:
                st.warning("⚠️ Buscando datos en el repositorio...")

        time.sleep(4)

if __name__ == "__main__":
    main()
