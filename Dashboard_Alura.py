# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:03:32 2025

@author: cvieira
"""

#%% Aula Alura

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(layout = 'wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /=1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = "https://labdados.com/produtos"
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

##Barra Lateral
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
    
query_string = {'regiao': regiao.lower(), 'ano': ano}

response = requests.get(url, verify=False, params = query_string)  # Ignore SSL verification e faz a filtragem
dados  = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y', errors = 'coerce')
dados = dados.dropna(subset=['Data da Compra'])

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]


## Tabelas de Receita

receita_estados = dados.groupby('Local da compra')['Preço'].agg('sum')
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra','lat','lon']].merge(receita_estados, left_on= 'Local da compra', right_index= True).sort_values('Preço', ascending = False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].agg('sum').reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month
receita_mensal['Mes'] = receita_mensal['Mes'].apply(lambda x: calendar.month_name[x])

receita_categoria = dados.groupby('Categoria do Produto')['Preço'].agg('sum').sort_values(ascending = False)

## Tabelas de Quantidade de Vendas


## Tabelas de Vendedores

vendedores = dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']).reset_index()


## Gráficos de Receita

fig_mapa_receita = px.scatter_geo(
    receita_estados,
    lat='lat', 
    lon='lon', 
    scope='south america', 
    size='Preço', 
    template='seaborn', 
    hover_name='Local da compra', 
    hover_data={'lat': False, 'lon': False}, 
    title='Receita por estado'
)

fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0,receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(), #o head() é para trazer apenas os 05 primeiros
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True, #colocar o valor acima da barra
                             title = 'Top Estados (Receita)')

fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categoria = px.bar(receita_categoria,
                                text_auto = True,
                                title = 'Receita por Categoria')

fig_receita_categoria.update_layout(yaxis_title = 'Receita')

## Visualização no streamlit

aba1, aba2, aba3, aba4 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores', 'Base de Dados'])

with aba1:
    coluna1, coluna2 = st.columns(2) #estabelece a quantidade de colunas que são visualizadas no site
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #conta as linhas
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categoria, use_container_width = True)
    
with aba2:
    coluna1, coluna2 = st.columns(2) #estabelece a quantidade de colunas que são visualizadas no site
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #conta as linhas

with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5) #mínimo, máximo e valor padrão
    coluna1, coluna2 = st.columns(2) #estabelece a quantidade de colunas que são visualizadas no site
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
        
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0])) #conta as linhas
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)
        
with aba4:
    st.dataframe(dados)
