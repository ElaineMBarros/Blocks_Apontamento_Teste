"""
🤖 DASHBOARD V2 - Análise de Apontamentos com Filtros Avançados
Versão com filtros de período, validador e análise de faixas horárias
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Verificar OpenAI
try:
    from openai import OpenAI
    OPENAI_DISPONIVEL = True
except ImportError:
    OPENAI_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="Análise de Apontamentos V2",
    page_icon="📊",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .alert-low {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .alert-high {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    .alert-ok {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown('<div class="main-header">📊 Análise Inteligente de Apontamentos V2</div>', unsafe_allow_html=True)

# Carregar dados
@st.cache_data
def carregar_dados():
    import glob
    arquivos = glob.glob("resultados/dados_com_duracao_*.csv")
    if arquivos:
        arquivo_mais_recente = max(arquivos)
        # Tentar múltiplos encodings
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(arquivo_mais_recente, encoding=encoding)
                
                # Converter colunas de data
                df['data'] = pd.to_datetime(df['d_dt_data'], errors='coerce')
                df['dt_inicio'] = pd.to_datetime(df['d_dt_inicio_apontamento'], errors='coerce')
                df['dt_fim'] = pd.to_datetime(df['d_dt_fim_apontamento'], errors='coerce')
                
                # IMPORTANTE: Garantir que duracao_horas seja numérica
                df['duracao_horas'] = pd.to_numeric(df['duracao_horas'], errors='coerce')
                
                # Remover registros sem duração válida
                df = df.dropna(subset=['duracao_horas'])
                
                # Corrigir strings com encoding
                for col in df.columns:
                    if df[col].dtype == 'object':
                        try:
                            df[col] = df[col].str.encode('latin-1').str.decode('utf-8')
                        except:
                            pass
                
                return df
            except (UnicodeDecodeError, KeyError):
                continue
        
        # Se nenhum encoding funcionou, usar o último tentado
        df = pd.read_csv(arquivo_mais_recente, encoding='utf-8-sig', errors='ignore')
        df['data'] = pd.to_datetime(df['d_dt_data'], errors='coerce')
        df['dt_inicio'] = pd.to_datetime(df['d_dt_inicio_apontamento'], errors='coerce')
        df['dt_fim'] = pd.to_datetime(df['d_dt_fim_apontamento'], errors='coerce')
        df['duracao_horas'] = pd.to_numeric(df['duracao_horas'], errors='coerce')
        df = df.dropna(subset=['duracao_horas'])
        return df
    return None

def classificar_por_faixa(duracao, faixa_referencia):
    """Classifica apontamento em relação a uma faixa de referência"""
    tolerancia = 0.5  # 30 minutos de tolerância
    
    if duracao < (faixa_referencia - tolerancia):
        return 'Abaixo'
    elif duracao > (faixa_referencia + tolerancia):
        return 'Acima'
    else:
        return 'Normal'

# Carregar dados
df_original = carregar_dados()

if df_original is None:
    st.error("❌ Nenhum dado encontrado! Execute: python analise_duracao_trabalho.py")
    st.stop()

# ==================== SIDEBAR COM FILTROS ====================
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    
    # Filtro de Período
    st.subheader("📅 Período")
    data_min = df_original['data'].min().date()
    data_max = df_original['data'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data Início",
            value=data_min,
            min_value=data_min,
            max_value=data_max
        )
    with col2:
        data_fim = st.date_input(
            "Data Fim",
            value=data_max,
            min_value=data_min,
            max_value=data_max
        )
    
    # Filtro de Validador
    st.subheader("👤 Validador (s_nm_usuario_valida)")
    validadores = ['Todos'] + sorted(df_original['s_nm_usuario_valida'].dropna().unique().tolist())
    validador_selecionado = st.selectbox("Selecione o validador:", validadores)
    
    # Filtro de Funcionário
    st.subheader("👨‍💼 Funcionário (s_nm_recurso)")
    funcionarios = ['Todos'] + sorted(df_original['s_nm_recurso'].dropna().unique().tolist())
    funcionario_selecionado = st.selectbox("Selecione o funcionário:", funcionarios)
    
    # Faixa de Referência
    st.subheader("⏱️ Faixa de Análise")
    faixa_referencia = st.selectbox(
        "Referência de horas:",
        [4.0, 6.0, 8.0],
        index=2,
        format_func=lambda x: f"{int(x)}h00min"
    )
    
    st.markdown("---")
    
    # Botão para aplicar filtros
    aplicar_filtros = st.button("🔄 Aplicar Filtros", use_container_width=True)

# ==================== APLICAR FILTROS ====================
# Filtrar por período
df_filtrado = df_original[
    (df_original['data'].dt.date >= data_inicio) &
    (df_original['data'].dt.date <= data_fim)
].copy()

# Filtrar por validador
if validador_selecionado != 'Todos':
    df_filtrado = df_filtrado[
        df_filtrado['s_nm_usuario_valida'] == validador_selecionado
    ]

# Filtrar por funcionário
if funcionario_selecionado != 'Todos':
    df_filtrado = df_filtrado[
        df_filtrado['s_nm_recurso'] == funcionario_selecionado
    ]

# Classificar por faixa
df_filtrado['classificacao'] = df_filtrado['duracao_horas'].apply(
    lambda x: classificar_por_faixa(x, faixa_referencia)
)

# ==================== MÉTRICAS PRINCIPAIS ====================
st.header("📊 Resumo do Período")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Apontamentos",
        f"{len(df_filtrado):,}",
        delta=f"De {len(df_original):,} total"
    )

with col2:
    abaixo = len(df_filtrado[df_filtrado['classificacao'] == 'Abaixo'])
    st.metric(
        f"⬇️ Abaixo {int(faixa_referencia)}h",
        abaixo,
        delta=f"{abaixo/len(df_filtrado)*100:.1f}%" if len(df_filtrado) > 0 else "0%"
    )

with col3:
    normal = len(df_filtrado[df_filtrado['classificacao'] == 'Normal'])
    st.metric(
        f"✅ Normal (~{int(faixa_referencia)}h)",
        normal,
        delta=f"{normal/len(df_filtrado)*100:.1f}%" if len(df_filtrado) > 0 else "0%"
    )

with col4:
    acima = len(df_filtrado[df_filtrado['classificacao'] == 'Acima'])
    st.metric(
        f"⬆️ Acima {int(faixa_referencia)}h",
        acima,
        delta=f"{acima/len(df_filtrado)*100:.1f}%" if len(df_filtrado) > 0 else "0%"
    )

st.markdown("---")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚨 Alertas",
    "📊 Análise Detalhada",
    "👤 Por Pessoa",
    "📈 Gráficos",
    "📋 Dados Brutos",
    "🤖 Chat IA"
])

# ==================== TAB 1: ALERTAS ====================
with tab1:
    st.header("🚨 Apontamentos Fora do Padrão")
    
    # Apontamentos ABAIXO da faixa
    st.subheader(f"⬇️ Apontamentos Abaixo de {int(faixa_referencia)}h")
    df_abaixo = df_filtrado[df_filtrado['classificacao'] == 'Abaixo'].sort_values('duracao_horas')
    
    if len(df_abaixo) > 0:
        for idx, row in df_abaixo.head(20).iterrows():
            # Garantir que duracao é numérica
            duracao = float(row['duracao_horas'])
            diferenca = faixa_referencia - duracao
            horas = int(duracao)
            minutos = int((duracao - horas) * 60)
            
            # Pegar nome da operação com segurança
            operacao = str(row['s_ds_operacao'])[:50] if pd.notna(row['s_ds_operacao']) else 'N/A'
            nome = str(row['s_nm_recurso']) if pd.notna(row['s_nm_recurso']) else 'N/A'
            
            st.markdown(f"""
            <div class="alert-box alert-low">
                <strong>📅 {row['data'].strftime('%d/%m/%Y')}</strong> - 
                <strong>{nome}</strong><br>
                ⏱️ Duração: {horas}h{minutos:02d}min ({duracao:.2f}h)<br>
                ⚠️ Falta: {diferenca:.2f}h para atingir {int(faixa_referencia)}h<br>
                📝 Operação: {operacao}...
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Nenhum apontamento abaixo da faixa!")
    
    st.markdown("---")
    
    # Apontamentos ACIMA da faixa
    st.subheader(f"⬆️ Apontamentos Acima de {int(faixa_referencia)}h")
    df_acima = df_filtrado[df_filtrado['classificacao'] == 'Acima'].sort_values('duracao_horas', ascending=False)
    
    if len(df_acima) > 0:
        for idx, row in df_acima.head(20).iterrows():
            # Garantir que duracao é numérica
            duracao = float(row['duracao_horas'])
            diferenca = duracao - faixa_referencia
            horas = int(duracao)
            minutos = int((duracao - horas) * 60)
            
            # Pegar nome da operação com segurança
            operacao = str(row['s_ds_operacao'])[:50] if pd.notna(row['s_ds_operacao']) else 'N/A'
            nome = str(row['s_nm_recurso']) if pd.notna(row['s_nm_recurso']) else 'N/A'
            
            st.markdown(f"""
            <div class="alert-box alert-high">
                <strong>📅 {row['data'].strftime('%d/%m/%Y')}</strong> - 
                <strong>{nome}</strong><br>
                ⏱️ Duração: {horas}h{minutos:02d}min ({duracao:.2f}h)<br>
                ⚠️ Excesso: {diferenca:.2f}h acima de {int(faixa_referencia)}h<br>
                📝 Operação: {operacao}...
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Nenhum apontamento acima da faixa!")

# ==================== TAB 2: ANÁLISE DETALHADA ====================
with tab2:
    st.header("📊 Análise Detalhada por Funcionário")
    
    # Análise por funcionário
    analise_func = df_filtrado.groupby('s_nm_recurso').agg({
        'duracao_horas': ['count', 'sum', 'mean', 'min', 'max'],
        'classificacao': lambda x: (x == 'Abaixo').sum()
    }).round(2)
    
    analise_func.columns = ['Qtd', 'Total_h', 'Média_h', 'Min_h', 'Max_h', 'Abaixo_Padrão']
    analise_func = analise_func.sort_values('Total_h', ascending=False)
    
    # Adicionar classificação geral
    analise_func['Status'] = analise_func.apply(
        lambda row: '🔴 Crítico' if row['Abaixo_Padrão'] > row['Qtd'] * 0.3
                    else '🟡 Atenção' if row['Abaixo_Padrão'] > 0
                    else '🟢 OK',
        axis=1
    )
    
    st.dataframe(analise_func, use_container_width=True)
    
    st.markdown("---")
    
    # Análise por dia
    st.subheader("📅 Análise Diária")
    analise_diaria = df_filtrado.groupby(df_filtrado['data'].dt.date).agg({
        'duracao_horas': ['count', 'sum', 'mean'],
        'classificacao': [
            lambda x: (x == 'Abaixo').sum(),
            lambda x: (x == 'Normal').sum(),
            lambda x: (x == 'Acima').sum()
        ]
    }).round(2)
    
    analise_diaria.columns = ['Qtd', 'Total_h', 'Média_h', 'Abaixo', 'Normal', 'Acima']
    
    st.dataframe(analise_diaria, use_container_width=True)

# ==================== TAB 3: ANÁLISE POR PESSOA ====================
with tab3:
    st.header("👤 Análise Detalhada por Pessoa")
    
    if funcionario_selecionado != 'Todos':
        # Análise do funcionário selecionado
        st.subheader(f"📊 Apontamentos de: {funcionario_selecionado}")
        
        # Métricas do funcionário
        col1, col2, col3, col4 = st.columns(4)
        
        pessoa_dados = df_filtrado[df_filtrado['s_nm_recurso'] == funcionario_selecionado]
        
        with col1:
            st.metric("Total de Apontamentos", len(pessoa_dados))
        
        with col2:
            st.metric("Total de Horas", f"{pessoa_dados['duracao_horas'].sum():.1f}h")
        
        with col3:
            st.metric("Média Diária", f"{pessoa_dados['duracao_horas'].mean():.2f}h")
        
        with col4:
            dias_criticos = len(pessoa_dados[pessoa_dados['classificacao'] == 'Abaixo'])
            st.metric("Dias Críticos", dias_criticos, 
                     delta=f"{dias_criticos/len(pessoa_dados)*100:.0f}%" if len(pessoa_dados) > 0 else "0%",
                     delta_color="inverse")
        
        st.markdown("---")
        
        # Tabela por dia com status
        st.subheader("📅 Apontamentos por Dia com Status")
        
        # Agrupar por dia - IMPORTANTE: não usar média, usar TOTAL do dia
        analise_diaria_pessoa = pessoa_dados.groupby(pessoa_dados['data'].dt.date).agg({
            'duracao_horas': ['count', 'sum']
        }).reset_index()
        
        analise_diaria_pessoa.columns = ['Data', 'Qtd_Apt', 'Total_h']
        
        # Classificar cada dia pelo TOTAL de horas do dia (não por apontamento)
        analise_diaria_pessoa['Status_Dia'] = analise_diaria_pessoa['Total_h'].apply(
            lambda x: classificar_por_faixa(x, faixa_referencia)
        )
        
        # Calcular diferença vs meta
        analise_diaria_pessoa['Diferença'] = analise_diaria_pessoa['Total_h'] - faixa_referencia
        analise_diaria_pessoa['Diferença_fmt'] = analise_diaria_pessoa['Diferença'].apply(
            lambda x: f"+{x:.1f}h" if x > 0 else f"{x:.1f}h"
        )
        
        # Adicionar emoji de status
        def get_status_emoji(status):
            if status == 'Abaixo':
                return '🔴 Crítico'
            elif status == 'Acima':
                return '🟡 Atenção'
            else:
                return '🟢 OK'
        
        analise_diaria_pessoa['Status'] = analise_diaria_pessoa['Status_Dia'].apply(get_status_emoji)
        
        # Mostrar tabela
        st.dataframe(
            analise_diaria_pessoa[['Data', 'Qtd_Apt', 'Total_h', 'Diferença_fmt', 'Status']].sort_values('Data', ascending=False),
            use_container_width=True,
            height=400,
            column_config={
                'Data': 'Data',
                'Qtd_Apt': 'Nº Apontamentos',
                'Total_h': st.column_config.NumberColumn('Total Dia', format="%.2f h"),
                'Diferença_fmt': f'vs Meta {int(faixa_referencia)}h',
                'Status': 'Status'
            }
        )
        
        st.markdown("---")
        
        # Gráfico de evolução da pessoa
        st.subheader("📈 Evolução de Horas")
        
        fig = go.Figure()
        
        # Linha de horas trabalhadas
        fig.add_trace(go.Scatter(
            x=analise_diaria_pessoa['Data'],
            y=analise_diaria_pessoa['Total_h'],
            mode='lines+markers',
            name='Horas Trabalhadas',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Linha de referência
        fig.add_trace(go.Scatter(
            x=analise_diaria_pessoa['Data'],
            y=[faixa_referencia] * len(analise_diaria_pessoa),
            mode='lines',
            name=f'Meta ({int(faixa_referencia)}h)',
            line=dict(color='green', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f"Evolução Diária - {funcionario_selecionado}",
            xaxis_title="Data",
            yaxis_title="Horas",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detalhes de cada apontamento
        st.subheader("📋 Todos os Apontamentos Detalhados")
        
        # Adicionar coluna de status individual
        pessoa_dados_display = pessoa_dados.copy()
        pessoa_dados_display['Status'] = pessoa_dados_display['classificacao'].apply(get_status_emoji)
        
        st.dataframe(
            pessoa_dados_display[[
                'data', 'd_dt_inicio_apontamento', 'd_dt_fim_apontamento',
                'duracao_horas', 'Status', 's_ds_operacao'
            ]].sort_values('data', ascending=False),
            use_container_width=True,
            column_config={
                'data': 'Data',
                'd_dt_inicio_apontamento': 'Início',
                'd_dt_fim_apontamento': 'Fim',
                'duracao_horas': 'Duração (h)',
                'Status': 'Status',
                's_ds_operacao': 'Operação'
            },
            height=400
        )
    else:
        st.info("👈 Selecione um funcionário na sidebar para ver análise detalhada")

# ==================== TAB 4: GRÁFICOS ====================
with tab4:
    st.header("📈 Visualizações")
    
    # Gráfico de pizza - Distribuição
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição por Classificação")
        distrib = df_filtrado['classificacao'].value_counts()
        fig = px.pie(
            values=distrib.values,
            names=distrib.index,
            title=f"Referência: {int(faixa_referencia)}h",
            color=distrib.index,
            color_discrete_map={
                'Abaixo': '#ffc107',
                'Normal': '#28a745',
                'Acima': '#dc3545'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Total de Horas por Funcionário")
        top_func = df_filtrado.groupby('s_nm_recurso')['duracao_horas'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=top_func.values,
            y=top_func.index,
            orientation='h',
            title="Top 10 Funcionários",
            labels={'x': 'Horas', 'y': 'Funcionário'},
            color=top_func.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico temporal
    st.subheader("📅 Evolução Temporal")
    temp = df_filtrado.groupby([df_filtrado['data'].dt.date, 'classificacao']).size().reset_index(name='count')
    fig = px.line(
        temp,
        x='data',
        y='count',
        color='classificacao',
        title="Apontamentos por Dia e Classificação",
        color_discrete_map={
            'Abaixo': '#ffc107',
            'Normal': '#28a745',
            'Acima': '#dc3545'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap de horas por dia da semana
    st.subheader("🗓️ Padrão Semanal")
    df_filtrado['dia_semana'] = df_filtrado['data'].dt.day_name()
    heatmap_data = df_filtrado.groupby(['dia_semana', 's_nm_recurso'])['duracao_horas'].mean().reset_index()
    
    # Top 10 funcionários para heatmap
    top_10_func = df_filtrado.groupby('s_nm_recurso')['duracao_horas'].sum().nlargest(10).index
    heatmap_data_filtered = heatmap_data[heatmap_data['s_nm_recurso'].isin(top_10_func)]
    
    if len(heatmap_data_filtered) > 0:
        heatmap_pivot = heatmap_data_filtered.pivot(index='s_nm_recurso', columns='dia_semana', values='duracao_horas')
        fig = px.imshow(
            heatmap_pivot,
            title="Média de Horas por Dia da Semana (Top 10)",
            labels=dict(x="Dia da Semana", y="Funcionário", color="Horas"),
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: DADOS BRUTOS ====================
with tab5:
    st.header("📋 Dados Filtrados")
    
    # Opções de visualização
    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar_classificacao = st.multiselect(
            "Filtrar por classificação:",
            ['Abaixo', 'Normal', 'Acima'],
            default=['Abaixo', 'Acima']
        )
    
    # Filtrar
    if mostrar_classificacao:
        df_exibir = df_filtrado[df_filtrado['classificacao'].isin(mostrar_classificacao)]
    else:
        df_exibir = df_filtrado
    
    # Selecionar colunas para exibir
    colunas_exibir = [
        'data', 's_nm_recurso', 's_nm_usuario_valida',
        'duracao_horas', 'classificacao', 's_ds_operacao'
    ]
    
    st.dataframe(
        df_exibir[colunas_exibir].sort_values('data', ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Botão de export
    csv = df_exibir.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Baixar CSV",
        data=csv,
        file_name=f"apontamentos_{data_inicio}_{data_fim}.csv",
        mime="text/csv"
    )

# ==================== TAB 6: CHAT IA ====================
with tab6:
    st.header("🤖 Chat com IA - Pergunte sobre seus Dados")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if OPENAI_DISPONIVEL:
            # Campo para API Key
            openai_key = st.text_input(
                "🔑 OpenAI API Key:",
                type="password",
                help="Cole sua API key da OpenAI aqui. Obtenha em: https://platform.openai.com/api-keys"
            )
            
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                
                # Inicializar histórico
                if "chat_messages" not in st.session_state:
                    st.session_state.chat_messages = []
                
                # Mostrar histórico
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                # Input do usuário
                if prompt := st.chat_input("Faça uma pergunta sobre os dados filtrados..."):
                    # Adicionar mensagem do usuário
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # Processar com IA
                    with st.chat_message("assistant"):
                        with st.spinner("🤔 Analisando..."):
                            try:
                                client = OpenAI(api_key=openai_key)
                                
                                # Preparar contexto com dados filtrados
                                stats = {
                                    'total_registros': len(df_filtrado),
                                    'periodo': f"{data_inicio} a {data_fim}",
                                    'validador': validador_selecionado,
                                    'faixa_referencia': faixa_referencia,
                                    'total_horas': df_filtrado['duracao_horas'].sum(),
                                    'media_horas': df_filtrado['duracao_horas'].mean(),
                                    'abaixo': len(df_filtrado[df_filtrado['classificacao'] == 'Abaixo']),
                                    'normal': len(df_filtrado[df_filtrado['classificacao'] == 'Normal']),
                                    'acima': len(df_filtrado[df_filtrado['classificacao'] == 'Acima']),
                                    'funcionarios': df_filtrado['s_nm_recurso'].nunique(),
                                    'top_3_func': df_filtrado.groupby('s_nm_recurso')['duracao_horas'].sum().nlargest(3).to_dict()
                                }
                                
                                contexto = f"""
Você é um assistente especializado em análise de dados de apontamentos de trabalho.

DADOS ATUAIS FILTRADOS:
- Período: {stats['periodo']}
- Validador: {stats['validador']}
- Faixa de referência: {stats['faixa_referencia']}h
- Total de apontamentos: {stats['total_registros']}
- Total de horas: {stats['total_horas']:.2f}h
- Média por apontamento: {stats['media_horas']:.2f}h
- Funcionários únicos: {stats['funcionarios']}

DISTRIBUIÇÃO:
- Abaixo da faixa: {stats['abaixo']} ({stats['abaixo']/stats['total_registros']*100:.1f}%)
- Normal: {stats['normal']} ({stats['normal']/stats['total_registros']*100:.1f}%)
- Acima da faixa: {stats['acima']} ({stats['acima']/stats['total_registros']*100:.1f}%)

TOP 3 FUNCIONÁRIOS (horas):
{chr(10).join([f"- {nome}: {horas:.2f}h" for nome, horas in stats['top_3_func'].items()])}

Responda de forma clara, objetiva e profissional. Use dados para fundamentar suas respostas.
Se for perguntado sobre um funcionário específico, analise os dados dele.
Se for sobre tendências, use a análise temporal disponível.
"""
                                
                                completion = client.chat.completions.create(
                                    model="gpt-3.5-turbo",
                                    messages=[
                                        {"role": "system", "content": contexto},
                                        {"role": "user", "content": prompt}
                                    ],
                                    temperature=0.7
                                )
                                
                                resposta = completion.choices[0].message.content
                                st.markdown(resposta)
                                
                                # Salvar no histórico
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": resposta
                                })
                                
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                                st.info("Verifique se a API key está correta e se tem créditos.")
            else:
                st.info("👆 Cole sua API Key da OpenAI acima para começar")
        else:
            st.error("❌ OpenAI não está instalada!")
            st.code("pip install openai", language="bash")
    
    with col2:
        st.subheader("💡 Perguntas Sugeridas")
        
        if openai_key:
            perguntas = [
                "Qual a média de horas do período?",
                "Quem está trabalhando mais?",
                "Quantos apontamentos estão abaixo?",
                "Analise os outliers",
                f"Como está o desempenho?",
                "Quais funcionários precisam de atenção?",
                "Há sobrecarga de trabalho?",
                "Compare os funcionários"
            ]
            
            for i, pergunta in enumerate(perguntas):
                if st.button(f"💬 {pergunta}", key=f"btn_chat_{i}", use_container_width=True):
                    # Adicionar pergunta ao histórico
                    if "chat_messages" not in st.session_state:
                        st.session_state.chat_messages = []
                    
                    st.session_state.chat_messages.append({"role": "user", "content": pergunta})
                    
                    # Processar resposta
                    try:
                        client = OpenAI(api_key=openai_key)
                        
                        # Preparar contexto
                        stats = {
                            'total_registros': len(df_filtrado),
                            'periodo': f"{data_inicio} a {data_fim}",
                            'validador': validador_selecionado,
                            'faixa_referencia': faixa_referencia,
                            'total_horas': df_filtrado['duracao_horas'].sum(),
                            'media_horas': df_filtrado['duracao_horas'].mean(),
                            'abaixo': len(df_filtrado[df_filtrado['classificacao'] == 'Abaixo']),
                            'normal': len(df_filtrado[df_filtrado['classificacao'] == 'Normal']),
                            'acima': len(df_filtrado[df_filtrado['classificacao'] == 'Acima']),
                            'funcionarios': df_filtrado['s_nm_recurso'].nunique(),
                            'top_3_func': df_filtrado.groupby('s_nm_recurso')['duracao_horas'].sum().nlargest(3).to_dict()
                        }
                        
                        contexto = f"""
Você é um assistente especializado em análise de dados de apontamentos de trabalho.

DADOS ATUAIS FILTRADOS:
- Período: {stats['periodo']}
- Validador: {stats['validador']}
- Faixa de referência: {stats['faixa_referencia']}h
- Total de apontamentos: {stats['total_registros']}
- Total de horas: {stats['total_horas']:.2f}h
- Média por apontamento: {stats['media_horas']:.2f}h
- Funcionários únicos: {stats['funcionarios']}

DISTRIBUIÇÃO:
- Abaixo da faixa: {stats['abaixo']} ({stats['abaixo']/stats['total_registros']*100:.1f}%)
- Normal: {stats['normal']} ({stats['normal']/stats['total_registros']*100:.1f}%)
- Acima da faixa: {stats['acima']} ({stats['acima']/stats['total_registros']*100:.1f}%)

TOP 3 FUNCIONÁRIOS (horas):
{chr(10).join([f"- {nome}: {horas:.2f}h" for nome, horas in stats['top_3_func'].items()])}

Responda de forma clara, objetiva e profissional. Use dados para fundamentar suas respostas.
"""
                        
                        completion = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": contexto},
                                {"role": "user", "content": pergunta}
                            ],
                            temperature=0.7
                        )
                        
                        resposta = completion.choices[0].message.content
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": resposta
                        })
                        
                    except Exception as e:
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": f"❌ Erro: {str(e)}\n\nVerifique se a API key está correta e se tem créditos."
                        })
                    
                    st.rerun()
        else:
            st.info("👈 Cole sua API Key primeiro")
        
        st.markdown("---")
        
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
        
        st.markdown("---")
        st.caption("💰 Custo médio: ~$0.001 por pergunta")

# Footer
st.markdown("---")
st.caption(f"📊 Dashboard V2 | Período: {data_inicio} a {data_fim} | Registros: {len(df_filtrado):,} | Validador: {validador_selecionado}")
