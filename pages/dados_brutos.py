import streamlit as st
import pandas as pd
import time

# Função para converter dataframe em CSV
@st.cache_data
def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Função de sucesso para feedback ao usuário
def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon="✅")
    time.sleep(5)
    sucesso.empty()

# Configuração da página
st.set_page_config(layout='wide')

# Título da Aplicação
st.title('DADOS BRUTOS')

# Carregar os dados
df = pd.read_csv("base_pedidos.csv")

# Converter a coluna de data corretamente
df['Data do Pedido'] = pd.to_datetime(df['Data do Pedido'], errors='coerce')

# Renomear a coluna de valor
df.rename(columns={'Valor PO - R$': 'Valor'}, inplace=True)

# Criar uma cópia para Compliance e preencher NaN
df_compliance = df.copy()
df_compliance['Check Compliance'] = df_compliance['Check Compliance'].fillna('Baixo')

# Expansor para seleção de colunas
with st.expander('Colunas'):
    colunas = st.multiselect('Selecione', list(df.columns), list(df.columns))

# Sidebar para filtros
st.sidebar.title('Filtros')

# Adicionar opção "Todos" nos filtros
opcoes_fornecedor = ["Todos"] + list(df['Nome Fornecedor'].dropna().unique())
opcoes_area = ["Todos"] + list(df['Area Autorizador'].dropna().unique())

# Filtro por Nome do Fornecedor
with st.sidebar.expander('Nome do Fornecedor'):
    fornecedor = st.selectbox('Selecione os Fornecedores', options=opcoes_fornecedor, index=0)

# Filtro por Área Responsável
with st.sidebar.expander('Área Responsável'):
    area = st.selectbox('Selecione as Áreas', options=opcoes_area, index=0)

# Filtro por Data da Compra
with st.sidebar.expander('Data da Compra'):
    data_pedido = st.date_input(
        'Selecione a Data',
        value=(df['Data do Pedido'].min(), df['Data do Pedido'].max())
    )

# Converter `st.date_input()` para datetime
data_inicio = pd.to_datetime(data_pedido[0])
data_fim = pd.to_datetime(data_pedido[1])

# Aplicar os filtros corretamente (permitindo "Todos")
dados_filtrados = df.copy()

if fornecedor != "Todos":
    dados_filtrados = dados_filtrados[dados_filtrados['Nome Fornecedor'] == fornecedor]

if area != "Todos":
    dados_filtrados = dados_filtrados[dados_filtrados['Area Autorizador'] == area]

# Filtrar por Data
dados_filtrados = dados_filtrados[
    (dados_filtrados['Data do Pedido'] >= data_inicio) &
    (dados_filtrados['Data do Pedido'] <= data_fim)
]

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
    nome_arquivo = st.text_input('', label_visibility='collapsed', value='dados') + '.csv'

# Botão de download
with coluna2:
    st.download_button(
        'Fazer download em csv',
        data=converte_csv(dados_filtrados),
        file_name=nome_arquivo,
        mime='text/csv',
        on_click=mensagem_sucesso
    )
