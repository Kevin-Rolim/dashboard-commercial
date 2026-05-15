from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Dashboard Comercial de Prospecção",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARQUIVOS_PADRAO = [
    "base_dashboard_comercial_prospeccao.csv",
    "dados_dashboard_prospects_streamlit_limpo.csv",
    "dados.csv",
    "Lista de Prospects - Página12 (1).csv",
    "Lista de Prospects - Pagina12 (1).csv",
]

COLUNAS_OFICIAIS = [
    "empresa_mapeada",
    "evento_mapeado_por_empresa",
    "ano_evento_mapeado",
    "setor_deduplicado_detalhado_da_empresa",
    "empresas_no_setor_deduplicado_detalhado",
    "setor_consolidado_hard_da_empresa",
    "empresas_no_setor_consolidado_hard",
    "tipo_publico_do_evento",
    "eventos_por_tipo_publico",
    "nicho_segmento_do_evento",
    "eventos_por_nicho_segmento",
    "empresa_priorizada_para_busca_de_contatos",
    "empresas_priorizadas_para_contato_total",
    "empresa_com_contato_encontrado",
    "empresas_com_contato_encontrado_total",
    "contatos_encontrados_total",
    "cargo_do_contato_encontrado",
    "senioridade_do_contato_encontrado",
    "contatos_por_senioridade",
    "departamento_do_contato_encontrado",
    "data_calendario_envio_email",
    "dia_mes_envio_email",
    "emails_enviados_no_dia",
    "status_da_resposta_do_email",
    "respostas_por_status",
]

ROTULOS = {
    "empresa_mapeada": "Empresa mapeada",
    "evento_mapeado_por_empresa": "Evento mapeado por empresa",
    "ano_evento_mapeado": "Ano do evento mapeado",
    "setor_deduplicado_detalhado_da_empresa": "Setor deduplicado detalhado",
    "empresas_no_setor_deduplicado_detalhado": "Empresas no setor detalhado",
    "setor_consolidado_hard_da_empresa": "Setor consolidado hard",
    "empresas_no_setor_consolidado_hard": "Empresas no setor hard",
    "tipo_publico_do_evento": "Tipo de público do evento",
    "eventos_por_tipo_publico": "Eventos por tipo de público",
    "nicho_segmento_do_evento": "Nicho ou segmento do evento",
    "eventos_por_nicho_segmento": "Eventos por nicho ou segmento",
    "empresa_priorizada_para_busca_de_contatos": "Empresa priorizada para busca de contatos",
    "empresas_priorizadas_para_contato_total": "Total de empresas priorizadas para contato",
    "empresa_com_contato_encontrado": "Empresa com contato encontrado",
    "empresas_com_contato_encontrado_total": "Total de empresas com contato encontrado",
    "contatos_encontrados_total": "Total de contatos encontrados",
    "cargo_do_contato_encontrado": "Cargo do contato encontrado",
    "senioridade_do_contato_encontrado": "Senioridade do contato encontrado",
    "contatos_por_senioridade": "Contatos por senioridade",
    "departamento_do_contato_encontrado": "Departamento do contato encontrado",
    "data_calendario_envio_email": "Data de envio do email",
    "dia_mes_envio_email": "Dia e mês do envio",
    "emails_enviados_no_dia": "Emails enviados no dia",
    "status_da_resposta_do_email": "Status da resposta do email",
    "respostas_por_status": "Respostas por status",
}

