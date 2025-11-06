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
from scipy import stats
import numpy as np
from scipy import stats

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
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #dee2e6;
        height: 500px;
        overflow-y: auto;
        display: flex;
        flex-direction: column-reverse;
    }
    .chat-message {
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .chat-message.user {
        justify-content: flex-end;
    }
    .chat-message.assistant {
        justify-content: flex-start;
    }
    .message-content {
        max-width: 80%;
        padding: 0.75rem 1rem;
        border-radius: 15px;
        word-wrap: break-word;
    }
    .message-content.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 5px;
    }
    .message-content.assistant {
        background-color: white;
        border: 1px solid #dee2e6;
        border-bottom-left-radius: 5px;
    }
    .chat-header {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Função para carregar dados
@st.cache_data(ttl=300)  # Cache por 5 minutos apenas
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
                
                # ========== NOVA LÓGICA: AGRUPAR POR DIA + FUNCIONÁRIO ==========
                # Manter dados originais para referência
                df_original = df.copy()
                
                # Agrupar por funcionário + dia e somar as horas
                df_agrupado = df.groupby(['s_nm_recurso', 'data', 's_nm_usuario_valida']).agg({
                    'duracao_horas': 'sum',  # SOMAR as horas do dia
                    'd_dt_inicio_apontamento': 'min',  # Primeiro apontamento do dia
                    'd_dt_fim_apontamento': 'max',     # Último apontamento do dia
                    's_ds_operacao': lambda x: f"{len(x)} apontamentos: " + "; ".join(x.astype(str).head(3)) + ("..." if len(x) > 3 else ""),  # Concatenar operações
                    'd_dt_data': 'first'  # Manter a data
                }).reset_index()
                
                # Renomear colunas para manter compatibilidade
                df_agrupado.columns = ['s_nm_recurso', 'data', 's_nm_usuario_valida', 'duracao_horas', 
                                     'd_dt_inicio_apontamento', 'd_dt_fim_apontamento', 's_ds_operacao', 'd_dt_data']
                
                # Corrigir strings com encoding
                for col in df_agrupado.columns:
                    if df_agrupado[col].dtype == 'object':
                        try:
                            df_agrupado[col] = df_agrupado[col].str.encode('latin-1').str.decode('utf-8')
                        except:
                            pass
                
                # Adicionar metadados sobre a agregação
                df_agrupado['total_apontamentos_dia'] = df.groupby(['s_nm_recurso', 'data']).size().values
                df_agrupado['tipo_analise'] = 'AGRUPADO_POR_DIA'
                
                # ========== AJUSTES SOLICITADOS PELO CLIENTE ==========
                
                # AJUSTE 1: IDENTIFICAR DIA ÚTIL vs NÃO ÚTIL
                # Seg-Sex = Dia Útil (0-4), Sáb-Dom = Não Útil (5-6)
                df_agrupado['dia_semana_num'] = df_agrupado['data'].dt.dayofweek
                df_agrupado['tipo_dia'] = df_agrupado['dia_semana_num'].apply(
                    lambda x: '📅 Dia Útil' if x < 5 else '🏖️ Fim de Semana'
                )
                df_agrupado['nome_dia'] = df_agrupado['data'].dt.day_name()
                df_agrupado['eh_dia_util'] = df_agrupado['dia_semana_num'] < 5
                
                # AJUSTE 2: DESCONTO DE 1H DE ALMOÇO
                # Descontar 1h de almoço das horas trabalhadas
                df_agrupado['duracao_bruta'] = df_agrupado['duracao_horas']  # Salvar original
                df_agrupado['horas_almoco'] = 1.0  # 1h de almoço
                df_agrupado['duracao_liquida'] = (df_agrupado['duracao_horas'] - df_agrupado['horas_almoco']).clip(lower=0)
                
                # AJUSTE 3: RECALCULAR HORAS EXTRAS (após desconto de almoço)
                # Horas extras = tudo acima de 8h APÓS descontar 1h de almoço
                df_agrupado['horas_extras'] = df_agrupado['duracao_liquida'].apply(
                    lambda x: max(0, x - 8) if x > 8 else 0
                )
                
                # Calcular horas normais (até 8h)
                df_agrupado['horas_normais'] = df_agrupado['duracao_liquida'].apply(
                    lambda x: min(8, x)
                )
                
                # Calcular horas pagas (horas normais + extras com adicional 50%)
                df_agrupado['horas_pagas'] = df_agrupado['horas_normais'] + (df_agrupado['horas_extras'] * 1.5)
                
                # Indicadores visuais
                df_agrupado['possui_hora_extra'] = df_agrupado['horas_extras'] > 0
                df_agrupado['classificacao_jornada'] = df_agrupado['duracao_liquida'].apply(
                    lambda x: '✅ Jornada Completa' if 7.5 <= x <= 8.5 
                             else '⚠️ Jornada Reduzida' if x < 7.5
                             else '🔴 Hora Extra'
                )
                
                return df_agrupado
            except (UnicodeDecodeError, KeyError):
                continue
        
        # Se nenhum encoding funcionou, usar o último tentado
        df = pd.read_csv(arquivo_mais_recente, encoding='utf-8-sig', errors='ignore')
        df['data'] = pd.to_datetime(df['d_dt_data'], errors='coerce')
        df['duracao_horas'] = pd.to_numeric(df['duracao_horas'], errors='coerce')
        df = df.dropna(subset=['duracao_horas'])
        return df
    return None

# Carregar dados
df_original = carregar_dados()

if df_original is None:
    st.error("❌ Nenhum dado encontrado! Execute: python analise_duracao_trabalho.py")
    st.stop()

def classificar_por_faixa(duracao, faixa_referencia):
    """Classifica apontamento em relação a uma faixa de referência"""
    tolerancia = 0.5  # 30 minutos de tolerância
    
    if duracao < (faixa_referencia - tolerancia):
        return 'Abaixo'
    elif duracao > (faixa_referencia + tolerancia):
        return 'Acima'
    else:
        return 'Normal'

def render_chat_lateral(df_filtrado, data_inicio, data_fim, validador_selecionado, faixa_referencia):
    """Renderiza o componente de chat lateral"""
    st.markdown('<div class="chat-header">🤖 Chat IA - Análise Inteligente</div>', unsafe_allow_html=True)
    
    if OPENAI_DISPONIVEL:
        # Tentar carregador API Key nesta ordem de prioridade:
        # 1. Streamlit Cloud secrets (produção)
        # 2. Variáveis de ambiente (local)
        # 3. Input manual (fallback)
        
        openai_key = None
        
        try:
            # Streamlit Cloud secrets (produção)
            openai_key = st.secrets["OPENAI_API_KEY"]
            st.success("🔑 API Key carregada (Streamlit Cloud)")
        except:
            try:
                # Variáveis de ambiente (local)
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    st.success("🔑 API Key carregada (Variável de ambiente)")
            except:
                pass
        
        if not openai_key:
            # Campo para API Key manual (fallback para desenvolvimento local)
            openai_key = st.text_input(
                "🔑 OpenAI API Key:",
                type="password",
                help="Cole sua API key da OpenAI aqui",
                key="chat_api_key"
            )
        
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            
            # Perguntas sugeridas
            st.subheader("💡 Perguntas Rápidas")
            
            perguntas = [
                "Resumo dos dados atuais",
                "Quem trabalha mais?",
                "Há sobrecarga?",
                "Tendências do período",
                "Outliers detectados"
            ]
            
            for pergunta in perguntas:
                # Evitar cliques múltiplos
                if st.button(f"💬 {pergunta}", key=f"btn_{pergunta.replace(' ', '_').replace('?', '')}", use_container_width=True):
                    if not ("processing_chat" in st.session_state and st.session_state.processing_chat):
                        processar_pergunta_chat(pergunta, df_filtrado, data_inicio, data_fim, validador_selecionado, faixa_referencia, openai_key)
            
            st.markdown("---")
            
            # Histórico de chat em formato de conversa (ACIMA)
            if "chat_messages" in st.session_state and st.session_state.chat_messages:
                st.subheader("💬 Histórico")
                
                # Container com rolagem usando st.container
                with st.container():
                    # Mostrar mensagens em ordem (mais antigas primeiro, mais recentes embaixo)
                    messages = st.session_state.chat_messages
                    for msg in messages[-10:]:  # Últimas 10 mensagens
                        role = msg["role"]
                        content = msg["content"]
                        
                        if role == "user":
                            # Mensagem do usuário (direita)
                            st.markdown(f"""
                            <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                            color: white; 
                                            padding: 0.75rem 1rem; 
                                            border-radius: 15px; 
                                            border-bottom-right-radius: 5px;
                                            max-width: 80%;
                                            word-wrap: break-word;">
                                    {content}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        elif role == "assistant":
                            # Mensagem da IA (esquerda)
                            st.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
                                <div style="background-color: white; 
                                            border: 1px solid #dee2e6;
                                            padding: 0.75rem 1rem; 
                                            border-radius: 15px; 
                                            border-bottom-left-radius: 5px;
                                            max-width: 80%;
                                            word-wrap: break-word;">
                                    {content}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            # Input personalizado com formulário (EMBAIXO)
            with st.form("chat_form", clear_on_submit=True):
                col_input, col_button = st.columns([4, 1])
                with col_input:
                    pergunta_input = st.text_input("✍️ Sua pergunta:", placeholder="Ex: Como está o desempenho da equipe?", label_visibility="collapsed")
                with col_button:
                    submitted = st.form_submit_button("📤 Enviar", use_container_width=True)
                
                if submitted and pergunta_input and not ("processing_chat" in st.session_state and st.session_state.processing_chat):
                    processar_pergunta_chat(pergunta_input, df_filtrado, data_inicio, data_fim, validador_selecionado, faixa_referencia, openai_key)
            
            # Botão para limpar
            if st.button("🗑️ Limpar Chat", use_container_width=True):
                st.session_state.chat_messages = []
                if "processing_chat" in st.session_state:
                    del st.session_state.processing_chat
                st.rerun()
        else:
            st.info("👆 Cole sua API Key acima")
    else:
        st.error("❌ OpenAI não instalada!")

def processar_pergunta_chat(pergunta, df_filtrado, data_inicio, data_fim, validador_selecionado, faixa_referencia, openai_key):
    """Processa pergunta do chat e gera resposta"""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Evitar processamento duplicado
    if "processing_chat" in st.session_state and st.session_state.processing_chat:
        return
    
    # Marcar como processando
    st.session_state.processing_chat = True
    
    try:
        # Feedback visual de processamento
        with st.spinner("🤖 Processando sua pergunta..."):
            client = OpenAI(api_key=openai_key)
            
            # Preparar contexto com dados filtrados
            total_horas_brutas = df_filtrado['duracao_bruta'].sum() if 'duracao_bruta' in df_filtrado.columns else df_filtrado['duracao_horas'].sum()
            total_horas_liquidas = df_filtrado['duracao_liquida'].sum() if 'duracao_liquida' in df_filtrado.columns else 0
            total_horas_extras = df_filtrado['horas_extras'].sum() if 'horas_extras' in df_filtrado.columns else 0
            total_horas_pagas = df_filtrado['horas_pagas'].sum() if 'horas_pagas' in df_filtrado.columns else 0
            
            # Estatísticas de dias úteis vs não úteis
            dias_uteis = len(df_filtrado[df_filtrado['eh_dia_util'] == True]) if 'eh_dia_util' in df_filtrado.columns else 0
            dias_nao_uteis = len(df_filtrado[df_filtrado['eh_dia_util'] == False]) if 'eh_dia_util' in df_filtrado.columns else 0
            
            stats = {
                'total_registros': len(df_filtrado),
                'periodo': f"{data_inicio} a {data_fim}",
                'validador': validador_selecionado,
                'faixa_referencia': faixa_referencia,
                'total_horas_brutas': total_horas_brutas,
                'total_horas_liquidas': total_horas_liquidas,
                'total_horas_extras': total_horas_extras,
                'total_horas_pagas': total_horas_pagas,
                'media_horas': df_filtrado['duracao_horas'].mean(),
                'abaixo': len(df_filtrado[df_filtrado['classificacao'] == 'Abaixo']),
                'normal': len(df_filtrado[df_filtrado['classificacao'] == 'Normal']),
                'acima': len(df_filtrado[df_filtrado['classificacao'] == 'Acima']),
                'funcionarios': df_filtrado['s_nm_recurso'].nunique(),
                'dias_uteis': dias_uteis,
                'dias_nao_uteis': dias_nao_uteis,
                'top_3_func': df_filtrado.groupby('s_nm_recurso')['duracao_horas'].sum().nlargest(3).to_dict()
            }
            
            contexto = f"""
Você é um assistente especializado em análise de dados de apontamentos de trabalho.
Forneça respostas detalhadas e estruturadas baseadas nos dados apresentados.

REGRAS DE CÁLCULO APLICADAS:
✅ Desconto de 1h de almoço por dia (já aplicado nos dados)
✅ Classificação de dia útil (seg-sex) vs final de semana (sáb-dom)
✅ Horas extras = tudo acima de 8h APÓS desconto do almoço
✅ Horas pagas = horas normais + (horas extras × 1.5)

DADOS ATUAIS FILTRADOS:
- Período: {stats['periodo']}
- Validador: {stats['validador']}
- Faixa de referência: {stats['faixa_referencia']}h
- Total de jornadas: {stats['total_registros']}
- Dias úteis: {stats['dias_uteis']} | Fins de semana: {stats['dias_nao_uteis']}
- Funcionários únicos: {stats['funcionarios']}

HORAS TRABALHADAS:
- Horas brutas (com almoço): {stats['total_horas_brutas']:.2f}h
- Horas líquidas (sem almoço): {stats['total_horas_liquidas']:.2f}h  
- Horas extras (>8h/dia): {stats['total_horas_extras']:.2f}h
- Horas pagas (com 50% extras): {stats['total_horas_pagas']:.2f}h
- Média por jornada: {stats['media_horas']:.2f}h

DISTRIBUIÇÃO:
- Abaixo da faixa: {stats['abaixo']} ({stats['abaixo']/stats['total_registros']*100:.1f}%)
- Normal: {stats['normal']} ({stats['normal']/stats['total_registros']*100:.1f}%)
- Acima da faixa: {stats['acima']} ({stats['acima']/stats['total_registros']*100:.1f}%)

TOP 3 FUNCIONÁRIOS (horas brutas):
{chr(10).join([f"- {nome}: {horas:.2f}h" for nome, horas in stats['top_3_func'].items()])}

IMPORTANTE: Ao responder sobre horas extras, sempre considere que:
- Horas extras são calculadas APÓS desconto de 1h de almoço
- Exemplo: 10h trabalhadas = 9h líquidas = 1h extra (9h - 8h)
- Dias úteis vs fins de semana podem ter padrões diferentes

Responda de forma clara, use dados específicos e foque em insights práticos sobre produtividade e custos.
"""
            
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": contexto},
                    {"role": "user", "content": pergunta}
                ],
                temperature=0.3,  # Reduzir temperatura para respostas mais focadas
                max_tokens=400,   # Aumentar tokens para respostas mais completas
                timeout=30  # Timeout de 30 segundos
            )
            
            resposta = completion.choices[0].message.content
            
            # Salvar no histórico
            st.session_state.chat_messages.append({"role": "user", "content": pergunta})
            st.session_state.chat_messages.append({"role": "assistant", "content": resposta})
        
        # Limpar flag de processamento
        st.session_state.processing_chat = False
        
        # Mostrar resposta imediatamente
        st.success("✅ Resposta gerada!")
        
    except Exception as e:
        st.session_state.processing_chat = False
        error_msg = f"❌ Erro no chat: {str(e)}"
        st.error(error_msg)
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": error_msg
        })

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
    
    # Calcular limite de 90 dias atrás
    data_limite_90_dias = data_max - timedelta(days=90)
    
    # Ajustar data mínima para não ultrapassar 90 dias
    data_min_permitida = max(data_min, data_limite_90_dias)
    
    # ✅ PADRÃO: Carregar automaticamente os últimos 30 dias
    data_inicio_padrao = data_max - timedelta(days=29)  # 29 + hoje = 30 dias
    data_inicio_padrao = max(data_inicio_padrao, data_min_permitida)  # Não ultrapassar limites
    
    # Mostrar informação sobre o período disponível
    st.info(f"📅 **Período disponível**: {data_min_permitida.strftime('%d/%m/%Y')} a {data_max.strftime('%d/%m/%Y')} (últimos 90 dias)")
    st.success(f"🎯 **Carregado automaticamente**: Últimos 30 dias ({data_inicio_padrao.strftime('%d/%m/%Y')} a {data_max.strftime('%d/%m/%Y')})")
    
    # Períodos pré-definidos
    st.subheader("⚡ Períodos Rápidos")
    col_periodo1, col_periodo2, col_periodo3 = st.columns(3)
    
    with col_periodo1:
        if st.button("📅 Últimos 7 dias", use_container_width=True):
            st.session_state['periodo_inicio'] = data_max - timedelta(days=6)
            st.session_state['periodo_fim'] = data_max
            st.rerun()
    
    with col_periodo2:
        if st.button("📅 Últimos 15 dias", use_container_width=True):
            st.session_state['periodo_inicio'] = data_max - timedelta(days=14)
            st.session_state['periodo_fim'] = data_max
            st.rerun()
    
    with col_periodo3:
        if st.button("📅 Últimos 30 dias", use_container_width=True):
            st.session_state['periodo_inicio'] = data_max - timedelta(days=29)
            st.session_state['periodo_fim'] = data_max
            st.rerun()
    
    st.subheader("📅 Seleção Manual")
    
    # Usar session_state se disponível, senão usar padrão
    if 'periodo_inicio' not in st.session_state:
        st.session_state['periodo_inicio'] = data_inicio_padrao
    if 'periodo_fim' not in st.session_state:
        st.session_state['periodo_fim'] = data_max
    
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data Início",
            value=st.session_state['periodo_inicio'],
            min_value=data_min_permitida,
            max_value=data_max,
            help="Período limitado aos últimos 90 dias",
            key='date_inicio_input'
        )
        # Atualizar session_state quando usuário muda manualmente
        if data_inicio != st.session_state['periodo_inicio']:
            st.session_state['periodo_inicio'] = data_inicio
    
    with col2:
        data_fim = st.date_input(
            "Data Fim",
            value=st.session_state['periodo_fim'],
            min_value=data_min_permitida,
            max_value=data_max,
            help="Período limitado aos últimos 90 dias",
            key='date_fim_input'
        )
        # Atualizar session_state quando usuário muda manualmente
        if data_fim != st.session_state['periodo_fim']:
            st.session_state['periodo_fim'] = data_fim
    
    # Validação: máximo 30 dias de intervalo
    if data_inicio and data_fim:
        dias_selecionados = (data_fim - data_inicio).days + 1
        
        if dias_selecionados > 30:
            st.error(f"⚠️ **Intervalo muito grande!** Selecionados: {dias_selecionados} dias. Máximo permitido: 30 dias.")
            st.info("💡 **Ajuste**: Selecione um período de até 30 dias para análise.")
            
            # Ajustar automaticamente para 30 dias a partir da data início
            data_fim_sugerida = data_inicio + timedelta(days=29)  # 29 + data_início = 30 dias
            if data_fim_sugerida <= data_max:
                st.warning(f"🔧 **Sugestão automática**: Período ajustado para {data_inicio.strftime('%d/%m/%Y')} a {data_fim_sugerida.strftime('%d/%m/%Y')} (30 dias)")
                data_fim = data_fim_sugerida
            else:
                # Se não puder ajustar para frente, ajustar para trás
                data_inicio_sugerida = data_fim - timedelta(days=29)
                st.warning(f"🔧 **Sugestão automática**: Período ajustado para {data_inicio_sugerida.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} (30 dias)")
                data_inicio = data_inicio_sugerida
        else:
            st.success(f"✅ **Período válido**: {dias_selecionados} dias selecionados (máximo: 30 dias)")
    
    # Mostrar estatísticas do período selecionado
    with st.expander("📊 Informações do Período Selecionado"):
        if data_inicio and data_fim:
            periodo_info = df_original[
                (df_original['data'].dt.date >= data_inicio) &
                (df_original['data'].dt.date <= data_fim)
            ]
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("📅 Dias", f"{dias_selecionados}")
            with col_info2:
                st.metric("📊 Apontamentos", f"{len(periodo_info):,}")
            with col_info3:
                st.metric("👥 Funcionários", f"{periodo_info['s_nm_recurso'].nunique()}")
            
            if len(periodo_info) == 0:
                st.warning("⚠️ Nenhum dado encontrado para o período selecionado!")
            else:
                st.success(f"✅ Dados carregados: {len(periodo_info):,} registros para análise")
    
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
    
    # Dicas de uso
    with st.expander("💡 Dicas de Uso"):
        st.markdown("""
        **Para melhor análise:**
        
        ✅ **Períodos recomendados:**
        - 7 dias: Análise detalhada por semana
        - 15 dias: Análise quinzenal  
        - 30 dias: Análise mensal completa
        
        📊 **Dados:**
        - Dados agregados por dia/funcionário
        - Horas extras calculadas automaticamente
        - Chat IA disponível em todas as abas
        
        🎯 **Navegação:**
        - Use filtros na sidebar para focar análise
        - Explore as 6 abas disponíveis
        - Chat lateral para insights inteligentes
        """)
    
    # Informações do sistema
    with st.expander("ℹ️ Informações do Sistema"):
        st.markdown(f"""
        **Dados carregados:**
        - Total de registros: {len(df_original):,}
        - Período completo: {df_original['data'].min().strftime('%d/%m/%Y')} a {df_original['data'].max().strftime('%d/%m/%Y')}
        - Funcionários únicos: {df_original['s_nm_recurso'].nunique()}
        - Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)

# ==================== APLICAR FILTROS ====================
# Validação final antes de processar
if data_inicio and data_fim:
    dias_periodo = (data_fim - data_inicio).days + 1
    
    if dias_periodo > 30:
        st.error("❌ **Não é possível processar**: Período maior que 30 dias. Ajuste as datas na sidebar.")
        st.stop()
    
    # Verificar se está dentro dos últimos 90 dias
    data_limite_90_dias = data_max - timedelta(days=90)
    if data_inicio < data_limite_90_dias:
        st.error(f"❌ **Período muito antigo**: Selecione datas a partir de {data_limite_90_dias.strftime('%d/%m/%Y')} (últimos 90 dias).")
        st.stop()

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

# Informações básicas do período
if len(df_filtrado) > 0:
    dias_periodo = (data_fim - data_inicio).days + 1
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.metric(
            "📅 Período Analisado",
            f"{dias_periodo} dias",
            help=f"De {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        )
    
    with col_info2:
        st.metric(
            "📊 Jornadas Analisadas",
            f"{len(df_filtrado):,}",
            help="Total de jornadas diárias no período (dados agregados por funcionário/dia)"
        )

# Estatísticas compactas em uma linha
abaixo = len(df_filtrado[df_filtrado['classificacao'] == 'Abaixo'])
normal = len(df_filtrado[df_filtrado['classificacao'] == 'Normal'])
acima = len(df_filtrado[df_filtrado['classificacao'] == 'Acima'])
total_horas = df_filtrado['duracao_horas'].sum()

if len(df_filtrado) > 0:
    perc_abaixo = abaixo/len(df_filtrado)*100
    perc_normal = normal/len(df_filtrado)*100
    perc_acima = acima/len(df_filtrado)*100
else:
    perc_abaixo = perc_normal = perc_acima = 0

st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 8px; border-radius: 5px; font-size: 12px; line-height: 1.2;">
    <b>⬇️ Abaixo {int(faixa_referencia)}h:</b> {abaixo} ({perc_abaixo:.1f}%) &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>✅ Normal (~{int(faixa_referencia)}h):</b> {normal} ({perc_normal:.1f}%) &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>⬆️ Acima {int(faixa_referencia)}h:</b> {acima} ({perc_acima:.1f}%) &nbsp;&nbsp;|&nbsp;&nbsp;
    <b>⏱️ Total:</b> {total_horas:.1f}h
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== LAYOUT PRINCIPAL COM CHAT LATERAL ====================
# Criar layout com chat lateral fixo
col_main, col_chat = st.columns([3, 1])

with col_chat:
    # Chat lateral sempre visível
    render_chat_lateral(df_filtrado, data_inicio, data_fim, validador_selecionado, faixa_referencia)

with col_main:
    # ==================== TABS ====================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚨 Alertas",
        "📊 Análise Detalhada", 
        "👤 Por Pessoa",
        "📈 Gráficos",
        "🕒 Horas Extras",
        "📋 Dados Brutos"
    ])

    # ==================== TAB 1: ALERTAS ====================
    with tab1:
        st.header("🚨 Apontamentos Fora do Padrão")
        
        st.info("ℹ️ **Nota:** Alertas consideram horas líquidas (após desconto de 1h de almoço)")
        
        # Apontamentos ABAIXO da faixa
        st.subheader(f"⬇️ Apontamentos Abaixo de {int(faixa_referencia)}h (líquidas)")
        df_abaixo = df_filtrado[df_filtrado['classificacao'] == 'Abaixo'].sort_values('duracao_horas')
        
        if len(df_abaixo) > 0:
            for idx, row in df_abaixo.head(20).iterrows():
                # Usar horas líquidas (após desconto de almoço)
                duracao_bruta = float(row['duracao_bruta']) if 'duracao_bruta' in row else float(row['duracao_horas'])
                duracao_liquida = float(row['duracao_liquida']) if 'duracao_liquida' in row else duracao_bruta - 1.0
                diferenca = faixa_referencia - duracao_liquida
                
                horas_bruta = int(duracao_bruta)
                minutos_bruta = int((duracao_bruta - horas_bruta) * 60)
                
                horas_liquida = int(duracao_liquida)
                minutos_liquida = int((duracao_liquida - horas_liquida) * 60)
                
                # Tipo de dia
                tipo_dia = str(row['tipo_dia']) if 'tipo_dia' in row else ''
                
                # Pegar nome da operação com segurança
                operacao = str(row['s_ds_operacao'])[:50] if pd.notna(row['s_ds_operacao']) else 'N/A'
                nome = str(row['s_nm_recurso']) if pd.notna(row['s_nm_recurso']) else 'N/A'
                
                st.markdown(f"""
                <div class="alert-box alert-low">
                    <strong>📅 {row['data'].strftime('%d/%m/%Y')}</strong> {tipo_dia} - 
                    <strong>{nome}</strong><br>
                    ⏱️ Apontado: {horas_bruta}h{minutos_bruta:02d}min ({duracao_bruta:.2f}h)<br>
                    🍽️ Líquido (após almoço): {horas_liquida}h{minutos_liquida:02d}min ({duracao_liquida:.2f}h)<br>
                    ⚠️ Falta: {diferenca:.2f}h para atingir {int(faixa_referencia)}h líquidas<br>
                    📝 Operação: {operacao}...
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Nenhum apontamento abaixo da faixa!")
        
        st.markdown("---")
        
        # Apontamentos ACIMA da faixa
        st.subheader(f"⬆️ Apontamentos Acima de {int(faixa_referencia)}h (com horas extras)")
        df_acima = df_filtrado[df_filtrado['classificacao'] == 'Acima'].sort_values('duracao_horas', ascending=False)
        
        if len(df_acima) > 0:
            for idx, row in df_acima.head(20).iterrows():
                # Usar horas líquidas e extras
                duracao_bruta = float(row['duracao_bruta']) if 'duracao_bruta' in row else float(row['duracao_horas'])
                duracao_liquida = float(row['duracao_liquida']) if 'duracao_liquida' in row else duracao_bruta - 1.0
                horas_extras = float(row['horas_extras']) if 'horas_extras' in row else max(0, duracao_liquida - 8)
                
                horas_bruta = int(duracao_bruta)
                minutos_bruta = int((duracao_bruta - horas_bruta) * 60)
                
                horas_liquida = int(duracao_liquida)
                minutos_liquida = int((duracao_liquida - horas_liquida) * 60)
                
                # Tipo de dia
                tipo_dia = str(row['tipo_dia']) if 'tipo_dia' in row else ''
                
                # Pegar nome da operação com segurança
                operacao = str(row['s_ds_operacao'])[:50] if pd.notna(row['s_ds_operacao']) else 'N/A'
                nome = str(row['s_nm_recurso']) if pd.notna(row['s_nm_recurso']) else 'N/A'
                
                st.markdown(f"""
                <div class="alert-box alert-high">
                    <strong>📅 {row['data'].strftime('%d/%m/%Y')}</strong> {tipo_dia} - 
                    <strong>{nome}</strong><br>
                    ⏱️ Apontado: {horas_bruta}h{minutos_bruta:02d}min ({duracao_bruta:.2f}h)<br>
                    🍽️ Líquido (após almoço): {horas_liquida}h{minutos_liquida:02d}min ({duracao_liquida:.2f}h)<br>
                    🔴 Horas Extras: {horas_extras:.2f}h acima de 8h<br>
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

    # ==================== TAB 5: HORAS EXTRAS ====================
    with tab5:
        st.header("🕒 Análise de Horas Extras")
        
        if 'horas_extras' not in df_filtrado.columns:
            st.warning("⚠️ Dados de horas extras não disponíveis. Execute novamente o processamento para obter os cálculos atualizados.")
        else:
            # Estatísticas gerais de horas extras
            total_funcionarios = df_filtrado['s_nm_recurso'].nunique()
            funcionarios_com_extras = len(df_filtrado[df_filtrado['horas_extras'] > 0]['s_nm_recurso'].unique())
            total_horas_extras = df_filtrado['horas_extras'].sum()
            total_horas_pagas = df_filtrado['horas_pagas'].sum()
            total_horas_normais = df_filtrado['duracao_horas'].sum()
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="👥 Funcionários com Hora Extra",
                    value=f"{funcionarios_com_extras}/{total_funcionarios}",
                    delta=f"{funcionarios_com_extras/total_funcionarios*100:.1f}%" if total_funcionarios > 0 else "0%"
                )
            
            with col2:
                st.metric(
                    label="⏱️ Total Horas Extras",
                    value=f"{total_horas_extras:.1f}h",
                    delta=f"{total_horas_extras/total_horas_normais*100:.1f}% do total" if total_horas_normais > 0 else "0%"
                )
            
            with col3:
                st.metric(
                    label="💰 Total Horas Pagas",
                    value=f"{total_horas_pagas:.1f}h",
                    delta=f"+{total_horas_pagas-total_horas_normais:.1f}h extras"
                )
            
            with col4:
                custo_extra = (total_horas_pagas - total_horas_normais) * 0.5
                st.metric(
                    label="📈 Custo Adicional",
                    value=f"+{custo_extra:.1f}h",
                    delta="50% sobre extras"
                )
            
            # Gráfico de distribuição de horas extras
            st.subheader("📊 Distribuição de Horas Extras por Funcionário")
            
            funcionarios_extras = df_filtrado[df_filtrado['horas_extras'] > 0].groupby('s_nm_recurso').agg({
                'horas_extras': 'sum',
                'horas_pagas': 'sum',
                'duracao_horas': 'sum'
            }).sort_values('horas_extras', ascending=False)
            
            if len(funcionarios_extras) > 0:
                fig_extras = px.bar(
                    funcionarios_extras.reset_index(),
                    x='s_nm_recurso',
                    y='horas_extras',
                    title="Horas Extras por Funcionário",
                    labels={'s_nm_recurso': 'Funcionário', 'horas_extras': 'Horas Extras'},
                    color='horas_extras',
                    color_continuous_scale='Reds'
                )
                fig_extras.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_extras, use_container_width=True)
                
                # Tabela detalhada
                st.subheader("📋 Detalhamento por Funcionário")
                funcionarios_extras_display = funcionarios_extras.copy()
                funcionarios_extras_display['custo_adicional'] = (funcionarios_extras_display['horas_pagas'] - funcionarios_extras_display['duracao_horas']) * 0.5
                funcionarios_extras_display = funcionarios_extras_display.round(2)
                funcionarios_extras_display.columns = ['Horas Extras', 'Horas Pagas', 'Horas Trabalhadas', 'Custo Adicional (50%)']
                st.dataframe(funcionarios_extras_display, use_container_width=True)
            else:
                st.info("✅ Nenhuma hora extra registrada no período selecionado!")
            
            # Análise temporal de horas extras
            if len(df_filtrado[df_filtrado['horas_extras'] > 0]) > 0:
                st.subheader("📅 Evolução das Horas Extras")
                
                horas_extras_tempo = df_filtrado[df_filtrado['horas_extras'] > 0].groupby('data').agg({
                    'horas_extras': 'sum',
                    's_nm_recurso': 'nunique'
                }).reset_index()
                
                fig_tempo = px.line(
                    horas_extras_tempo,
                    x='data',
                    y='horas_extras',
                    title="Evolução das Horas Extras por Data",
                    labels={'data': 'Data', 'horas_extras': 'Total de Horas Extras'}
                )
                st.plotly_chart(fig_tempo, use_container_width=True)

    # ==================== TAB 6: DADOS BRUTOS ====================
    with tab6:
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

# Footer
st.markdown("---")
st.caption(f"📊 Dashboard V2 | Período: {data_inicio} a {data_fim} | Registros: {len(df_filtrado):,} | Validador: {validador_selecionado}")
