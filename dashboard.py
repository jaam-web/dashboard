import streamlit as st
from supabase import create_client
import pandas as pd
import time

# 1. Configuración de página
st.set_page_config(page_title="Estación Meteorológica", layout="wide")

# 2. Inyección de CSS para Imagen de Fondo y Estilos
def add_bg_and_styles():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)),
                        url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
        }}

        /* Estilo para las métricas (Números en BOLD) */
        [data-testid="stMetricValue"] {{
            font-weight: 800 !important;
            font-size: 2.5rem !important;
            color: #00ffcc !important;
        }}

        /* Títulos de métricas */
        [data-testid="stMetricLabel"] {{
            color: #ffffff !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }}

        /* Contenedores traslúcidos */
        div[data-testid="column"] {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
        }}

        h1, h2, h3 {{
            color: white !important;
            text-shadow: 2px 2px 4px #000000;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_and_styles()

# 3. Conexión Supabase
URL = "https://fbwbzmlffgxnrzgvaeak.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZid2J6bWxmZmd4bnJ6Z3ZhZWFrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzNDU0MzksImV4cCI6MjA4NjkyMTQzOX0.NI3rwempQ3lGbndUAUfsiKO8cEOEdJEF1PsBFAcmUyY"
supabase = create_client(URL, KEY)

st.title("🛰️ Estación Meteorológica PROCPIC")
st.markdown("### Datos procesados en tiempo real")

placeholder = st.empty()

def cargar_datos():
    query = supabase.table("mediciones").select("*").order("created_at", desc=True).limit(20).execute()
    df = pd.DataFrame(query.data)
    if not df.empty:
        # Convertir tiempo y formatear a HH:mm:ss
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
    return df

while True:
    df = cargar_datos()

    with placeholder.container():
        if not df.empty:
            actual = df.iloc[0]

            # FILA 1: Principales
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Temperatura", f"{actual['temperatura']} °C")
            c2.metric("💧 Humedad", f"{actual['humedad']} %")
            c3.metric("💨 Viento", f"{actual['velocidad_viento']} m/s")

            st.write("") # Espaciador

            # FILA 2: Secundarias
            c4, c5, c6 = st.columns(3)
            c4.metric("🧊 Punto Rocío", f"{actual['punto_rocio']} °C")
            c5.metric("☀️ Radiación", f"{actual['radiacion_solar']} W/m²")
            c6.metric("⏲️ Presión", f"{actual['presion_atmosferica']} hPa")

            st.markdown("---")

            # GRÁFICAS ESTILIZADAS
            st.markdown("### 📊 Tendencias Recientes ")

            # Invertimos el df para que el gráfico fluya de izquierda a derecha
            df_plot = df.iloc[::-1]

            tab1, tab2 = st.tabs(["🔥 Térmico y Rocío", "🌊 Humedad y Viento"])

            with tab1:
                st.line_chart(df_plot.set_index('created_at')[['temperatura', 'punto_rocio']], height=300)
            with tab2:
                st.area_chart(df_plot.set_index('created_at')[['humedad', 'velocidad_viento']], height=300)
        else:
            st.warning("⚠️ Esperando datos de Supabase...")

    time.sleep(4)