MAPA_COLUNAS_ANTIGAS = {
    "empresa_prospect_mapeada": "empresa_mapeada",
    "evento_prospect_mapeado": "evento_mapeado_por_empresa",
    "ano_evento_prospect": "ano_evento_mapeado",
    "setor_empresa_detalhado": "setor_deduplicado_detalhado_da_empresa",
    "quantidade_empresas_no_setor_detalhado": "empresas_no_setor_deduplicado_detalhado",
    "setor_empresa_consolidado_hard": "setor_consolidado_hard_da_empresa",
    "quantidade_empresas_no_setor_consolidado_hard": "empresas_no_setor_consolidado_hard",
    "tipo_publico_evento": "tipo_publico_do_evento",
    "quantidade_eventos_por_tipo_publico": "eventos_por_tipo_publico",
    "nicho_segmento_evento": "nicho_segmento_do_evento",
    "quantidade_eventos_por_nicho_segmento": "eventos_por_nicho_segmento",
    "empresa_alvo_para_busca_de_contato": "empresa_priorizada_para_busca_de_contatos",
    "total_empresas_alvo_para_contato": "empresas_priorizadas_para_contato_total",
    "empresa_com_contato_encontrado": "empresa_com_contato_encontrado",
    "total_empresas_com_contato_encontrado": "empresas_com_contato_encontrado_total",
    "total_contatos_encontrados": "contatos_encontrados_total",
    "cargo_contato_mapeado": "cargo_do_contato_encontrado",
    "senioridade_contato": "senioridade_do_contato_encontrado",
    "quantidade_contatos_por_senioridade": "contatos_por_senioridade",
    "departamento_contato_mapeado": "departamento_do_contato_encontrado",
    "data_envio_email": "data_calendario_envio_email",
    "dia_mes_envio_email_original": "dia_mes_envio_email",
    "quantidade_emails_enviados_no_dia": "emails_enviados_no_dia",
    "status_resposta_email": "status_da_resposta_do_email",
    "quantidade_respostas_por_status": "respostas_por_status",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
.stApp {
    background:
        radial-gradient(circle at 8% 2%, rgba(244, 63, 94, 0.20), transparent 28%),
        radial-gradient(circle at 92% 6%, rgba(249, 115, 22, 0.20), transparent 30%),
        radial-gradient(circle at 50% 100%, rgba(59, 130, 246, 0.12), transparent 34%),
        linear-gradient(135deg, #050814 0%, #0B1020 48%, #111827 100%);
}
.block-container {padding-top: 1.25rem; padding-bottom: 3rem; max-width: 1500px;}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #090D18 100%);
    border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] * {color: #E5E7EB;}
.hero {
    padding: 28px 30px;
    border-radius: 30px;
    background: linear-gradient(135deg, rgba(249,115,22,.24), rgba(236,72,153,.13) 42%, rgba(59,130,246,.14));
    border: 1px solid rgba(255,255,255,.14);
    box-shadow: 0 26px 80px rgba(0,0,0,.38);
    margin-bottom: 18px;
}
.hero h1 {font-size: 2.35rem; line-height: 1.04; margin: 0 0 8px 0; font-weight: 900; color: #FFFFFF; letter-spacing: -.055em;}
.hero p {font-size: 1.02rem; color: #D1D5DB; margin: 0; max-width: 1120px;}
.badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    color: #FED7AA;
    border: 1px solid rgba(251,146,60,.28);
    font-size: .74rem;
    font-weight: 850;
    margin: 0 6px 12px 0;
    letter-spacing: .03em;
}
.kpi-card {
    padding: 18px 18px 16px 18px;
    border-radius: 24px;
    background: linear-gradient(180deg, rgba(255,255,255,.085), rgba(255,255,255,.035));
    border: 1px solid rgba(255,255,255,.11);
    box-shadow: 0 15px 42px rgba(0,0,0,.24);
    min-height: 132px;
}
.kpi-label {font-size: .73rem; text-transform: uppercase; letter-spacing: .09em; color: #A7B3C7; font-weight: 850;}
.kpi-value {font-size: 2.08rem; margin-top: 8px; color: #FFFFFF; font-weight: 900; letter-spacing: -.045em;}
.kpi-help {font-size: .84rem; color: #CBD5E1; margin-top: 7px;}
.section-title {font-size: 1.22rem; font-weight: 900; color: #F8FAFC; margin: 18px 0 2px 0; letter-spacing: -.025em;}
.section-subtitle {font-size: .91rem; color: #9CA3AF; margin-bottom: 14px;}
[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.03));
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 20px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] {color: #B6C2D2;}
[data-testid="stMetricValue"] {color: #FFFFFF; font-weight: 900;}
.stTabs [data-baseweb="tab-list"] {gap: 8px; margin-top: 8px;}
.stTabs [data-baseweb="tab"] {
    height: 46px;
    padding: 0 18px;
    border-radius: 999px;
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.08);
    font-weight: 750;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(249,115,22,.38), rgba(236,72,153,.25));
    border: 1px solid rgba(255,255,255,.18);
}
[data-testid="stDataFrame"] {border-radius: 18px; overflow: hidden;}
.small-note {font-size: .82rem; color: #94A3B8;}
hr {border-color: rgba(255,255,255,.08);}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def limpar_texto(valor: object) -> str:
    if valor is None or pd.isna(valor):
        return ""
    texto = str(valor).replace("\u00a0", " ").strip()
    texto = re.sub(r"\s+", " ", texto)
    if texto.lower() in {"nan", "none", "null"}:
        return ""
    if texto.upper() in {"#VALUE!", "#NAME?", "#N/A", "#REF!", "#DIV/0!"}:
        return ""
    return texto


def normalizar_chave(valor: object) -> str:
    texto = limpar_texto(valor).lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def normalizar_nome_coluna(valor: object) -> str:
    return normalizar_chave(valor).replace(" ", "_")


def para_numero(serie: pd.Series) -> pd.Series:
    texto = (
        serie.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^0-9.\-]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(texto, errors="coerce").fillna(0)


def formato_inteiro(valor: float | int | None) -> str:
    if valor is None or pd.isna(valor):
        return "0"
    return f"{int(round(float(valor))):,}".replace(",", ".")


def formato_percentual(valor: float | int | None) -> str:
    if valor is None or pd.isna(valor):
        return "0,0%"
    return f"{float(valor):.1%}".replace(".", ",")


def serie_limpa(df: pd.DataFrame, coluna: str) -> pd.Series:
    if coluna not in df.columns:
        return pd.Series(dtype="object")
    return df[coluna].map(limpar_texto)


def valores_validos(df: pd.DataFrame, coluna: str) -> pd.Series:
    serie = serie_limpa(df, coluna)
    return serie[serie != ""]


def contar_unicos(df: pd.DataFrame, coluna: str) -> int:
    return int(valores_validos(df, coluna).nunique())


def primeiro_numero(df: pd.DataFrame, coluna: str, fallback: int = 0) -> int:
    if coluna not in df.columns:
        return int(fallback)
    numeros = para_numero(df[coluna])
    numeros = numeros[numeros > 0]
    return int(numeros.iloc[0]) if not numeros.empty else int(fallback)


def tabela_lista(df: pd.DataFrame, coluna: str, nome_saida: str) -> pd.DataFrame:
    valores = valores_validos(df, coluna)
    if valores.empty:
        return pd.DataFrame(columns=[nome_saida])
    return pd.DataFrame({nome_saida: valores}).drop_duplicates().reset_index(drop=True)


def tabela_contagem_por_coluna(df: pd.DataFrame, coluna_categoria: str, coluna_quantidade: str | None, nome_categoria: str, nome_quantidade: str) -> pd.DataFrame:
    categorias = valores_validos(df, coluna_categoria)
    if categorias.empty:
        return pd.DataFrame(columns=[nome_categoria, nome_quantidade])

    base = pd.DataFrame({nome_categoria: categorias})
    if coluna_quantidade and coluna_quantidade in df.columns:
        quantidades = para_numero(df.loc[base.index, coluna_quantidade])
        base[nome_quantidade] = quantidades.values
        base[nome_quantidade] = base[nome_quantidade].where(base[nome_quantidade] > 0, 1)
    else:
        base[nome_quantidade] = 1

    base[nome_categoria] = base[nome_categoria].map(limpar_texto)
    base = base[base[nome_categoria] != ""]
    base = base.groupby(nome_categoria, as_index=False)[nome_quantidade].sum()
    base[nome_quantidade] = base[nome_quantidade].astype(int)
    return base.sort_values(nome_quantidade, ascending=False).reset_index(drop=True)


def ler_csv_flexivel(file_bytes: bytes | None = None, caminho: str | None = None, header: int | None = 0) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
    ultimo_erro = None
    for encoding in encodings:
        try:
            if file_bytes is not None:
                return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=encoding, header=header)
            if caminho is not None:
                return pd.read_csv(caminho, sep=None, engine="python", encoding=encoding, header=header)
        except Exception as erro:
            ultimo_erro = erro
    raise RuntimeError(f"Não consegui ler o CSV. Último erro: {ultimo_erro}")


def localizar_arquivo_padrao() -> str | None:
    for nome in ARQUIVOS_PADRAO:
        if Path(nome).exists():
            return nome
    return None


def garantir_colunas_oficiais(df: pd.DataFrame) -> pd.DataFrame:
    saida = df.copy()
    for coluna in COLUNAS_OFICIAIS:
        if coluna not in saida.columns:
            saida[coluna] = ""
    return saida[COLUNAS_OFICIAIS]


def converter_csv_antigo_com_blocos(file_bytes: bytes | None = None, caminho: str | None = None) -> pd.DataFrame:
    bruto = ler_csv_flexivel(file_bytes=file_bytes, caminho=caminho, header=None)
    indice_cabecalho = None

    for idx, linha in bruto.iterrows():
        valores = [limpar_texto(v) for v in linha.tolist()]
        if "Empresas (Dedup)" in valores:
            indice_cabecalho = idx
            break

    if indice_cabecalho is None:
        raise ValueError("Não encontrei uma base reconhecível. Use o CSV tratado ou o CSV original da planilha.")

    dados = bruto.iloc[indice_cabecalho + 1:].reset_index(drop=True)

    def col(indice: int) -> pd.Series:
        if indice >= dados.shape[1]:
            return pd.Series([""] * len(dados))
        return dados.iloc[:, indice]

    base = pd.DataFrame({
        "empresa_mapeada": col(0),
        "evento_mapeado_por_empresa": col(1),
        "ano_evento_mapeado": col(2),
        "setor_deduplicado_detalhado_da_empresa": col(3),
        "empresas_no_setor_deduplicado_detalhado": col(4),
        "setor_consolidado_hard_da_empresa": col(5),
        "empresas_no_setor_consolidado_hard": col(6),
        "tipo_publico_do_evento": col(7),
        "eventos_por_tipo_publico": col(8),
        "nicho_segmento_do_evento": col(9),
        "eventos_por_nicho_segmento": col(10),
        "empresa_priorizada_para_busca_de_contatos": col(11),
        "empresas_priorizadas_para_contato_total": col(12),
        "empresa_com_contato_encontrado": col(13),
        "empresas_com_contato_encontrado_total": col(14),
        "contatos_encontrados_total": col(15),
        "cargo_do_contato_encontrado": col(16),
        "senioridade_do_contato_encontrado": col(17),
        "contatos_por_senioridade": col(18),
        "departamento_do_contato_encontrado": col(19),
        "data_calendario_envio_email": col(20),
        "dia_mes_envio_email": col(20),
        "emails_enviados_no_dia": col(21),
        "status_da_resposta_do_email": col(22),
        "respostas_por_status": col(23),
    })
    return garantir_colunas_oficiais(base)


@st.cache_data(show_spinner=False)
def carregar_base(file_bytes: bytes | None, caminho: str | None) -> pd.DataFrame:
    try:
        df = ler_csv_flexivel(file_bytes=file_bytes, caminho=caminho, header=0)
        df.columns = [normalizar_nome_coluna(c) for c in df.columns]
        df = df.rename(columns=MAPA_COLUNAS_ANTIGAS)
        tem_colunas_oficiais = len(set(COLUNAS_OFICIAIS).intersection(df.columns)) >= 8
        if tem_colunas_oficiais:
            return garantir_colunas_oficiais(df)
    except Exception:
        pass

    return converter_csv_antigo_com_blocos(file_bytes=file_bytes, caminho=caminho)


def preparar_envios(df: pd.DataFrame, ano_padrao: int) -> pd.DataFrame:
    envios = tabela_contagem_por_coluna(df, "data_calendario_envio_email", "emails_enviados_no_dia", "data_envio_email", "emails_enviados")
    if envios.empty:
        return envios

    texto_data = envios["data_envio_email"].astype(str).str.strip()
    data_iso = pd.to_datetime(texto_data, errors="coerce")
    data_dia_mes = pd.to_datetime(texto_data + f"/{ano_padrao}", format="%d/%m/%Y", errors="coerce")
    envios["data_envio"] = data_iso.fillna(data_dia_mes)
    envios = envios.dropna(subset=["data_envio"]).sort_values("data_envio")
    envios["dia_mes"] = envios["data_envio"].dt.strftime("%d/%m")
    envios["emails_acumulados"] = envios["emails_enviados"].cumsum()
    envios["crescimento_absoluto"] = envios["emails_enviados"].diff().fillna(0).astype(int)
    envios["crescimento_percentual"] = envios["emails_enviados"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    return envios.reset_index(drop=True)


def kpi_card(titulo: str, valor: str, detalhe: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-help">{detalhe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def secao(titulo: str, subtitulo: str = "") -> None:
    st.markdown(f"<div class='section-title'>{titulo}</div>", unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f"<div class='section-subtitle'>{subtitulo}</div>", unsafe_allow_html=True)


def preparar_figura(fig: go.Figure, altura: int) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=58, b=20),
        font=dict(family="Inter", color="#E5E7EB"),
        title=dict(font=dict(size=18, color="#F8FAFC"), x=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,.08)", zeroline=False)
    return fig


def grafico_barras(df: pd.DataFrame, categoria: str, quantidade: str, titulo: str, key: str, horizontal: bool = True, top_n: int | None = None, altura: int = 440) -> None:
    if df.empty:
        st.info("Sem dados para exibir neste bloco.")
        return

    base = df.copy().head(top_n) if top_n else df.copy()
    if horizontal:
        base = base.sort_values(quantidade, ascending=True)
        fig = px.bar(base, x=quantidade, y=categoria, orientation="h", text=quantidade, title=titulo, color=quantidade, color_continuous_scale="Sunsetdark")
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title=None)
    else:
        fig = px.bar(base, x=categoria, y=quantidade, text=quantidade, title=titulo, color=quantidade, color_continuous_scale="Sunsetdark")
        fig.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)

    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(preparar_figura(fig, altura), use_container_width=True, key=key)


def grafico_donut(df: pd.DataFrame, categoria: str, quantidade: str, titulo: str, key: str, altura: int = 390) -> None:
    if df.empty:
        st.info("Sem dados para exibir neste bloco.")
        return

    fig = px.pie(df, names=categoria, values=quantidade, hole=.62, title=titulo, color_discrete_sequence=px.colors.sequential.Sunsetdark)
    fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="rgba(255,255,255,.14)", width=1)))
    st.plotly_chart(preparar_figura(fig, altura), use_container_width=True, key=key)


def tabela_com_busca(df: pd.DataFrame, coluna_busca: str, label: str, key: str, altura: int = 420) -> None:
    if df.empty:
        st.info("Sem dados nesta tabela.")
        return

    termo = st.text_input(label, placeholder="Digite para filtrar", key=f"busca_{key}")
    visual = df.copy()
    if termo and coluna_busca in visual.columns:
        visual = visual[visual[coluna_busca].astype(str).str.contains(termo, case=False, na=False)]

    st.dataframe(visual, use_container_width=True, hide_index=True, height=altura)
    st.download_button(
        "Baixar tabela filtrada em CSV",
        data=visual.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"download_{key}",
    )


def renomear_para_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: ROTULOS.get(c, c) for c in df.columns})


