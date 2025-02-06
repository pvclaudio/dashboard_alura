# -*- coding: utf-8 -*-
"""
Editor Spyder

Este é um arquivo de script temporário.
"""

#%% Agente de PO

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import calendar
import time

st.set_page_config(layout = 'wide')

st.title('AGENTE DE COMPRAS :shopping_trolley:')

def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil', 'milhões', 'bilhões']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'.strip()
        valor /= 1000
    return f'{prefixo} {valor:.2f} trilhões'

def formata_numero2(valor, prefixo=''):
    for unidade in ['', 'mil', 'MM', 'BI']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'.strip()
        valor /= 1000
    return f'{prefixo} {valor:.2f} TRI'

def converte_csv(df):
    return df.to_csv(index = False).encode('utf-8')

def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon = "✅" )
    time.sleep(5)
    sucesso.empty()

# Read the Excel file correctly
# df = pd.read_excel("auditoria_pedidos.xlsx", engine="openpyxl")
df = pd.read_csv("base_pedidos.csv")
df['Data do Pedido'] = pd.to_datetime(df['Data do Pedido'], errors = 'coerce')
df.rename(columns={'Valor PO - R$': 'Valor'}, inplace=True)
data_min = df['Data do Pedido'].min().strftime('%d/%m/%Y')  # Formata como dd/mm/yyyy
data_max = df['Data do Pedido'].max().strftime('%d/%m/%Y')  # Formata como dd/mm/yyyy
df['Ano'] = df['Data do Pedido'].dt.year
df_fup = pd.read_excel('controle_fups.xlsx', sheet_name='2024', engine="openpyxl", header=0)
df_fup['Status'] = df_fup['Status'].replace(
    {'Concluído - No Prazo': 'Concluído', 'Concluído - Fora do Prazo': 'Concluído'}
)
df_fup = df_fup.drop(columns='Titulo')
df_fup['Status'] = df_fup['Status'].str.strip()

# Sidebar - Filtros
st.sidebar.title('Filtros')

opcoes_fornecedor = ["Todos"] + list(df['Nome Fornecedor'].dropna().unique())
opcoes_area = ["Todos"] + list(df['Area Autorizador'].dropna().unique())
opcoes_contabil = ["Todos"] + list(df['Tipo Contábil'].dropna().unique())
opcoes_ano = ['Todos'] + [2025] + list(df_fup['Ano'].dropna().unique())

fornecedor = st.sidebar.selectbox('Selecione o Fornecedor', opcoes_fornecedor, index=0)
area = st.sidebar.selectbox('Selecione a Área', opcoes_area, index=0, key='selecionar area')
tipo_contabil = st.sidebar.selectbox('Selecione o tipo contábil', opcoes_contabil, index=0)
ano_escolhido = st.sidebar.selectbox('Selecione o Ano', opcoes_ano, index=0, key='selecionar ano')
data_pedido = st.sidebar.date_input(
    'Selecione a Data',
    value=(df['Data do Pedido'].min(), df['Data do Pedido'].max()),  # Mantém os valores originais como datetime
    key='data_pedido'
)


if fornecedor != "Todos":
    df = df[df['Nome Fornecedor'] == fornecedor]

if area != "Todos":
    df = df[df['Area Autorizador'] == area]

if tipo_contabil != "Todos":
    df = df[df['Tipo Contábil'] == tipo_contabil]
    
if ano_escolhido != 'Todos':
    df = df[df['Ano'] == ano_escolhido]
    df_fup = df_fup[df_fup['Ano'] == ano_escolhido]
    
# Verificar se o usuário deixou o filtro vazio ou inválido
if not data_pedido or len(data_pedido) != 2 or data_pedido[0] > data_pedido[1]:
    st.sidebar.warning("Nenhuma data válida foi selecionada. Exibindo todos os dados.")
else:
    # Aplicar filtro de data apenas se válido
    df = df[
        (df['Data do Pedido'] >= pd.to_datetime(data_pedido[0])) &
        (df['Data do Pedido'] <= pd.to_datetime(data_pedido[1]))
    ]

# Tabelas

pedidos_fornecedor = df.groupby(['Ano', 'Nome Fornecedor'])['Valor'].agg(['sum', 'count']) \
    .rename(columns={'sum': 'Valor Total', 'count': 'Quantidade'}) \
    .sort_values(by=['Ano', 'Valor Total'], ascending=[True, False]) \
    .reset_index()
