import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import re
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Comercial",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# Funções auxiliares
# -----------------------------

def normalizar_texto(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = re.sub(r"\s+", " ", texto)
    return texto


def encontrar_coluna(df, opcoes):
    colunas_normalizadas = {
        normalizar_texto(col): col for col in df.columns
    }

    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        if opcao_norm in colunas_normalizadas:
            return colunas_normalizadas[opcao_norm]

    for col_norm, col_original in colunas_normalizadas.items():
        for opcao in opcoes:
            if normalizar_texto(opcao) in col_norm:
                return col_original

    return None


def converter_link_google_sheets(url):
    if "docs.google.com/spreadsheets" not in url:
        return url

    match_id = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    match_gid = re.search(r"gid=([0-9]+)", url)

    if not match_id:
        return url

    sheet_id = match_id.group(1)
    gid = match_gid.group(1) if match_gid else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=600)
def carregar_csv_por_url(url):
    url_csv = converter_link_google_sheets(url)
    return pd.read_csv(url_csv)


def carregar_arquivo(arquivo):
    nome = arquivo.name.lower()

    if nome.endswith(".csv"):
        return pd.read_csv(arquivo, sep=None, engine="python")

    if nome.endswith(".xlsx") or nome.endswith(".xls"):
        return pd.read_excel(arquivo)

    return None


def criar_base_exemplo():
    dados = [
        {
            "Empresa": "Empresa Alpha",
            "Nome": "Mariana Silva",
            "Email": "mariana@alpha.com.br",
            "Campanha": "Prospecção Maio",
            "Segmento": "Tecnologia",
            "Evento": "Evento A",
            "Status": "Enviado",
            "Data": "2026-05-01"
        },
        {
            "Empresa": "Grupo Beta",
            "Nome": "Carlos Souza",
            "Email": "carlos@beta.com.br",
            "Campanha": "Prospecção Maio",
            "Segmento": "Logística",
            "Evento": "Evento B",
            "Status": "Abriu",
            "Data": "2026-05-02"
        },
        {
            "Empresa": "Delta Corp",
            "Nome": "Fernanda Lima",
            "Email": "fernanda@delta.com.br",
            "Campanha": "Prospecção Maio",
            "Segmento": "Varejo",
            "Evento": "Evento A",
            "Status": "Clicou",
            "Data": "2026-05-03"
        },
        {
            "Empresa": "Nova Hub",
            "Nome": "Ricardo Alves",
            "Email": "ricardo@novahub.com.br",
            "Campanha": "Reativação",
            "Segmento": "Serviços",
            "Evento": "Evento C",
            "Status": "Reunião marcada",
            "Data": "2026-05-04"
        },
        {
            "Empresa": "Prime Solutions",
            "Nome": "Ana Martins",
            "Email": "ana@prime.com.br",
            "Campanha": "Reativação",
            "Segmento": "Tecnologia",
            "Evento": "Evento B",
            "Status": "Sem resposta",
            "Data": "2026-05-05"
        },
        {
            "Empresa": "Rota Inteligente",
            "Nome": "Paulo Mendes",
            "Email": "paulo@rota.com.br",
            "Campanha": "Transporte",
            "Segmento": "Mobilidade",
            "Evento": "Evento D",
            "Status": "Recusado",
            "Data": "2026-05-06"
        }
    ]

    return pd.DataFrame(dados)


def preparar_dataframe(df):
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    return df


def aplicar_filtro_multiselect(df, coluna, valores):
    if coluna and valores:
        return df[df[coluna].astype(str).isin(valores)]
    return df


def contar_por_palavra(df, colunas, palavras):
    if df.empty:
        return 0

    colunas_validas = [col for col in colunas if col and col in df.columns]

    if not colunas_validas:
        return 0

    texto_linhas = df[colunas_validas].astype(str).agg(" ".join, axis=1)
    texto_linhas = texto_linhas.apply(normalizar_texto)

    padrao = "|".join([normalizar_texto(palavra) for palavra in palavras])
    return texto_linhas.str.contains(padrao, regex=True, na=False).sum()


def card_metrica(titulo, valor, ajuda=None):
    st.metric(label=titulo, value=valor, help=ajuda)


# -----------------------------
# Cabeçalho
# -----------------------------

st.title("📊 Dashboard Comercial Interativo")
st.caption("Modelo inicial em Streamlit para acompanhar leads, campanhas, status, eventos e performance comercial.")

# -----------------------------
# Entrada de dados
# -----------------------------

with st.sidebar:
    st.header("Base de dados")

    arquivo = st.file_uploader(
        "Suba um CSV ou Excel",
        type=["csv", "xlsx", "xls"]
    )

    url_planilha = st.text_input(
        "Ou cole um link público do Google Sheets",
        placeholder="https://docs.google.com/spreadsheets/..."
    )

    st.divider()

    st.caption("Dica: para Google Sheets funcionar sem senha, a planilha precisa estar pública ou compartilhada para qualquer pessoa com o link.")

