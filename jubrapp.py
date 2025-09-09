import streamlit as st
import pandas as pd
from io import BytesIO

# --- Configurações da Página ---
st.set_page_config(
    page_title="Analisador de Processos Arquivados",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Função Principal de Análise (Adaptada do script original) ---
def analisar_processos(df, movimentos_arquivamento):
    """
    Analisa um DataFrame de movimentos processuais para identificar processos
    que foram efetivamente arquivados.

    Args:
        df (pd.DataFrame): O DataFrame com os dados dos processos.
        movimentos_arquivamento (list): Lista de strings que indicam arquivamento.

    Returns:
        tuple: Uma tupla contendo:
               - lista_arquivados (list): Números dos processos arquivados.
               - df_resultados (pd.DataFrame): DataFrame com detalhes dos arquivados.
    """
    # --- Tratamento dos Dados ---
    try:
        df.columns = ['numero_processo', 'tipo_movimento', 'data_movimento']
        df['data_movimento'] = pd.to_datetime(df['data_movimento'], dayfirst=True)
        df['tipo_movimento'] = df['tipo_movimento'].str.strip()
    except Exception as e:
        st.error(f"Erro ao processar as colunas da planilha. Verifique se ela possui as 3 colunas esperadas (Número, Movimento, Data). Erro: {e}")
        return [], pd.DataFrame()

    processos_arquivados = []
    detalhes_arquivados = []
    
    processos_unicos = df['numero_processo'].unique()

    for numero_processo in processos_unicos:
        movimentos = df[df['numero_processo'] == numero_processo]
        movimentos_ordenados = movimentos.sort_values(by='data_movimento', ascending=False)
        
        if not movimentos_ordenados.empty:
            ultimo_movimento = movimentos_ordenados.iloc[0]
            
            # Verifica se o tipo do último andamento está na lista de arquivamento
            if any(termo.lower() in ultimo_movimento['tipo_movimento'].lower() for termo in movimentos_arquivamento):
                processos_arquivados.append(numero_processo)
                detalhes_arquivados.append({
                    "Número do Processo": ultimo_movimento['numero_processo'],
                    "Último Movimento (Arquivamento)": ultimo_movimento['tipo_movimento'],
                    "Data do Arquivamento": ultimo_movimento['data_movimento'].strftime('%d/%m/%Y')
                })

    df_resultados = pd.DataFrame(detalhes_arquivados)
    return processos_arquivados, df_resultados

# --- Função para converter DataFrame para Excel (para download) ---
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Processos Arquivados')
    processed_data = output.getvalue()
    return processed_data

# --- Interface da Aplicação ---

# Título
st.title("⚖️ Analisador de Processos Efetivamente Arquivados")
st.markdown("Faça o upload da sua planilha para identificar quais processos tiveram um andamento de arquivamento como sua **última movimentação**.")

# Barra Lateral (Sidebar)
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.markdown("Adicione ou remova os termos que indicam o arquivamento de um processo.")
    
    # Textos padrão para os andamentos de arquivamento
    movimentos_padrao = [
        'Arquivado Definitivamente',
        'Determinado o Arquivamento',
        'Determinado o arquivamento definitivo',
        'Definitivo',
        'Baixa Definitiva'
    ]
    
    # Usamos uma área de texto para que o usuário possa editar
    movimentos_input = st.text_area(
        "Termos de Arquivamento (um por linha)",
        value='\n'.join(movimentos_padrao),
        height=150
    )
    
    # Converte o input de volta para uma lista
    movimentos_de_arquivamento = [linha.strip() for linha in movimentos_input.split('\n') if linha.strip()]

    st.info("A análise não diferencia maiúsculas/minúsculas dos termos acima.")

# Corpo Principal da Aplicação
st.header("1. Faça o upload da sua planilha")

uploaded_file = st.file_uploader(
    "A planilha deve conter 3 colunas: Número do Processo, Tipo do Movimento e Data do Movimento.",
    type=['xlsx', 'xls', 'csv']
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Planilha carregada com sucesso!")
        st.subheader("Pré-visualização dos dados carregados:")
        st.dataframe(df.head())

        # Botão para iniciar a análise
        if st.button("🚀 Iniciar Análise", type="primary"):
            with st.spinner('Analisando os processos... Por favor, aguarde.'):
                
                lista_arquivados, df_resultados = analisar_processos(df.copy(), movimentos_de_arquivamento)
                
                total_processos_unicos = df['numero_processo'].nunique()
                total_arquivados = len(lista_arquivados)

                st.subheader("📊 Resultados da Análise")
                
                # Exibição de métricas
                col1, col2 = st.columns(2)
                col1.metric("Total de Processos Únicos Analisados", f"{total_processos_unicos} 🗂️")
                col2.metric("Processos Efetivamente Arquivados", f"{total_arquivados} ✅")

                if not df_resultados.empty:
                    st.markdown("### Detalhes dos Processos Arquivados")
                    st.dataframe(df_resultados)

                    # Botão de Download
                    excel_data = to_excel(df_resultados)
                    st.download_button(
                        label="📥 Baixar Resultados em Excel",
                        data=excel_data,
                        file_name="processos_arquivados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("Nenhum processo foi identificado como efetivamente arquivado com base nos critérios definidos.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar ou processar o arquivo: {e}")
else:
    st.info("Aguardando o upload de uma planilha para iniciar a análise.")