pedidos_fornecedor['Valor Total Formatado'] = pedidos_fornecedor['Valor Total'].apply(lambda x: formata_numero2(x, 'R$'))
pedidos_fornecedor['Ano'] = pedidos_fornecedor['Ano'].astype(str)

pedidos_mensal = df.copy()
pedidos_mensal['Ano'] = pedidos_mensal['Data do Pedido'].dt.year
pedidos_mensal['Mes'] = pedidos_mensal['Data do Pedido'].dt.month.apply(lambda x: calendar.month_name[x])
pedidos_mensal = pedidos_mensal.groupby(['Ano', 'Mes'], as_index=False)['Valor'].agg('sum')
meses_ordem = list(calendar.month_name[1:])
pedidos_mensal['Mes'] = pd.Categorical(pedidos_mensal['Mes'], categories=meses_ordem, ordered=True)
pedidos_mensal = pedidos_mensal.sort_values(['Ano', 'Mes']).reset_index(drop=True)

pedidos_area = df.groupby(['Ano', 'Area Autorizador'])['Valor'].agg('sum').reset_index()
pedidos_area['Valor'] = round(pedidos_area['Valor'], 0)
pedidos_area['Valor Formatado'] = pedidos_area['Valor'].apply(lambda x: formata_numero2(x, 'R$'))
pedidos_area = pedidos_area.sort_values(['Ano', 'Valor'], ascending=[True, False]).reset_index(drop=True)
pedidos_area['Ano'] = pedidos_area['Ano'].astype(str)

df_compliance = df.copy()
df_compliance['Check Compliance'] = df_compliance['Check Compliance'].fillna('Baixo')

pedidos_compliance = df_compliance.groupby('Check Compliance')['Numero PO'].agg('count').reset_index()
pedidos_compliance['Numero Formatado'] = pedidos_compliance['Numero PO'].apply(lambda x: formata_numero2(x))

pedidos_compliance_alto = df_compliance[df_compliance['Check Compliance'].isin(['Alto','Médio'])].groupby(['Ano','Nome Fornecedor'])['Valor'].agg('sum').sort_values(ascending=False).reset_index()
pedidos_compliance_alto['Valor Formatado'] = pedidos_compliance_alto['Valor'].apply(lambda x: formata_numero2(x, 'R$'))
pedidos_compliance_alto['Ano'] = pedidos_compliance_alto['Ano'].astype(str)

pedidos_compliance_alto_area = df_compliance[df_compliance['Check Compliance'] == 'Alto'].groupby(['Ano','Area Autorizador'])['Valor'].agg('sum').sort_values(ascending=False).reset_index()
pedidos_compliance_alto_area['Valor Formatado'] = pedidos_compliance_alto_area['Valor'].apply(lambda x: formata_numero2(x, 'R$'))
pedidos_compliance_alto_area['Ano'] = pedidos_compliance_alto_area['Ano'].astype(str)

# Gráficos
cores = {
    'Alto': '#B22222',    
    'Médio': '#FFD700', 
    'Baixo': '#228B22'   
}

cores2 = {
    'Inefetivo': '#B22222',     
    'Efetivo': '#228B22'   
}

cores3 = {
    '2024.0':"#174A7E",
    '2025.0':'#4A81BF'
    }

cores4 = {
    2024 :"#174A7E",
    2025 :'#4A81BF'
    }

cores5 = {
    'Concluído': '#174A7E',
    'Em andamento': '#4A81BF'
    }

## ABA1                 

fig_pedidos_mensal = px.line(pedidos_mensal,
                             x = 'Mes',
                             y = 'Valor',
                             title = 'Gastos por mês',
                             color = 'Ano',
                             color_discrete_map = cores4,
                             markers = True)


# Remover os labels dos eixos X e Y

fig_pedidos_mensal.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    yaxis=dict(range=[0, pedidos_mensal['Valor'].max()*1.1])
)

# Display the data in Streamlit

aba1, aba2, aba3, aba4 = st.tabs(['Visão Geral dos Pedidos', 'Compliance', 'Auditoria', 'Follow UPs'])