try:
    if arquivo is not None:
        df_original = carregar_arquivo(arquivo)
    elif url_planilha:
        df_original = carregar_csv_por_url(url_planilha)
    else:
        df_original = criar_base_exemplo()

    df_original = preparar_dataframe(df_original)

except Exception as erro:
    st.error("Não consegui carregar a base. Verifique o arquivo ou o link da planilha.")
    st.exception(erro)
    st.stop()

if df_original is None or df_original.empty:
    st.warning("A base está vazia.")
    st.stop()

# -----------------------------
# Detecção automática de colunas
# -----------------------------

col_empresa = encontrar_coluna(df_original, ["Empresa", "Company", "Conta", "Cliente"])
col_nome = encontrar_coluna(df_original, ["Nome", "Contato", "Pessoa", "Lead"])
col_email = encontrar_coluna(df_original, ["Email", "E-mail", "Mail"])
col_status = encontrar_coluna(df_original, ["Status", "Status de envio", "Status do envio", "Situação"])
col_envio = encontrar_coluna(df_original, ["Envio", "Enviado", "Status Envio"])
col_resposta = encontrar_coluna(df_original, ["Resposta", "Retorno", "Reply"])
col_campanha = encontrar_coluna(df_original, ["Campanha", "Campaign"])
col_segmento = encontrar_coluna(df_original, ["Segmento", "Setor", "Categoria", "Nicho"])
col_evento = encontrar_coluna(df_original, ["Evento", "Event"])
col_data = encontrar_coluna(df_original, ["Data", "Data envio", "Data de envio", "Created At", "Criado em"])

colunas_status = [col_status, col_envio, col_resposta]

df = df_original.copy()

# -----------------------------
# Filtros
# -----------------------------

with st.sidebar:
    st.header("Filtros")

    if col_campanha:
        campanhas = sorted(df[col_campanha].dropna().astype(str).unique())
        filtro_campanha = st.multiselect("Campanha", campanhas)
        df = aplicar_filtro_multiselect(df, col_campanha, filtro_campanha)

    if col_segmento:
        segmentos = sorted(df[col_segmento].dropna().astype(str).unique())
        filtro_segmento = st.multiselect("Segmento", segmentos)
        df = aplicar_filtro_multiselect(df, col_segmento, filtro_segmento)

    if col_evento:
        eventos = sorted(df[col_evento].dropna().astype(str).unique())
        filtro_evento = st.multiselect("Evento", eventos)
        df = aplicar_filtro_multiselect(df, col_evento, filtro_evento)

    if col_status:
        status_opcoes = sorted(df[col_status].dropna().astype(str).unique())
        filtro_status = st.multiselect("Status", status_opcoes)
        df = aplicar_filtro_multiselect(df, col_status, filtro_status)

    busca = st.text_input("Buscar empresa, contato ou e-mail")

    if busca:
        busca_norm = normalizar_texto(busca)
        colunas_busca = [col for col in [col_empresa, col_nome, col_email] if col]
        if colunas_busca:
            texto_busca = df[colunas_busca].astype(str).agg(" ".join, axis=1)
            texto_busca = texto_busca.apply(normalizar_texto)
            df = df[texto_busca.str.contains(busca_norm, na=False)]

# -----------------------------
# Métricas principais
# -----------------------------

total_registros = len(df)

total_empresas = df[col_empresa].nunique() if col_empresa else 0
total_contatos = df[col_email].nunique() if col_email else (df[col_nome].nunique() if col_nome else total_registros)

total_enviados = contar_por_palavra(
    df,
    colunas_status,
    ["enviado", "enviada", "sent", "delivered"]
)

total_abertos = contar_por_palavra(
    df,
    colunas_status,
    ["abriu", "aberto", "abertura", "open", "opened"]
)

total_cliques = contar_por_palavra(
    df,
    colunas_status,
    ["clicou", "clique", "click", "clicked"]
)

total_respostas = contar_por_palavra(
    df,
    colunas_status,
    ["respondeu", "resposta", "reply", "respondido"]
)

total_reunioes = contar_por_palavra(
    df,
    colunas_status,
    ["reunião", "reuniao", "meeting", "agenda marcada", "reunião marcada"]
)

taxa_abertura = (total_abertos / total_enviados * 100) if total_enviados else 0
taxa_clique = (total_cliques / total_enviados * 100) if total_enviados else 0
taxa_resposta = (total_respostas / total_enviados * 100) if total_enviados else 0

st.subheader("Resumo executivo")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    card_metrica("Registros", f"{total_registros:,}".replace(",", "."))

with col2:
    card_metrica("Empresas", f"{total_empresas:,}".replace(",", "."))

with col3:
    card_metrica("Contatos", f"{total_contatos:,}".replace(",", "."))

with col4:
    card_metrica("Enviados", f"{total_enviados:,}".replace(",", "."))

