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

# --- Função Principal de Análise (Agora mais robusta) ---
def analisar_processos(df, col_processo, col_movimento, col_data, movimentos_arquivamento):
    """
    Analisa um DataFrame de movimentos processuais para identificar processos
    que foram efetivamente arquivados.
    """
    try:
        # 1. Seleciona apenas as colunas mapeadas pelo usuário
        df_analise = df[[col_processo, col_movimento, col_data]].copy()
        
        # 2. Renomeia para nomes padronizados para o resto da função
        df_analise.columns = ['numero_processo', 'tipo_movimento', 'data_movimento']

        # 3. Converte e limpa os dados
        df_analise['numero_processo'] = df_analise['numero_processo'].astype(str)
        df_analise['data_movimento'] = pd.to_datetime(df_analise['data_movimento'], dayfirst=True, errors='coerce')
        df_analise['tipo_movimento'] = df_analise['tipo_movimento'].str.strip()
        
        # Remove linhas onde a data não pôde ser convertida
        df_analise.dropna(subset=['data_movimento'], inplace=True)

    except Exception as e:
        st.error(f"Erro ao processar as colunas selecionadas. Verifique se o mapeamento está correto e se os dados nas colunas são válidos (especialmente as datas). Erro: {e}")
        return [], pd.DataFrame()

    processos_arquivados = []
    detalhes_arquivados = []
    
    # Agrupa pelo nome da coluna padronizado
    processos_agrupados = df_analise.groupby('numero_processo')

    for numero_processo, movimentos in processos_agrupados:
        movimentos_ordenados = movimentos.sort_values(by='data_movimento', ascending=False)
        
        if not movimentos_ordenados.empty:
            ultimo_movimento = movimentos_ordenados.iloc[0]
            
            # Verifica se algum dos termos de arquivamento está contido no último movimento
            if any(termo.lower() in str(ultimo_movimento['tipo_movimento']).lower() for termo in movimentos_arquivamento):
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
st.title("⚖️ Analisador de Processos Efetivamente Arquivados")
st.markdown("Uma ferramenta inteligente para identificar processos que tiveram um andamento de arquivamento como sua **última movimentação**.")

# Barra Lateral (Sidebar)
with st.sidebar:
    st.header("⚙️ Configurações")
    st.markdown("Adicione ou remova os termos que indicam o arquivamento de um processo.")
    
    movimentos_padrao = [
        'Arquivado Definitivamente',
        'Determinado o Arquivamento',
        'Determinado o arquivamento definitivo',
        'Definitivo',
        'Baixa Definitiva'
    ]
    movimentos_input = st.text_area(
        "Termos de Arquivamento (um por linha)",
        value='\n'.join(movimentos_padrao),
        height=150
    )
    movimentos_de_arquivamento = [linha.strip() for linha in movimentos_input.split('\n') if linha.strip()]
    st.info("A análise busca se o movimento **contém** um dos termos acima (não diferencia maiúsculas/minúsculas).")

# Corpo Principal da Aplicação
st.header("1. Faça o upload da sua planilha")
uploaded_file = st.file_uploader(
    "Arraste e solte o arquivo ou clique para selecionar (formatos .xlsx, .xls, .csv).",
    type=['xlsx', 'xls', 'csv']
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Planilha carregada com sucesso!")
        st.subheader("Pré-visualização dos dados:")
        st.dataframe(df.head())
        
        st.header("2. Mapeie as colunas da sua planilha")
        st.markdown("Indique qual coluna corresponde a cada informação necessária.")
        
        colunas_disponiveis = df.columns.tolist()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            col_processo = st.selectbox("Coluna com o NÚMERO DO PROCESSO", colunas_disponiveis, index=0)
        with col2:
            col_movimento = st.selectbox("Coluna com o TIPO DO MOVIMENTO", colunas_disponiveis, index=1)
        with col3:
            col_data = st.selectbox("Coluna com a DATA DO MOVIMENTO", colunas_disponiveis, index=2)
        
        # Verifica se o usuário selecionou colunas diferentes
        if len(set([col_processo, col_movimento, col_data])) < 3:
            st.error("Atenção: Você selecionou a mesma coluna para diferentes campos. Por favor, corrija o mapeamento.")
        else:
            st.header("3. Inicie a Análise")
            if st.button("🚀 Analisar Processos", type="primary", use_container_width=True):
                with st.spinner('Analisando... Isso pode levar alguns segundos.'):
                    lista_arquivados, df_resultados = analisar_processos(df, col_processo, col_movimento, col_data, movimentos_de_arquivamento)
                    
                    total_processos_unicos = df[col_processo].nunique()
                    total_arquivados = len(lista_arquivados)

                    st.subheader("📊 Resultados")
                    
                    res_col1, res_col2 = st.columns(2)
                    res_col1.metric("Total de Processos Únicos Analisados", f"{total_processos_unicos} 🗂️")
                    res_col2.metric("Processos Efetivamente Arquivados", f"{total_arquivados} ✅")

                    if not df_resultados.empty:
                        st.markdown("### Detalhes dos Processos Arquivados")
                        st.dataframe(df_resultados)

                        excel_data = to_excel(df_resultados)
                        st.download_button(
                            label="📥 Baixar Resultados em Excel",
                            data=excel_data,
                            file_name="processos_arquivados.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.warning("Nenhum processo foi identificado como efetivamente arquivado com base nos critérios definidos.")

    except Exception as e:
        st.error(f"Ocorreu um erro fatal ao carregar o arquivo. Verifique se o formato está correto. Erro: {e}")

else:
    st.info("Aguardando o upload de uma planilha para iniciar a análise.")