with aba1:
    st.plotly_chart(fig_pedidos_mensal,use_container_width = True)
    numero_fornecedor = st.number_input('Quantos fornecedores deseja visualizar?',min_value = 1, value = 5, key= 'numero_fornecedor')
    numero_fornecedor = min(numero_fornecedor, len(pedidos_fornecedor))
    
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Gasto Total - R$', formata_numero(df['Valor'].sum(), 'R$'))
        
        top_fornecedores = pedidos_fornecedor.groupby('Nome Fornecedor')['Valor Total'].sum().nlargest(numero_fornecedor).index
        pedidos_fornecedor_filtrados = pedidos_fornecedor[pedidos_fornecedor['Nome Fornecedor'].isin(top_fornecedores)]
        y_max_pedidos_fornecedor = pedidos_fornecedor_filtrados.groupby(['Nome Fornecedor', 'Ano'])['Valor Total'].sum().max() * 1.4
    
        fig_pedidos_fornecedor = px.bar(
            pedidos_fornecedor_filtrados,
            x='Nome Fornecedor',
            y='Valor Total',  # O eixo Y mantém os valores numéricos para não afetar a escala
            text='Valor Total Formatado',  # Exibir valores formatados nos rótulos
            title=f'Gastos pelo Top {numero_fornecedor}',
            color = 'Ano',
            color_discrete_map = cores3,
            barmode='stack'
        )
        
        fig_pedidos_fornecedor.update_layout(
            xaxis_title=None,
            yaxis_title=None
        )

        fig_pedidos_fornecedor.update_yaxes(title=None, showticklabels=False, range=[0, y_max_pedidos_fornecedor])
        
        st.plotly_chart(fig_pedidos_fornecedor, use_container_width = True)
        
    with coluna2:
        st.metric('Quantidade de Pedidos', formata_numero(df.shape[0]))
        
        top_areas = pedidos_area.groupby('Area Autorizador')['Valor'].sum().nlargest(numero_fornecedor).index
        pedidos_area_filtrados = pedidos_area[pedidos_area['Area Autorizador'].isin(top_areas)]
        y_max_pedidos_area = pedidos_area_filtrados.groupby(['Area Autorizador', 'Ano'])['Valor'].sum().max() * 1.4
        
        fig_pedidos_area = px.bar(
            pedidos_area_filtrados,
            x='Area Autorizador',
            y='Valor',  # Usar a coluna numérica para manter a escala correta
            title=f'Gastos por área (Top {numero_fornecedor})',
            color = 'Ano',
            color_discrete_map = cores3,
            barmode='stack',
            text='Valor Formatado'  # Exibir os valores formatados como rótulos
        )
        
        fig_pedidos_area.update_layout(
            xaxis_title=None,
            yaxis_title=None
        )

        fig_pedidos_area.update_yaxes(title=None, showticklabels=False,range=[0, y_max_pedidos_area])
        
        st.plotly_chart(fig_pedidos_area,  use_container_width = True)
        
        
with aba2: 
    numero_fornecedores = st.number_input('Quantos itens deseja visualizar?',min_value = 1, value = 5, key= 'numero_fornecedores')
    numero_fornecedores = min(numero_fornecedores, len(pedidos_fornecedor))
    
    fig_compliance_riscos = px.bar(pedidos_compliance,
                                   x = 'Check Compliance',
                                   y = 'Numero PO',
                                   text = 'Numero Formatado',
                                   title = 'Distribuição dos pedidos - riscos',
                                   color = 'Check Compliance',
                                   color_discrete_map = cores)
    
    top_fornecedor_alto = pedidos_compliance_alto.groupby('Nome Fornecedor')['Valor'].sum().nlargest(numero_fornecedores).index
    pedidos_compliance_alto_filtrados = pedidos_compliance_alto[pedidos_compliance_alto['Nome Fornecedor'].isin(top_fornecedor_alto)]
    y_max_pedidos_compliance_alto = pedidos_compliance_alto_filtrados.groupby(['Nome Fornecedor', 'Ano'])['Valor'].sum().max() * 1.4

    fig_fornecedor_alto = px.bar(pedidos_compliance_alto_filtrados,
                                 x = 'Nome Fornecedor',
                                 y = 'Valor',
                                 text = 'Valor Formatado',
                                 title = f'Top {numero_fornecedores} fornecedores de risco',
                                 color = 'Ano',
                                 color_discrete_map = cores3,
                                 barmode='stack')
    
    top_fornecedor_alto_area = pedidos_compliance_alto_area.groupby('Area Autorizador')['Valor'].sum().nlargest(numero_fornecedores).index
    pedidos_compliance_alto_area_filtrados = pedidos_compliance_alto_area[pedidos_compliance_alto_area['Area Autorizador'].isin(top_fornecedor_alto_area)]
    y_max_pedidos_compliance_alto_area = pedidos_compliance_alto_area_filtrados.groupby(['Area Autorizador', 'Ano'])['Valor'].sum().max() * 1.4

    fig_fornecedor_alto_area = px.bar(pedidos_compliance_alto_area_filtrados,
                                 x = 'Area Autorizador',
                                 y = 'Valor',
                                 text = 'Valor Formatado',
                                 title = f'Top {numero_fornecedores} áreas de maior risco',
                                 color = 'Ano',
                                 color_discrete_map = cores3,
                                 barmode='stack')
    
    fig_compliance_riscos.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False
    )

    fig_compliance_riscos.update_yaxes(title=None, showticklabels=False)
    
    fig_fornecedor_alto.update_layout(
        xaxis_title=None,
        yaxis_title=None
    )
    
    fig_fornecedor_alto.update_yaxes(title=None, showticklabels=False, range=[0, y_max_pedidos_compliance_alto])

    fig_fornecedor_alto_area.update_layout(
        xaxis_title=None,
        yaxis_title=None
    )
    
    fig_fornecedor_alto_area.update_yaxes(title=None, showticklabels=False, range=[0, y_max_pedidos_compliance_alto_area])
    
    st.plotly_chart(fig_compliance_riscos, use_container_width = True)
    coluna1, coluna2 = st.columns(2)
    
    with coluna1:
        st.plotly_chart(fig_fornecedor_alto, use_container_width = True)

    with coluna2:
        st.plotly_chart(fig_fornecedor_alto_area, use_container_width = True)


