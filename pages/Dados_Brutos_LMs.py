# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 11:53:25 2025

@author: cvieira
"""

import streamlit as st
import pandas as pd
import time
from io import BytesIO

# Função para converter dataframe em CSV
@st.cache_data

def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Função de sucesso para feedback ao usuário
def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon="✅")
    time.sleep(5)
    sucesso.empty()
    
def converte_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')  # Exportar para Excel sem índice
    return output.getvalue()  # Retorna os bytes do arquivo

# Configuração da página
st.set_page_config(layout='wide')

# Upload do arquivo base_pedidos.csv
uploaded_csv = st.file_uploader("📂 Carregue o arquivo base_lms.csv", type=["csv"])

# Upload do arquivo auditoria_pedidos.xlsx
uploaded_xlsx = st.file_uploader("📂 Carregue o arquivo auditoria_lms.xlsx", type=["xlsx"])


# Título da Aplicação
st.title('DADOS BRUTOS')

# Carregar os dados
df_lms = pd.read_csv('base_lms.csv')
df_lms['Data Documento'] = pd.to_datetime(df_lms['Data Documento'], errors = 'coerce')
df_lms.drop(columns='Valor', inplace = True)
df_lms.rename(columns={'Valor R$': 'Valor'}, inplace = True)

df_lms = df_lms.sort_values('Data Documento', ascending=True).reset_index()
df_lms['Mes'] = df_lms['Data Documento'].dt.month.astype(str).str.zfill(2)  # Meses como '01', '02', etc.
df_lms['Ano'] = df_lms['Data Documento'].dt.year.astype(str)
   
# Expansor para seleção de colunas
with st.expander('Colunas'):
    colunas = st.multiselect('Selecione', list(df_lms.columns), list(df_lms.columns))

# Sidebar para filtros
st.sidebar.title('Filtros')

# Adicionar opção "Todos" nos filtros
opcoes_funcionario = ["Todos"] + list(df_lms['Nome'].dropna().unique())
opcoes_cc = ["Todas"] + list(df_lms['Nome CC'].dropna().unique())
opcoes_categoria = ['Todas'] + list(df_lms['Categoria do Gasto'].dropna().unique())

# Filtro por Nome do Fornecedor
with st.sidebar.expander('Nome do Funcionário'):
    funcionario = st.selectbox('Selecione os Funcionários', options=opcoes_funcionario, index=0)

# Filtro por Área Responsável
with st.sidebar.expander('Área Responsável'):
    area = st.selectbox('Selecione as Áreas', options=opcoes_cc, index=0)

# Filtro por Tipo
with st.sidebar.expander('Categoria da Despesa'):
    categoria = st.selectbox(
        'Selecione a Categoria',opcoes_categoria)

# Aplicar os filtros corretamente (permitindo "Todos")
dados_filtrados = df_lms.copy()

if funcionario != "Todos":
    dados_filtrados = dados_filtrados[dados_filtrados['Nome'] == funcionario]

if area != "Todas":
    dados_filtrados = dados_filtrados[dados_filtrados['Nome CC'] == area]

if categoria != 'Todas':
    dados_filtrados = dados_filtrados[dados_filtrados['Categoria do Gasto'] == categoria]

# Selecionar apenas as colunas desejadas
dados_filtrados = dados_filtrados[colunas]

# Exibir a tabela filtrada
st.dataframe(dados_filtrados)

# Exibir a quantidade de linhas e colunas filtradas
st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas.')

# Input para nome do arquivo
st.markdown('Escreva o nome do arquivo.')
coluna1, coluna2 = st.columns(2)

with coluna1:
    nome_arquivo = st.text_input('', label_visibility='collapsed', value='dados_lms') + '.xlsx'

# Botão de download
with coluna2:
    st.download_button(
    label="Fazer download em Excel",
    data=converte_excel(dados_filtrados),
    file_name=f"{nome_arquivo}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    on_click=mensagem_sucesso,
    key="download4"
    )