st.sidebar.title("Base de dados")
st.sidebar.caption("Use o CSV tratado no GitHub ou envie manualmente pelo painel abaixo.")

arquivo_enviado = st.sidebar.file_uploader("Enviar CSV", type=["csv"], key="upload_csv")
ano_padrao = st.sidebar.number_input("Ano usado quando o envio vier só como dia/mês", min_value=2020, max_value=2035, value=datetime.today().year, step=1)

caminho_padrao = localizar_arquivo_padrao()
bytes_csv = arquivo_enviado.getvalue() if arquivo_enviado else None
caminho_csv = None if arquivo_enviado else caminho_padrao

if not bytes_csv and not caminho_csv:
    st.error("Não encontrei o CSV no projeto. Coloque `base_dashboard_comercial_prospeccao.csv` na raiz do GitHub ou envie o arquivo pela lateral.")
    st.stop()

try:
    base = carregar_base(bytes_csv, caminho_csv)
except Exception as erro:
    st.error(f"Não consegui montar o dashboard com esse arquivo. Erro: {erro}")
    st.stop()

empresas_mapeadas = tabela_lista(base, "empresa_mapeada", "Empresa mapeada")
eventos_mapeados = tabela_lista(base, "evento_mapeado_por_empresa", "Evento mapeado")
empresas_eventos = base[["empresa_mapeada", "evento_mapeado_por_empresa", "ano_evento_mapeado"]].copy()
empresas_eventos = empresas_eventos.applymap(limpar_texto)
empresas_eventos = empresas_eventos[(empresas_eventos["empresa_mapeada"] != "") | (empresas_eventos["evento_mapeado_por_empresa"] != "")]
empresas_eventos = empresas_eventos.drop_duplicates().rename(columns=ROTULOS).reset_index(drop=True)