with aba3:
    coluna1, coluna2 = st.columns(2)
    
    colunas_desejadas = [
    "Numero PO", "Tipo PO", "Tipo Contábil", "Valor", "Aprovador",
    "Numero Fornecedor", "Nome Fornecedor", "Area Autorizador", "Check Compliance"]
    
    st.header('Pedidos Inefetivos')
    
    df_filtrado = df[df['Check Alcada'] == 'Inefetivo'][colunas_desejadas].reset_index(drop=True)
    df_filtrado = df_filtrado.dropna(subset=['Area Autorizador'])
    df_filtrado['Check Compliance'] = df_filtrado['Check Compliance'].fillna('Baixo')
    st.dataframe(df_filtrado)
    st.markdown(f'A tabela possui :blue[{df_filtrado.shape[0]}] linhas e :blue[{df_filtrado.shape[1]}] colunas.')
    
    df_inefetivo = df[df['Check Alcada'] == 'Inefetivo'].groupby(['Area Autorizador','Tipo Contábil'])['Numero PO'].agg('count').reset_index().sort_values('Numero PO',ascending = False)
    nome_arquivo = st.text_input('', label_visibility = 'collapsed', value = 'Digite o nome do seu arquivo')
    nome_arquivo += '.csv'
    
    st.download_button('Fazer download em csv', 
                       data = converte_csv(df_inefetivo), 
                       file_name = nome_arquivo, 
                       mime = 'text/csv', 
                       on_click = mensagem_sucesso)
    
    st.header('Análise do Agente (IA)')
    
    df_agente = pd.read_excel('auditoria_pedidos.xlsx', engine='openpyxl').drop(columns=['ID'])
    st.dataframe(df_agente)
    st.markdown(f'A tabela possui :blue[{df_agente.shape[0]}] linhas e :blue[{df_agente.shape[1]}] colunas.')
    
    nome_arquivo2 = st.text_input('', label_visibility = 'collapsed', value = 'Digite o nome do seu arquivo.')
    nome_arquivo2 += '.csv'
    st.download_button('Fazer download em csv', 
                       data = converte_csv(df_agente), 
                       file_name = nome_arquivo2, 
                       mime = 'text/csv', 
                       on_click = mensagem_sucesso)
    
    
    
    with coluna1:
        efetividade_pedidos = df.groupby('Check Alcada')['Numero PO'].agg('count').reset_index()
        fig_efetividade_pedidos = px.pie(efetividade_pedidos,
                                         names='Check Alcada',
                                         title = '% de Efetividade',
                                         values='Numero PO',
                                         color = 'Check Alcada',
                                         color_discrete_map=cores2)
        st.plotly_chart(fig_efetividade_pedidos, use_container_width = True)
        
    
    with coluna2:
        df_inefetivo = df[df['Check Alcada'] == 'Inefetivo'].groupby(['Area Autorizador','Tipo Contábil'])['Numero PO'].agg('count').reset_index().sort_values('Numero PO',ascending = False)
        fig_pedidos_inefetivos = px.bar(df_inefetivo,
                                        x = 'Area Autorizador',
                                        y = 'Numero PO',
                                        color = 'Tipo Contábil',
                                        title = 'Distribuição dos inefetivos',
                                        text_auto = True,
                                        range_y = (0,df_inefetivo['Numero PO'].max()*1.3)
                                        )
        fig_pedidos_inefetivos.update_layout(
            xaxis_title=None,
            yaxis_title=None
        )
        fig_pedidos_inefetivos.update_yaxes(title=None, showticklabels=False)
        fig_pedidos_inefetivos.update_traces(textposition='inside', textangle=0)
        st.plotly_chart(fig_pedidos_inefetivos, use_container_width = True)

