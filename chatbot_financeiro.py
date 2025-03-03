import streamlit as st
import sqlite3
import yfinance as yf
import pandas as pd
from streamlit_extras.colored_header import colored_header

# Configuração do Streamlit
st.set_page_config(page_title="ChatBot Financeiro", page_icon="💰", layout="wide")
st.title("🤖 ChatBot Financeiro 📈 - Desenvolvido por Nilson Marcelo @TopGrafx")
st.write("Este bot analisa o mercado e exibe setups ativados.")

# Criar banco de dados SQLite
db_path = "setups_mercado.db"

# Lista de ativos monitorados na B3
ativos_b3 = ["ABEV3", "ASAI3", "AZUL4", "AZZA3", "B3SA3", "BBSE3", "BBDC4", "BBAS3", 
    "BRAV3", "BRFS3", "BPAC11", "CMIG4", "CPLE6", "CSAN3", "CYRE3", "ELET3", 
    "EMBR3", "ENGI11", "ENEV3", "EQTL3", "GGBR4", "NTCO3", "HAPV3", "HYPE3", 
    "ITUB4", "JBSS3", "KLBN11", "RENT3", "LREN3", "MGLU3", "MRVE3", 
    "MULT3", "PETR3", "PETR4", "PRIO3", "RADL3", "RDOR3", "RAIL3", "SBSP3", 
    "CSNA3", "SUZB3", "VIVT3", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3", 
    "VBBR3", "WEGE3"]

# Criar tabelas para armazenar os setups
def criar_tabelas():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tabelas = {
        "bebe_abandonado_alta": "ticker TEXT, data TEXT, fechamento REAL",
        "bebe_abandonado_baixa": "ticker TEXT, data TEXT, fechamento REAL",
        "bb_rompimento_alta": "ticker TEXT, data TEXT, fechamento REAL",
        "bb_rompimento_baixa": "ticker TEXT, data TEXT, fechamento REAL",
        "cruzamento_mme9_mms21_alta": "ticker TEXT, data TEXT, fechamento REAL",
        "cruzamento_mme9_mms21_baixa": "ticker TEXT, data TEXT, fechamento REAL",
    }

    for tabela, colunas in tabelas.items():
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {tabela} (id INTEGER PRIMARY KEY AUTOINCREMENT, {colunas})")

    conn.commit()
    conn.close()

# Detectar Bebê Abandonado de Alta e Baixa
def detectar_bebe_abandonado():
    alta = []
    baixa = []
    
    for ticker in ativos_b3:
        hist = yf.Ticker(ticker + ".SA").history(period="10d")

        if len(hist) < 3:
            continue

        c3, c2, c1 = hist.iloc[-3], hist.iloc[-2], hist.iloc[-1]

        # Bebê Abandonado de Alta
        if c3.Close < c3.Open and c2.Low > c3.Close and c2.High < c3.Open and c1.Close > c1.Open and c1.Low > c2.High:
            alta.append((ticker, c1.name.strftime("%Y-%m-%d"), c1.Close))

        # Bebê Abandonado de Baixa
        if c3.Close > c3.Open and c2.High < c3.Close and c2.Low > c3.Open and c1.Close < c1.Open and c1.High < c2.Low:
            baixa.append((ticker, c1.name.strftime("%Y-%m-%d"), c1.Close))

    return alta, baixa

# Detectar rompimento das Bandas de Bollinger
def detectar_rompimento_bb():
    alta = []
    baixa = []

    for ticker in ativos_b3:
        hist = yf.Ticker(ticker + ".SA").history(period="20d")

        if len(hist) < 20:
            continue

        hist["BB_sup"] = hist["Close"].rolling(20).mean() + 2 * hist["Close"].rolling(20).std()
        hist["BB_inf"] = hist["Close"].rolling(20).mean() - 2 * hist["Close"].rolling(20).std()

        if hist["Close"].iloc[-1] > hist["BB_sup"].iloc[-1]:
            alta.append((ticker, hist.index[-1].strftime("%Y-%m-%d"), hist["Close"].iloc[-1]))
        if hist["Close"].iloc[-1] < hist["BB_inf"].iloc[-1]:
            baixa.append((ticker, hist.index[-1].strftime("%Y-%m-%d"), hist["Close"].iloc[-1]))

    return alta, baixa

# Detectar cruzamento da MME9 com MMS21
def detectar_cruzamento_medias():
    alta = []
    baixa = []

    for ticker in ativos_b3:
        hist = yf.Ticker(ticker + ".SA").history(period="50d")

        if len(hist) < 21:
            continue

        hist["MME9"] = hist["Close"].ewm(span=9, adjust=False).mean()
        hist["MMS21"] = hist["Close"].rolling(window=21).mean()

        if hist["MME9"].iloc[-2] < hist["MMS21"].iloc[-2] and hist["MME9"].iloc[-1] > hist["MMS21"].iloc[-1]:
            alta.append((ticker, hist.index[-1].strftime("%Y-%m-%d"), hist["Close"].iloc[-1]))

        if hist["MME9"].iloc[-2] > hist["MMS21"].iloc[-2] and hist["MME9"].iloc[-1] < hist["MMS21"].iloc[-1]:
            baixa.append((ticker, hist.index[-1].strftime("%Y-%m-%d"), hist["Close"].iloc[-1]))

    return alta, baixa

# Criar tabelas no banco
criar_tabelas()

# Detectar e salvar os setups
setups = {
    "bebe_abandonado_alta": detectar_bebe_abandonado()[0],
    "bebe_abandonado_baixa": detectar_bebe_abandonado()[1],
    "bb_rompimento_alta": detectar_rompimento_bb()[0],
    "bb_rompimento_baixa": detectar_rompimento_bb()[1],
    "cruzamento_mme9_mms21_alta": detectar_cruzamento_medias()[0],
    "cruzamento_mme9_mms21_baixa": detectar_cruzamento_medias()[1],
}

# Exibir setups no Streamlit
for setup, ativos in setups.items():
    st.subheader(f"📊 {setup.replace('_', ' ').title()}")
    if ativos:
        df = pd.DataFrame(ativos, columns=["Ticker", "Data", "Fechamento"])
        st.dataframe(df)
    else:
        st.write("Nenhum ativo encontrado.")