setores_detalhados = tabela_contagem_por_coluna(base, "setor_deduplicado_detalhado_da_empresa", "empresas_no_setor_deduplicado_detalhado", "Setor deduplicado detalhado", "Empresas mapeadas")
setores_hard = tabela_contagem_por_coluna(base, "setor_consolidado_hard_da_empresa", "empresas_no_setor_consolidado_hard", "Setor consolidado hard", "Empresas mapeadas")
tipos_evento = tabela_contagem_por_coluna(base, "tipo_publico_do_evento", "eventos_por_tipo_publico", "Tipo de público do evento", "Eventos mapeados")
nichos_evento = tabela_contagem_por_coluna(base, "nicho_segmento_do_evento", "eventos_por_nicho_segmento", "Nicho ou segmento do evento", "Eventos mapeados")
empresas_priorizadas = tabela_lista(base, "empresa_priorizada_para_busca_de_contatos", "Empresa priorizada para busca de contatos")
empresas_com_contato = tabela_lista(base, "empresa_com_contato_encontrado", "Empresa com contato encontrado")

priorizadas_chave = set(empresas_priorizadas["Empresa priorizada para busca de contatos"].map(normalizar_chave))
encontradas_chave = set(empresas_com_contato["Empresa com contato encontrado"].map(normalizar_chave))
chaves_faltantes = priorizadas_chave - encontradas_chave
empresas_sem_contato = empresas_priorizadas[empresas_priorizadas["Empresa priorizada para busca de contatos"].map(normalizar_chave).isin(chaves_faltantes)].reset_index(drop=True)

