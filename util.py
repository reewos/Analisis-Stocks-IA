import re
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from openai import OpenAI
import sqlite3
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Configuración del cliente OpenAI para NVIDIA
llm = ChatNVIDIA(model="meta/llama3-70b-instruct")

def query_historical_data(symbol):
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM historical_data WHERE symbol = ? ORDER BY date DESC LIMIT 5", (symbol,))
    rows = c.fetchall()
    conn.close()
    for row in rows:
        print(row)

# query_historical_data("AAPL")

def create_database():
    """
    Crea la base de datos y las tablas necesarias si no existen.
    """
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    
    # Tabla para datos históricos
    c.execute('''CREATE TABLE IF NOT EXISTS historical_data
                 (symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER)''')
    
    # Tabla para información general del stock
    c.execute('''CREATE TABLE IF NOT EXISTS stock_info
                 (symbol TEXT PRIMARY KEY, name TEXT, sector TEXT, industry TEXT, market_cap REAL, pe_ratio REAL)''')
    
    # Tabla para noticias
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (symbol TEXT, title TEXT, summary TEXT)''')
    
    conn.commit()
    conn.close()

def get_stock_data(symbol, period="1mo"):
    """
    Obtiene datos históricos de precios y volumen para un símbolo de stock dado y los guarda en la base de datos.
    """
    stock = yf.Ticker(symbol)
    history = stock.history(period=period)
    
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    
    for index, row in history.iterrows():
        c.execute('''INSERT OR REPLACE INTO historical_data (symbol, date, open, high, low, close, volume)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (symbol, index.strftime('%Y-%m-%d'), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
    
    conn.commit()
    conn.close()
    
    return history

def get_stock_info(symbol):
    """
    Obtiene información general sobre el stock y la guarda en la base de datos.
    """
    stock = yf.Ticker(symbol)
    info = stock.info
    
    data = {
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
    }
    
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO stock_info (symbol, name, sector, industry, market_cap, pe_ratio)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (symbol, data['name'], data['sector'], data['industry'], data['market_cap'], data['pe_ratio']))
    
    conn.commit()
    conn.close()
    
    return data

def get_news(symbol, num_articles=5):
    """
    Obtiene noticias recientes relacionadas con el stock y las guarda en la base de datos.
    """
    api_key = "TU_CLAVE_API_AQUI"  # Reemplaza con tu clave API de Alpha Vantage
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    articles = data.get("feed", [])[:num_articles]
    news_data = [{"title": article["title"], "summary": article["summary"]} for article in articles]
    
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    
    for article in news_data:
        c.execute('''INSERT INTO news (symbol, title, summary) VALUES (?, ?, ?)''',
                  (symbol, article['title'], article['summary']))
    
    conn.commit()
    conn.close()
    
    return news_data



def get_stock_data_from_db(symbol):
    """Obtiene los datos del stock de la base de datos SQLite."""
    conn = sqlite3.connect('stock_data.db')
    c = conn.cursor()
    
    # Obtener información general del stock
    c.execute("SELECT * FROM stock_info WHERE symbol = ?", (symbol,))
    stock_info = c.fetchone()
    
    # Obtener noticias recientes
    c.execute("SELECT title, summary FROM news WHERE symbol = ? LIMIT 5", (symbol,))
    news = c.fetchall()
    
    conn.close()
    
    return stock_info, news

def analyze_sentiment(text):
    """Analiza el sentimiento del texto dado usando el modelo LLM."""
    prompt = f"Analiza el sentimiento del siguiente texto y clasifícalo como positivo, negativo o neutral. Texto: {text}\nSentimiento:"
    
    # completion = client.chat.completions.create(
    #     model="meta/llama3-70b-instruct",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.5,
    #     top_p=1,
    #     max_tokens=1024
    # )

    completion = llm.invoke(prompt)
    
    # return completion.choices[0].message.content.strip()
    return str(completion.content)


def summarize_news(news_list):
    """Resume las noticias y analiza su sentimiento general."""
    news_text = "\n".join([f"Título: {title}\nResumen: {summary}" for title, summary in news_list])
    prompt = f"Resume las siguientes noticias y proporciona un análisis general del sentimiento:\n{news_text}\nResumen y análisis:"

    completion = llm.invoke(prompt)
    return str(completion.content)

def analyze_stock(symbol):
    """Analiza el stock usando los datos de la base de datos y el modelo LLM."""
    stock_info, news = get_stock_data_from_db(symbol)
    
    if not stock_info:
        return "No se encontró información para este stock."
    # print(stock_info)
    
    id, name, sector, industry, market_cap, pe_ratio = stock_info
    
    news_summary = summarize_news(news)
    
    prompt = f"""
    Analiza el siguiente stock basándote en la información proporcionada:
    
    Nombre: {name}
    Sector: {sector}
    Industria: {industry}
    Capitalización de mercado: {market_cap}
    Ratio P/E: {pe_ratio}
    
    Resumen de noticias recientes:
    {news_summary}
    
    Proporciona un análisis detallado del stock, incluyendo:
    1. Una evaluación general de la empresa y su posición en el mercado.
    2. Posibles riesgos y oportunidades basados en las noticias recientes.
    3. Una recomendación de inversión (comprar, mantener, vender) con justificación.
    
    Análisis:
    """
    
    # completion = client.chat.completions.create(
    #     model="meta/llama3-70b-instruct",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.5,
    #     top_p=1,
    #     max_tokens=1024
    # )
    
    # return completion.choices[0].message.content.strip()


    completion = llm.invoke(prompt)
    return str(completion.content)

def delete_links(text):
    # Patrón de regex para encontrar enlaces en formato [texto](enlace)
    patron_enlaces = r'\[(.*?)\]\((.*?)\)'
    
    # Reemplazar los enlaces por el texto visible
    texto_limpio = re.sub(patron_enlaces, r'\1', text)
    
    return texto_limpio

def check_words_in_sentence(words, sentence):    
    # Verificar si al menos una palabra está presente en la oración
    for word in words:
        if word in sentence.split():
            return True
    return False