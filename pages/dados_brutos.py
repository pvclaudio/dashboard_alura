import streamlit as st
import requests
import pandas as pd
import time

@st.cache_data

def converte_csv(df):
    return df.to_csv(index = False).encode('utf-8')
    
def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon = "✅" )
    time.sleep(5)
    sucesso.empty()

st.set_page_config(layout = 'wide')

st.title('DADOS BRUTOS')

url = "https://labdados.com/produtos"

response = requests.get(url, verify = False)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y', errors = 'coerce')


with st.expander('Colunas'):
    colunas = st.multiselect('Selecione', list(dados.columns), list(dados.columns))
    
st.sidebar.title('Filtros')

with st.sidebar.expander('Nome do Produto'):
    produtos = st.selectbox('Selecione os Produtos', options=dados['Produto'].unique())

with st.sidebar.expander('Preço do Produto'):
    preco = st.slider('Selecione o Preço', 0, 5000, (0,5000))

with st.sidebar.expander('Data da Compra'):
    data_compra = st.date_input('Selecione a Data', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))

query = '''
Produto in @produtos and \
@preco[0] <= Preço <= @preco[1] and \
@data_compra[0] <= `Data da Compra` <= @data_compra[1]
'''

dados_filtrados = dados.query(query)
dados_filtrados = dados_filtrados[colunas]

st.dataframe(dados_filtrados)

st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas.')

st.markdown('Escreva o nome do arquivo.')
coluna1, coluna2 = st.columns(2)

with coluna1:
    nome_arquivo = st.text_input('', label_visibility = 'collapsed', value = 'dados')
    nome_arquivo += '.csv'

with coluna2:
    st.download_button('Fazer download em csv', 
                       data = converte_csv(dados_filtrados), 
                       file_name = nome_arquivo, 
                       mime = 'text/csv', 
                       on_click = mensagem_sucesso)
