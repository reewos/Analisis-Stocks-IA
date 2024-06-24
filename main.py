import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
import sqlite3
from openai import OpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os
from util import *
# Carga de variables de entorno
import dotenv
dotenv.load_dotenv()


import getpass
import os

if not os.environ.get("NVIDIA_API_KEY", "").startswith("nvapi-"):
    nvidia_api_key = getpass.getpass("Enter your NVIDIA API key: ")
    assert nvidia_api_key.startswith("nvapi-"), f"{nvidia_api_key[:5]}... is not a valid key"
    os.environ["NVIDIA_API_KEY"] = nvidia_api_key


# Función para obtener datos históricos actualizados
def get_stock_data(symbol, period="1mo"):
    stock = yf.Ticker(symbol)
    history = stock.history(period=period)
    return history

# Función para crear gráfico de precios
def create_price_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Precio'))
    fig.update_layout(title='Gráfico de Precios', xaxis_title='Fecha', yaxis_title='Precio')
    return fig

# Interfaz de Streamlit
st.title('Análisis de Stocks con IA')

# Input para el símbolo del stock
symbol = st.text_input('Ingrese el símbolo del stock (ej. NVDA):', 'NVDA')

if st.button('Analizar'):
    # Obtener datos históricos actualizados
    historical_data = get_stock_data(symbol)
    
    # Crear y mostrar gráfico de precios
    price_chart = create_price_chart(historical_data)
    st.plotly_chart(price_chart)
    
    create_database()
    # Obtener y guardar datos históricos
    historical_data = get_stock_data(symbol)
    print(f"Datos históricos para {symbol} guardados en la base de datos.")
    st.write(f"Datos historicas para {symbol} guardadas en la base de datos.")
    
    # Obtener y guardar información general del stock
    stock_info = get_stock_info(symbol)
    # print("Información general del stock guardada en la base de datos.")
    # st.write(f"Información general del stock guardada en la base de datos.")
    
    # Obtener y guardar noticias recientes
    news = get_news(symbol)
    # print("Noticias recientes guardadas en la base de datos.")
    # st.write(f"Noticias recientes guardadas en la base de datos.")

    # print("\nTodos los datos han sido guardados en 'stock_data.db'")
    # st.write(f"Todos los datos han sido guardados en 'stock_data.db'")

    # Mostrar información básica del stock
    try:
        stock_info, news = get_stock_data_from_db(symbol)
    except:
        st.error('No se encontró información para este stock.')
        

    if stock_info:
        st.subheader('Información del Stock')
        st.write(f"Nombre: {stock_info[0]}")
        st.write(f"Sector: {stock_info[1]}")
        st.write(f"Industria: {stock_info[2]}")
        st.write(f"Capitalización de mercado: {stock_info[3]}")
        st.write(f"Ratio P/E: {stock_info[4]}")
    else:
        st.error('No se encontró información para este stock.')
        
    
    # Mostrar noticias recientes
    st.subheader('Noticias Recientes')
    for title, summary in news:
        st.write(f"**{title}**")
        st.write(summary)
        st.write("---")
    
    # Realizar y mostrar análisis
    st.subheader('Análisis del Stock')
    with st.spinner('Analizando el stock...'):
        analysis = analyze_stock(symbol)
        st.write(analysis)

# Agregar información sobre el uso de IA
st.sidebar.title('Acerca de')
with st.sidebar:
    # Crear una entrada de texto para la clave API
    api_key = st.text_input("Ingrese su clave API", type="password")

    # Mostrar la clave API si se ingresa (para propósitos de prueba, en producción no mostrarías la clave)
    if api_key:
        st.write("Clave API ingresada correctamente.")
        os.environ["NVIDIA_API_KEY"] = api_key

st.sidebar.info('Esta aplicación utiliza IA para analizar stocks. El análisis se basa en datos históricos, información de la empresa y noticias recientes. La IA proporciona un resumen y recomendaciones, pero no debe considerarse como asesoramiento financiero profesional.')