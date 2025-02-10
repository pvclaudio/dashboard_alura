import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import calendar
import time
from io import BytesIO

st.set_page_config(layout='wide')

st.title('Dashboard de LMs :mag_right:')

# Funções

def format_value(valor, prefixo=''):
    for unidade in ['', 'mil', 'milhões', 'bilhões']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'.strip()
        valor /= 1000
    return f'{prefixo} {valor:.2f} trilhões'

def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon = "✅" )
    time.sleep(5)
    sucesso.empty()

def converte_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')  # Exportar para Excel sem índice
    return output.getvalue()  # Retorna os bytes do arquivo

# Bases de Dados

df_lms = pd.read_csv('base_lms.csv')
df_lms['Data Documento'] = pd.to_datetime(df_lms['Data Documento'], errors = 'coerce')
df_lms.drop(columns='Valor', inplace = True)
df_lms.rename(columns={'Valor R$': 'Valor'}, inplace = True)

df_lms = df_lms.sort_values('Data Documento', ascending=True).reset_index()
df_lms['Mes'] = df_lms['Data Documento'].dt.month.astype(str).str.zfill(2)  # Meses como '01', '02', etc.
df_lms['Ano'] = df_lms['Data Documento'].dt.year.astype(str)
df_lms['Ano_Mes'] = df_lms['Ano'] + '-' + df_lms['Mes']

df_lms_filtrado = df_lms.groupby('Ano_Mes', as_index=False)['Valor'].sum()
df_lms_filtrado['Valor Formatado'] = df_lms_filtrado['Valor'].apply(lambda x: format_value(x, 'R$'))
df_lms_filtrado['Ano'] = df_lms_filtrado['Ano_Mes'].str.slice(0, 4)

df_agente = pd.read_excel('auditoria_lms.xlsx', engine = 'openpyxl')
df_agente['Nome CC'].fillna('Não informado', inplace = True)

# Opções para os filtros

opcoes_anos = ['Todos'] + list(df_lms['Ano'].unique())

# Criando Filtros

with st.sidebar.expander('Ano'):
    anos = st.selectbox('Selecione os Anos', options=opcoes_anos, index=0)
    
# Lógica dos filtros

if anos != 'Todos':
    df_lms = df_lms[df_lms['Ano'] == anos]
    df_lms_filtrado = df_lms_filtrado[df_lms_filtrado['Ano'] == anos]

# Tabelas

tab_tipo = df_lms.groupby(['Ano', 'Categoria do Gasto'])['Valor'].agg('sum').sort_values(ascending=False).reset_index()
tab_tipo['Valor Formatado'] = tab_tipo['Valor'].apply(lambda x: format_value(x, 'R$'))

tab_func = df_lms.groupby(['Ano', 'Nome'])['Valor'].agg('sum').sort_values(ascending=False).reset_index()
tab_func['Valor Formatado'] = tab_func['Valor'].apply(lambda x: format_value(x, 'R$'))

tab_cc = df_lms.groupby(['Ano', 'Nome CC'])['Valor'].agg('sum').sort_values(ascending=False).reset_index()
tab_cc['Valor Formatado'] = tab_cc['Valor'].apply(lambda x: format_value(x, 'R$'))


# Cores

cores = {
    '2024': '#2596be',
    '2025': '#94AFC5'
    }

# Gráfico

fig_mes = px.line(
    df_lms_filtrado,
    x='Ano_Mes',
    y='Valor',
    text = 'Valor Formatado',
    title='💵 Abertura das despesas',
    color = 'Ano',
    color_discrete_map=cores,
    markers=True  # Adiciona marcadores nos pontos para melhor visualização
)

# Ajustes de layout

fig_mes.update_layout(xaxis_title=None, yaxis_title=None, yaxis=dict(showticklabels=False))
fig_mes.update_traces(textposition='top center')

# Streamlit

aba1,aba2 = st.tabs(['Visão Geral', 'Auditoria'])

with aba1:
    
    st.plotly_chart(fig_mes, use_container_width = True)
    
    numero_itens_aba1 = st.number_input('Quantos funcionários deseja visualizar?', value=5, min_value=1)
    
    coluna1, coluna2 = st.columns(2)
    
    with coluna1:
        
        st.metric('Gasto Total - R$', format_value(df_lms['Valor'].sum(), 'R$'))
        
        top_tipo = df_lms.groupby('Categoria do Gasto')['Valor'].agg('sum').sort_values(ascending=False).reset_index().nlargest(numero_itens_aba1, 'Valor')
        top_tipo = list(top_tipo['Categoria do Gasto'])
        tab_tipo_filtrado = tab_tipo[tab_tipo['Categoria do Gasto'].isin(top_tipo)]
        
        fig_tipo = px.bar(tab_tipo_filtrado,
                          title = f'Distribuição pelo top {numero_itens_aba1} despesas',
                          x = 'Categoria do Gasto',
                          y='Valor',
                          text='Valor Formatado',
                          barmode='stack',
                          color = 'Ano',
                          color_discrete_map=cores)
        
        fig_tipo.update_layout(xaxis_title=None, yaxis_title=None,yaxis=dict(showticklabels=False))
        
        st.plotly_chart(fig_tipo, use_container_width = True)
    
    with coluna2:
        
        st.metric('Quandidade de lançamentos', format_value(df_lms['Documento Contabil'].count()))
        
        top_cc = df_lms.groupby('Nome CC')['Valor'].agg('sum').sort_values(ascending=False).reset_index().nlargest(numero_itens_aba1, 'Valor')
        top_cc = list(top_cc['Nome CC'])
        tab_cc_filtrado = tab_cc[tab_cc['Nome CC'].isin(top_cc)]
        
        fig_cc = px.bar(tab_cc_filtrado,
                        x = 'Nome CC',
                        y = 'Valor',
                        text = 'Valor Formatado',
                        title = f'Distribuição das despesas pelo top {numero_itens_aba1} centros de custos',
                        color = 'Ano',
                        color_discrete_map = cores)
        
        fig_cc.update_layout(xaxis_title=None, yaxis_title=None,yaxis=dict(showticklabels=False))
        
        st.plotly_chart(fig_cc, use_container_width = True)   
    
    top_funcionarios = df_lms.groupby('Nome')['Valor'].agg('sum').sort_values(ascending=False).reset_index().nlargest(numero_itens_aba1,'Valor')
    top_funcionarios = list(top_funcionarios['Nome'])
    tab_func_filtrado = tab_func[tab_func['Nome'].isin(top_funcionarios)]
    
    fig_func = px.bar(tab_func_filtrado,
                      title = f'Total de despesa pelo top {numero_itens_aba1} funcionários',
                      x = 'Nome',
                      y = 'Valor',
                      text = 'Valor Formatado',
                      barmode ='stack',
                      color = 'Ano',
                      color_discrete_map = cores)
    
    fig_func.update_layout(xaxis_title=None, yaxis_title=None,yaxis=dict(showticklabels=False))        
    
    st.plotly_chart(fig_func, use_container_width = True)
    
    
with aba2:
    st.title('Base de despesas para análise - Agente IA 🤖')
    st.dataframe(df_agente)
    st.markdown(f'A tabela possui :blue[{df_agente.shape[0]}] linhas e :blue[{df_agente.shape[1]}] colunas.')
    nome_arquivo = st.text_input('', label_visibility = 'collapsed', value = 'analise_agente_ia')
    nome_arquivo += '.xlsx'
    
    st.download_button(
    label="Fazer download em Excel",
    data=converte_excel(df_agente),
    file_name=f"{nome_arquivo}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    on_click=mensagem_sucesso,
    key="download"
    )