cargos_contatos = tabela_contagem_por_coluna(base, "cargo_do_contato_encontrado", None, "Cargo do contato encontrado", "Contatos mapeados")
senioridades = tabela_contagem_por_coluna(base, "senioridade_do_contato_encontrado", "contatos_por_senioridade", "Senioridade do contato encontrado", "Contatos mapeados")
departamentos = tabela_contagem_por_coluna(base, "departamento_do_contato_encontrado", None, "Departamento do contato encontrado", "Contatos mapeados")
envios = preparar_envios(base, int(ano_padrao))
respostas = tabela_contagem_por_coluna(base, "status_da_resposta_do_email", "respostas_por_status", "Status da resposta do email", "Respostas mapeadas")

total_empresas = contar_unicos(base, "empresa_mapeada")
total_eventos = contar_unicos(base, "evento_mapeado_por_empresa")
total_setores_detalhados = len(setores_detalhados)
total_setores_hard = len(setores_hard)
total_priorizadas = max(primeiro_numero(base, "empresas_priorizadas_para_contato_total", len(empresas_priorizadas)), len(empresas_priorizadas))
total_com_contato = max(primeiro_numero(base, "empresas_com_contato_encontrado_total", len(empresas_com_contato)), len(empresas_com_contato))
total_contatos = max(primeiro_numero(base, "contatos_encontrados_total", int(cargos_contatos["Contatos mapeados"].sum()) if not cargos_contatos.empty else 0), int(cargos_contatos["Contatos mapeados"].sum()) if not cargos_contatos.empty else 0)
total_enviados = int(envios["emails_enviados"].sum()) if not envios.empty else 0
total_respostas = int(respostas["Respostas mapeadas"].sum()) if not respostas.empty else 0
sem_resposta = respostas[respostas["Status da resposta do email"].map(normalizar_chave).eq("sem resposta")]
total_sem_resposta = int(sem_resposta["Respostas mapeadas"].sum()) if not sem_resposta.empty else 0
respostas_com_status_util = max(total_respostas - total_sem_resposta, 0)
taxa_cobertura = total_com_contato / total_priorizadas if total_priorizadas else 0
taxa_resposta_util = respostas_com_status_util / total_enviados if total_enviados else 0