with col5:
    card_metrica("Reuniões", f"{total_reunioes:,}".replace(",", "."))

col6, col7, col8 = st.columns(3)

with col6:
    card_metrica("Taxa de abertura", f"{taxa_abertura:.1f}%")

with col7:
    card_metrica("Taxa de clique", f"{taxa_clique:.1f}%")

with col8:
    card_metrica("Taxa de resposta", f"{taxa_resposta:.1f}%")

st.divider()

# -----------------------------
# Gráficos
# -----------------------------

aba1, aba2, aba3, aba4 = st.tabs([
    "Funil",
    "Distribuições",
    "Evolução",
    "Base detalhada"
])

with aba1:
    st.subheader("Funil comercial")

    df_funil = pd.DataFrame({
        "Etapa": ["Enviados", "Abertos", "Cliques", "Respostas", "Reuniões"],
        "Quantidade": [
            total_enviados,
            total_abertos,
            total_cliques,
            total_respostas,
            total_reunioes
        ]
    })

    fig_funil = px.bar(
        df_funil,
        x="Etapa",
        y="Quantidade",
        text="Quantidade",
        title="Funil de engajamento"
    )

    fig_funil.update_traces(textposition="outside")
    fig_funil.update_layout(yaxis_title="", xaxis_title="")
    st.plotly_chart(fig_funil, use_container_width=True)

with aba2:
    col_a, col_b = st.columns(2)

    with col_a:
        if col_status:
            st.subheader("Status")

            df_status = (
                df[col_status]
                .fillna("Sem status")
                .astype(str)
                .value_counts()
                .reset_index()
            )
            df_status.columns = ["Status", "Quantidade"]

            fig_status = px.pie(
                df_status,
                names="Status",
                values="Quantidade",
                title="Distribuição por status"
            )

            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Não encontrei uma coluna de status na base.")

    with col_b:
        if col_segmento:
            st.subheader("Segmentos")

            df_segmento = (
                df[col_segmento]
                .fillna("Sem segmento")
                .astype(str)
                .value_counts()
                .reset_index()
                .head(15)
            )
            df_segmento.columns = ["Segmento", "Quantidade"]

            fig_segmento = px.bar(
                df_segmento,
                x="Quantidade",
                y="Segmento",
                orientation="h",
                title="Top segmentos"
            )

            fig_segmento.update_layout(yaxis_title="", xaxis_title="")
            st.plotly_chart(fig_segmento, use_container_width=True)
        else:
            st.info("Não encontrei uma coluna de segmento na base.")

    if col_empresa:
        st.subheader("Empresas com mais registros")

        df_empresas = (
            df[col_empresa]
            .fillna("Sem empresa")
            .astype(str)
            .value_counts()
            .reset_index()
            .head(20)
        )
        df_empresas.columns = ["Empresa", "Quantidade"]

        fig_empresas = px.bar(
            df_empresas,
            x="Empresa",
            y="Quantidade",
            title="Top empresas"
        )

        fig_empresas.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_empresas, use_container_width=True)

with aba3:
    st.subheader("Evolução no tempo")

    if col_data:
        df_tempo = df.copy()
        df_tempo[col_data] = pd.to_datetime(df_tempo[col_data], errors="coerce")
        df_tempo = df_tempo.dropna(subset=[col_data])

        if not df_tempo.empty:
            df_tempo["Data Agrupada"] = df_tempo[col_data].dt.date

            df_evolucao = (
                df_tempo
                .groupby("Data Agrupada")
                .size()
                .reset_index(name="Quantidade")
            )

            fig_tempo = px.line(
                df_evolucao,
                x="Data Agrupada",
                y="Quantidade",
                markers=True,
                title="Registros por data"
            )

            fig_tempo.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_tempo, use_container_width=True)
        else:
            st.info("Encontrei uma coluna de data, mas não consegui converter os valores.")
    else:
        st.info("Não encontrei uma coluna de data na base.")

with aba4:
    st.subheader("Base detalhada")

    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )

    csv_export = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Baixar base filtrada em CSV",
        data=csv_export,
        file_name="base_filtrada_dashboard.csv",
        mime="text/csv"
    )

# -----------------------------
# Diagnóstico das colunas
# -----------------------------

with st.expander("Diagnóstico das colunas detectadas"):
    diagnostico = pd.DataFrame({
        "Campo esperado": [
            "Empresa",
            "Nome",
            "Email",
            "Status",
            "Envio",
            "Resposta",
            "Campanha",
            "Segmento",
            "Evento",
            "Data"
        ],
        "Coluna encontrada": [
            col_empresa,
            col_nome,
            col_email,
            col_status,
            col_envio,
            col_resposta,
            col_campanha,
            col_segmento,
            col_evento,
            col_data
        ]
    })

    st.dataframe(diagnostico, use_container_width=True)

st.caption("Dashboard criado em Streamlit. Ajuste as colunas da base para melhorar as métricas e filtros.")