with aba4:
    
    coluna1, coluna2 = st.columns(2)
    
    with coluna1:
        
        lista_auditoria = ['Todas'] + list(df_fup['Auditoria'].dropna().unique())
        lista_criticidade = ['Todas'] + list(df_fup['Risco'].dropna().str.strip().unique())
        
        filtro_auditoria = st.selectbox('Selecione a auditoria que deseja visualizar', lista_auditoria, index=0)
        filtro_criticidade = st.selectbox('Selecione a criticidade que deseja visualizar', lista_criticidade, index=0)
        
        if filtro_auditoria != 'Todas':
            df_fup = df_fup[df_fup['Auditoria'] == filtro_auditoria]
        if filtro_criticidade != 'Todas':
            df_fup = df_fup[df_fup['Risco'] == filtro_criticidade]
    
        st.metric('Total Concluído', formata_numero(df_fup[df_fup['Status'] == 'Concluído'].shape[0]))
        
    with coluna2:
        
        lista_responsaveis = ['Todos'] + list(df_fup['Responsavel'].dropna().unique())
        lista_status = ['Todos'] + list(df_fup['Status'].dropna().unique())
        
        filtro_responsaveis = st.selectbox('Selecione o responsável da área auditada', lista_responsaveis, index=0)
        filtro_status = st.selectbox('Selecione o status do plano de ação', lista_status, index=0)
        
        if filtro_responsaveis != 'Todos':
            df_fup = df_fup[df_fup['Responsavel'] == filtro_responsaveis]
        if filtro_status != 'Todos':
            df_fup = df_fup[df_fup['Status'] == filtro_status]
            
        st.metric('Total Em andamento', formata_numero(df_fup[df_fup['Status'] == 'Em andamento'].shape[0]))
        
    tabela_auditoria = df_fup.groupby(['Ano', 'Auditoria', 'Status'])['ID'].agg('count').sort_values(ascending = False).reset_index()
    
    y_max_auditoria = df_fup.groupby(['Ano', 'Auditoria', 'Status'])['ID'].count().max() *1.5
    
    fig_auditoria = px.bar(
        tabela_auditoria,
        x='Auditoria',
        y='ID',
        title = 'Status dos Planos de Ação',
        text_auto=True,
        barmode='stack',
        color='Status',
        color_discrete_map=cores5)
    
    fig_auditoria.update_yaxes(title=None, showticklabels=False, range=[0, y_max_auditoria])  # Remove título e ticks do eixo Y
    fig_auditoria.update_xaxes(title=None)  # Remove o título do eixo X, mas mantém os rótulos
    fig_auditoria.update_traces(textposition='inside', textangle=0)  # Centralizar os números dentro das barras
    
    st.plotly_chart(fig_auditoria, use_container_width = True)
    
    st.header('Controle de Planos de Ação')
    st.dataframe(df_fup)
    st.markdown(f'A tabela possui :blue[{df_fup.shape[0]}] linhas e :blue[{df_fup.shape[1]}] colunas.')
    nome_arquivo3 = st.text_input('', label_visibility = 'collapsed', value = 'Digite o nome do seu arquivo.', key='nome arquivo fup')
    nome_arquivo3 += '.csv'
    st.download_button('Fazer download em csv', 
                       data = converte_csv(df_fup), 
                       file_name = nome_arquivo3, 
                       mime = 'text/csv', 
                       on_click = mensagem_sucesso,key='fup')