st.markdown(
    """
    <div class="hero">
        <span class="badge">PROSPECÇÃO COMERCIAL</span>
        <span class="badge">EVENTOS</span>
        <span class="badge">CONTATOS</span>
        <span class="badge">ENVIOS</span>
        <h1>Dashboard Comercial de Prospecção</h1>
        <p>Visão executiva para comparar empresas mapeadas, setores consolidados, eventos, cobertura de contatos, senioridades, cargos, volume de envios e respostas comerciais.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

linha1 = st.columns(4)
with linha1[0]:
    kpi_card("Empresas mapeadas", formato_inteiro(total_empresas), "Empresas únicas identificadas na base")
with linha1[1]:
    kpi_card("Eventos mapeados", formato_inteiro(total_eventos), "Eventos únicos relacionados às empresas")
with linha1[2]:
    kpi_card("Setores hard", formato_inteiro(total_setores_hard), f"{formato_inteiro(total_setores_detalhados)} setores detalhados")
with linha1[3]:
    kpi_card("Cobertura de contatos", formato_percentual(taxa_cobertura), f"{formato_inteiro(total_com_contato)} de {formato_inteiro(total_priorizadas)} empresas")

linha2 = st.columns(4)
with linha2[0]:
    kpi_card("Contatos encontrados", formato_inteiro(total_contatos), "Volume total de contatos mapeados")
with linha2[1]:
    kpi_card("Cargos únicos", formato_inteiro(len(cargos_contatos)), "Cargos diferentes encontrados")
with linha2[2]:
    kpi_card("Emails enviados", formato_inteiro(total_enviados), "Soma dos envios por dia")
with linha2[3]:
    kpi_card("Respostas úteis", formato_inteiro(respostas_com_status_util), f"Taxa sobre envios: {formato_percentual(taxa_resposta_util)}")

st.sidebar.divider()
st.sidebar.title("Filtros de visualização")

filtro_setores = st.sidebar.multiselect("Setor consolidado hard", options=setores_hard["Setor consolidado hard"].tolist(), default=[])
filtro_tipos_evento = st.sidebar.multiselect("Tipo de público do evento", options=tipos_evento["Tipo de público do evento"].tolist(), default=[])
filtro_respostas = st.sidebar.multiselect("Status da resposta do email", options=respostas["Status da resposta do email"].tolist(), default=[])

visao_setores_hard = setores_hard if not filtro_setores else setores_hard[setores_hard["Setor consolidado hard"].isin(filtro_setores)]
visao_tipos_evento = tipos_evento if not filtro_tipos_evento else tipos_evento[tipos_evento["Tipo de público do evento"].isin(filtro_tipos_evento)]
visao_respostas = respostas if not filtro_respostas else respostas[respostas["Status da resposta do email"].isin(filtro_respostas)]

aba_geral, aba_empresas, aba_eventos, aba_contatos, aba_envios, aba_dados = st.tabs([
    "Visão executiva",
    "Empresas e setores",
    "Eventos",
    "Contatos",
    "Envios e respostas",
    "Base explorável",
])

with aba_geral:
    esquerda, direita = st.columns([1.05, .95])
    with esquerda:
        secao("Panorama executivo", "Resumo do volume, cobertura comercial e avanço dos envios.")
        resumo = pd.DataFrame(
            [
                ["Empresas mapeadas", total_empresas],
                ["Eventos mapeados", total_eventos],
                ["Setores detalhados", total_setores_detalhados],
                ["Setores consolidados hard", total_setores_hard],
                ["Empresas priorizadas para contato", total_priorizadas],
                ["Empresas com contato encontrado", total_com_contato],
                ["Empresas ainda sem contato", max(total_priorizadas - total_com_contato, 0)],
                ["Contatos encontrados", total_contatos],
                ["Cargos únicos", len(cargos_contatos)],
                ["Emails enviados", total_enviados],
                ["Respostas mapeadas", total_respostas],
                ["Respostas úteis", respostas_com_status_util],
            ],
            columns=["Indicador comercial", "Resultado"],
        )
        st.dataframe(resumo, use_container_width=True, hide_index=True, height=430)

    with direita:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=taxa_cobertura * 100,
                number={"suffix": "%", "valueformat": ".1f", "font": {"color": "#FFFFFF", "size": 54}},
                title={"text": "Cobertura de empresas com contatos", "font": {"color": "#E5E7EB", "size": 18}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#94A3B8"},
                    "bar": {"color": "#F97316", "thickness": 0.26},
                    "bgcolor": "rgba(255,255,255,.04)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,.12)",
                    "steps": [
                        {"range": [0, 50], "color": "rgba(239,68,68,.24)"},
                        {"range": [50, 80], "color": "rgba(245,158,11,.22)"},
                        {"range": [80, 100], "color": "rgba(34,197,94,.22)"},
                    ],
                },
            )
        )
        st.plotly_chart(preparar_figura(fig, 430), use_container_width=True, key="gauge_cobertura")

    c1, c2 = st.columns(2)
    with c1:
        grafico_donut(visao_tipos_evento, "Tipo de público do evento", "Eventos mapeados", "Distribuição por tipo de público", "donut_tipo_publico")
    with c2:
        grafico_donut(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Distribuição dos status de resposta", "donut_respostas")

with aba_empresas:
    secao("Empresas e setores", "Use o setor hard para leitura executiva. Use o setor detalhado para investigação fina.")
    c1, c2 = st.columns([1.05, .95])
    with c1:
        grafico_barras(visao_setores_hard, "Setor consolidado hard", "Empresas mapeadas", "Empresas por setor consolidado hard", "bar_setor_hard", top_n=30, altura=560)
    with c2:
        if setores_hard.empty:
            st.info("Sem setores para exibir.")
        else:
            fig = px.treemap(setores_hard, path=["Setor consolidado hard"], values="Empresas mapeadas", title="Concentração visual por setor hard", color="Empresas mapeadas", color_continuous_scale="Sunsetdark")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(preparar_figura(fig, 560), use_container_width=True, key="treemap_setor_hard")

    c3, c4 = st.columns([1.05, .95])
    with c3:
        grafico_barras(setores_detalhados, "Setor deduplicado detalhado", "Empresas mapeadas", "Top setores detalhados", "bar_setor_detalhado", top_n=35, altura=620)
    with c4:
        secao("Empresas mapeadas", "Lista pesquisável das empresas identificadas.")
        tabela_com_busca(empresas_mapeadas, "Empresa mapeada", "Buscar empresa mapeada", "empresas_mapeadas", altura=510)

with aba_eventos:
    secao("Eventos", "Leitura dos eventos mapeados, tipos de público e nichos comerciais.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Eventos únicos", formato_inteiro(total_eventos))
    m2.metric("Tipos de público", formato_inteiro(len(tipos_evento)))
    m3.metric("Nichos ou segmentos", formato_inteiro(len(nichos_evento)))

    c1, c2 = st.columns([.85, 1.15])
    with c1:
        grafico_donut(visao_tipos_evento, "Tipo de público do evento", "Eventos mapeados", "Eventos por tipo de público", "eventos_tipo_publico", altura=440)
    with c2:
        grafico_barras(nichos_evento, "Nicho ou segmento do evento", "Eventos mapeados", "Nichos e segmentos com mais eventos", "bar_nichos", top_n=30, altura=440)

    secao("Relação empresa x evento", "Tabela útil para investigar quais empresas aparecem relacionadas a quais eventos.")
    tabela_com_busca(empresas_eventos, "Empresa mapeada", "Buscar por empresa", "empresa_evento", altura=470)

with aba_contatos:
    secao("Contatos", "Mostra cobertura das empresas priorizadas, contatos encontrados, senioridade, cargos e departamentos.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Empresas priorizadas", formato_inteiro(total_priorizadas))
    m2.metric("Empresas com contato", formato_inteiro(total_com_contato))
    m3.metric("Empresas faltantes", formato_inteiro(max(total_priorizadas - total_com_contato, 0)))
    m4.metric("Contatos encontrados", formato_inteiro(total_contatos))

    c1, c2 = st.columns([.9, 1.1])
    with c1:
        grafico_donut(senioridades, "Senioridade do contato encontrado", "Contatos mapeados", "Contatos por senioridade", "donut_senioridade", altura=450)
    with c2:
        grafico_barras(cargos_contatos, "Cargo do contato encontrado", "Contatos mapeados", "Cargos com maior recorrência", "bar_cargos", top_n=30, altura=450)

    c3, c4 = st.columns([1, 1])
    with c3:
        grafico_barras(departamentos, "Departamento do contato encontrado", "Contatos mapeados", "Departamentos mapeados", "bar_departamentos", top_n=25, altura=420)
    with c4:
        grafico_barras(empresas_sem_contato.assign(**{"Empresas faltantes": 1}), "Empresa priorizada para busca de contatos", "Empresas faltantes", "Empresas priorizadas ainda sem contato", "bar_empresas_faltantes", top_n=25, altura=420)

    c5, c6 = st.columns([1, 1])
    with c5:
        secao("Empresas priorizadas para busca")
        tabela_com_busca(empresas_priorizadas, "Empresa priorizada para busca de contatos", "Buscar empresa priorizada", "empresas_priorizadas", altura=420)
    with c6:
        secao("Empresas com contato encontrado")
        tabela_com_busca(empresas_com_contato, "Empresa com contato encontrado", "Buscar empresa encontrada", "empresas_com_contato", altura=420)

with aba_envios:
    secao("Envios e respostas", "Volume enviado por dia, acumulado de envios, evolução e leitura dos status de resposta.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Emails enviados", formato_inteiro(total_enviados))
    m2.metric("Dias com envio", formato_inteiro(len(envios)))
    m3.metric("Respostas úteis", formato_inteiro(respostas_com_status_util))
    m4.metric("Taxa de resposta útil", formato_percentual(taxa_resposta_util))

    if not envios.empty:
        c1, c2 = st.columns([1.15, .85])
        with c1:
            fig = px.bar(envios, x="dia_mes", y="emails_enviados", text="emails_enviados", title="Emails enviados por dia", color="emails_enviados", color_continuous_scale="Sunsetdark")
            fig.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(preparar_figura(fig, 450), use_container_width=True, key="bar_envios_dia")
        with c2:
            fig = px.line(envios, x="dia_mes", y="emails_acumulados", markers=True, title="Acumulado de emails enviados")
            fig.update_traces(line=dict(width=4, color="#F97316"), marker=dict(size=9, color="#FB7185"))
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            st.plotly_chart(preparar_figura(fig, 450), use_container_width=True, key="linha_acumulado_envios")

        tabela_envios = envios[["data_envio", "emails_enviados", "emails_acumulados", "crescimento_absoluto", "crescimento_percentual"]].copy()
        tabela_envios["data_envio"] = tabela_envios["data_envio"].dt.strftime("%d/%m/%Y")
        tabela_envios["crescimento_percentual"] = tabela_envios["crescimento_percentual"].map(formato_percentual)
        tabela_envios = tabela_envios.rename(columns={
            "data_envio": "Data do envio",
            "emails_enviados": "Emails enviados",
            "emails_acumulados": "Emails acumulados",
            "crescimento_absoluto": "Crescimento absoluto",
            "crescimento_percentual": "Crescimento percentual",
        })
        st.dataframe(tabela_envios, use_container_width=True, hide_index=True, height=260)
    else:
        st.info("Sem dados de envio para exibir.")

    c3, c4 = st.columns([.9, 1.1])
    with c3:
        grafico_donut(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Status de resposta", "donut_status_envio", altura=430)
    with c4:
        grafico_barras(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Quantidade por status de resposta", "bar_status_resposta", top_n=25, altura=430)

with aba_dados:
    secao("Base explorável", "Tabelas separadas por bloco para investigar a origem de cada número.")
    opcoes = {
        "Empresas mapeadas": empresas_mapeadas,
        "Relação empresa x evento": empresas_eventos,
        "Setores detalhados": setores_detalhados,
        "Setores consolidados hard": setores_hard,
        "Tipos de público dos eventos": tipos_evento,
        "Nichos e segmentos dos eventos": nichos_evento,
        "Empresas priorizadas para contatos": empresas_priorizadas,
        "Empresas com contatos encontrados": empresas_com_contato,
        "Empresas ainda sem contatos": empresas_sem_contato,
        "Cargos dos contatos": cargos_contatos,
        "Senioridades dos contatos": senioridades,
        "Departamentos dos contatos": departamentos,
        "Envios por dia": envios,
        "Status das respostas": respostas,
        "Base tratada completa": renomear_para_exibicao(base),
    }
    bloco = st.selectbox("Escolha a visão para explorar", list(opcoes.keys()), key="select_bloco_exploravel")
    tabela = opcoes[bloco]
    st.dataframe(tabela, use_container_width=True, hide_index=True, height=560)
    st.download_button(
        "Baixar esta visão em CSV",
        data=tabela.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{normalizar_nome_coluna(bloco)}.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_bloco_exploravel",
    )

st.caption("Dashboard montado a partir dos blocos Empresas, Eventos, Contatos e Dados de envio. Para uma etapa futura, o ideal é transformar tudo em tabelas relacionais normalizadas.")
