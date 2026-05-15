from __future__ import annotations

import io
import os
import unicodedata
from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================
# Configuração geral
# =============================
st.set_page_config(
    page_title="Dashboard de Prospects",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_FILES = [
    "dados.csv",
    "prospects.csv",
    "Lista de Prospects - Página12 (1).csv",
    "Lista de Prospects - Pagina12 (1).csv",
]


# =============================
# Estilo visual
# =============================
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }
    .hero {
        padding: 1.25rem 1.35rem;
        border: 1px solid rgba(148, 163, 184, .22);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(15,23,42,.95), rgba(30,41,59,.88));
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 18px 45px rgba(15,23,42,.12);
    }
    .hero h1 {
        font-size: 2rem;
        line-height: 1.12;
        margin: 0 0 .35rem 0;
        letter-spacing: -0.03em;
    }
    .hero p {
        margin: 0;
        color: rgba(226,232,240,.92);
        font-size: .98rem;
    }
    .kpi-card {
        border: 1px solid rgba(148, 163, 184, .22);
        border-radius: 22px;
        padding: 1rem 1rem .85rem 1rem;
        background: rgba(255,255,255,.76);
        box-shadow: 0 12px 28px rgba(15,23,42,.07);
        min-height: 116px;
    }
    .kpi-label {
        font-size: .78rem;
        color: #64748b;
        margin-bottom: .45rem;
        text-transform: uppercase;
        letter-spacing: .04em;
        font-weight: 700;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 850;
        color: #0f172a;
        line-height: 1;
    }
    .kpi-help {
        font-size: .78rem;
        color: #64748b;
        margin-top: .5rem;
    }
    .section-title {
        font-size: 1.18rem;
        font-weight: 850;
        color: #0f172a;
        margin: .35rem 0 .2rem 0;
    }
    .section-subtitle {
        color: #64748b;
        font-size: .92rem;
        margin-bottom: .7rem;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 850;
    }
    div[data-testid="stTabs"] button p {
        font-weight: 700;
    }
    .small-note {
        color: #64748b;
        font-size: .85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================
# Funções utilitárias
# =============================
def strip_accents(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def clean_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).replace("\u00a0", " ").strip()
    text = " ".join(text.split())
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def clean_category(value: object, fallback: str = "Não informado") -> str:
    text = clean_text(value)
    if text is None:
        return fallback
    if text.upper() in {"#VALUE!", "#N/A", "#REF!", "#NAME?"}:
        return fallback
    return text


def to_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def format_int(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def format_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0,0%"
    return f"{float(value):.1%}".replace(".", ",")


def normalize_key(value: object) -> str:
    return strip_accents(value).lower().strip()


def find_first_existing_file(files: Iterable[str]) -> str | None:
    for file in files:
        if os.path.exists(file):
            return file
    return None


def read_csv_anywhere(file_bytes: bytes | None = None, file_path: str | None = None, url: str | None = None) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
    last_error = None

    for encoding in encodings:
        try:
            if file_bytes is not None:
                return pd.read_csv(io.BytesIO(file_bytes), header=None, sep=None, engine="python", encoding=encoding)
            if file_path is not None:
                return pd.read_csv(file_path, header=None, sep=None, engine="python", encoding=encoding)
            if url:
                return pd.read_csv(url, header=None, sep=None, engine="python", encoding=encoding)
        except Exception as exc:  # pragma: no cover
            last_error = exc

    raise RuntimeError(f"Não consegui ler o CSV. Último erro: {last_error}")


def locate_header(raw: pd.DataFrame) -> int:
    target = "Empresas (Dedup)"
    for idx, row in raw.iterrows():
        values = [clean_text(v) for v in row.tolist()]
        if target in values:
            return int(idx)
    raise ValueError("Não encontrei a linha de cabeçalho com 'Empresas (Dedup)'.")


def get_one_number(data: pd.DataFrame, col_idx: int) -> int:
    if col_idx >= data.shape[1]:
        return 0
    nums = to_number(data.iloc[:, col_idx]).dropna()
    if nums.empty:
        return 0
    return int(nums.iloc[0])


def get_list_table(data: pd.DataFrame, col_idx: int, name: str) -> pd.DataFrame:
    if col_idx >= data.shape[1]:
        return pd.DataFrame(columns=[name])
    out = pd.DataFrame({name: data.iloc[:, col_idx].map(clean_text)})
    out = out.dropna().drop_duplicates().reset_index(drop=True)
    return out


def get_count_table(data: pd.DataFrame, label_idx: int, count_idx: int, label: str, count: str = "qtd") -> pd.DataFrame:
    if max(label_idx, count_idx) >= data.shape[1]:
        return pd.DataFrame(columns=[label, count])
    out = pd.DataFrame(
        {
            label: data.iloc[:, label_idx].map(lambda x: clean_category(x)),
            count: to_number(data.iloc[:, count_idx]),
        }
    )
    out = out.dropna(subset=[label])
    out = out[out[label].astype(str).str.strip() != ""]
    out[count] = out[count].fillna(0).astype(int)
    out = out[out[label] != "Não informado"]
    out = out.groupby(label, as_index=False)[count].sum()
    out = out.sort_values(count, ascending=False).reset_index(drop=True)
    return out


def parse_send_dates(envios: pd.DataFrame, year: int) -> pd.DataFrame:
    if envios.empty:
        return envios
    out = envios.copy()
    raw = out["dia_envio"].astype(str).str.strip()
    parsed = pd.to_datetime(raw + f"/{year}", format="%d/%m/%Y", errors="coerce")
    fallback = pd.to_datetime(raw, errors="coerce", dayfirst=True)
    out["data_envio"] = parsed.fillna(fallback)
    out = out.dropna(subset=["data_envio"])
    out = out.sort_values("data_envio")
    out["acumulado"] = out["qtd_enviados"].cumsum()
    out["variacao_abs"] = out["qtd_enviados"].diff().fillna(0).astype(int)
    out["variacao_pct"] = out["qtd_enviados"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    out["data_label"] = out["data_envio"].dt.strftime("%d/%m")
    return out


@st.cache_data(show_spinner=False)
def parse_dashboard_data(file_bytes: bytes | None, file_path: str | None, url: str | None, selected_year: int) -> dict[str, pd.DataFrame | int | float]:
    raw = read_csv_anywhere(file_bytes=file_bytes, file_path=file_path, url=url)
    header_idx = locate_header(raw)
    data = raw.iloc[header_idx + 1 :].reset_index(drop=True)

    empresas = get_list_table(data, 0, "empresa")
    eventos = get_list_table(data, 1, "evento")
    anos = get_list_table(data, 2, "ano")
    setores = get_count_table(data, 3, 4, "setor_dedup", "qtd")
    setores_hard = get_count_table(data, 5, 6, "setor_hard", "qtd")
    tipos_evento = get_count_table(data, 7, 8, "tipo_evento", "qtd")
    nichos = get_count_table(data, 9, 10, "nicho", "qtd")
    empresas_precisas = get_list_table(data, 11, "empresa")
    empresas_encontradas = get_list_table(data, 13, "empresa")
    cargos = get_list_table(data, 16, "cargo")
    senioridades = get_count_table(data, 17, 18, "senioridade", "qtd")
    departamentos = get_list_table(data, 19, "departamento")
    departamentos["departamento"] = departamentos["departamento"].map(lambda x: clean_category(x, "Não informado"))
    departamentos = departamentos[departamentos["departamento"] != "Não informado"].drop_duplicates().reset_index(drop=True)

    envios = get_count_table(data, 20, 21, "dia_envio", "qtd_enviados")
    envios = parse_send_dates(envios, selected_year)
    respostas = get_count_table(data, 22, 23, "estado_resposta", "qtd")

    total_empresas_precisas = max(get_one_number(data, 12), len(empresas_precisas))
    total_empresas_encontradas = max(get_one_number(data, 14), len(empresas_encontradas))
    total_contatos = max(get_one_number(data, 15), len(cargos))

    needed_keys = set(empresas_precisas["empresa"].map(normalize_key))
    found_keys = set(empresas_encontradas["empresa"].map(normalize_key))
    missing_keys = needed_keys - found_keys
    faltantes = empresas_precisas[empresas_precisas["empresa"].map(normalize_key).isin(missing_keys)].reset_index(drop=True)

    respostas_total = int(respostas["qtd"].sum()) if not respostas.empty else 0
    enviados_total = int(envios["qtd_enviados"].sum()) if not envios.empty else 0
    resposta_sem_resposta = respostas[respostas["estado_resposta"].map(normalize_key).eq("sem resposta")]
    sem_resposta = int(resposta_sem_resposta["qtd"].sum()) if not resposta_sem_resposta.empty else 0
    respostas_com_status = max(respostas_total - sem_resposta, 0)

    return {
        "raw": raw,
        "empresas": empresas,
        "eventos": eventos,
        "anos": anos,
        "setores": setores,
        "setores_hard": setores_hard,
        "tipos_evento": tipos_evento,
        "nichos": nichos,
        "empresas_precisas": empresas_precisas,
        "empresas_encontradas": empresas_encontradas,
        "faltantes": faltantes,
        "cargos": cargos,
        "senioridades": senioridades,
        "departamentos": departamentos,
        "envios": envios,
        "respostas": respostas,
        "total_empresas_precisas": total_empresas_precisas,
        "total_empresas_encontradas": total_empresas_encontradas,
        "total_contatos": total_contatos,
        "respostas_total": respostas_total,
        "respostas_com_status": respostas_com_status,
        "enviados_total": enviados_total,
    }


def kpi_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, orientation: str = "v", height: int = 420, top_n: int | None = None) -> None:
    if df.empty:
        st.info("Sem dados para exibir aqui.")
        return
    plot_df = df.copy()
    if top_n:
        plot_df = plot_df.head(top_n)
    if orientation == "h":
        plot_df = plot_df.sort_values(x, ascending=True)
        fig = px.bar(plot_df, x=x, y=y, orientation="h", text=x, title=title)
        fig.update_traces(textposition="outside", cliponaxis=False)
    else:
        fig = px.bar(plot_df, x=x, y=y, text=y, title=title)
        fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=height,
        title_x=0,
        margin=dict(l=10, r=20, t=55, b=20),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def donut_chart(df: pd.DataFrame, names: str, values: str, title: str, height: int = 390) -> None:
    if df.empty:
        st.info("Sem dados para exibir aqui.")
        return
    fig = px.pie(df, names=names, values=values, hole=.58, title=title)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=height, title_x=0, margin=dict(l=10, r=10, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)


def searchable_table(df: pd.DataFrame, search_col: str, label: str, height: int = 390) -> None:
    if df.empty:
        st.info("Sem dados nessa tabela.")
        return
    term = st.text_input(label, placeholder="Digite para filtrar...")
    view = df.copy()
    if term:
        view = view[view[search_col].astype(str).str.contains(term, case=False, na=False)]
    st.dataframe(view, use_container_width=True, hide_index=True, height=height)
    csv = view.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar tabela filtrada em CSV",
        data=csv,
        file_name=f"{search_col}_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =============================
# Entrada de dados
# =============================
st.sidebar.title("Base de dados")
st.sidebar.caption("Use o CSV publicado no GitHub ou envie um arquivo manualmente.")

uploaded = st.sidebar.file_uploader("Enviar CSV", type=["csv"])
selected_year = st.sidebar.number_input("Ano usado para interpretar dias de envio", min_value=2020, max_value=2035, value=datetime.today().year, step=1)

csv_url = ""
try:
    csv_url = st.secrets.get("CSV_URL", "")
except Exception:
    csv_url = ""

local_file = find_first_existing_file(DEFAULT_FILES)

file_bytes = uploaded.getvalue() if uploaded else None
file_path = None if uploaded or csv_url else local_file
url = csv_url if not uploaded and csv_url else None

if not uploaded and not file_path and not url:
    st.warning(
        "Não encontrei um CSV no repositório. Envie o arquivo pela lateral ou coloque o arquivo como `dados.csv` na raiz do GitHub."
    )
    st.stop()

try:
    data = parse_dashboard_data(file_bytes, file_path, url, int(selected_year))
except Exception as exc:
    st.error(f"Não consegui montar o dashboard com esse arquivo. Erro: {exc}")
    st.stop()

empresas = data["empresas"]
eventos = data["eventos"]
anos = data["anos"]
setores = data["setores"]
setores_hard = data["setores_hard"]
tipos_evento = data["tipos_evento"]
nichos = data["nichos"]
empresas_precisas = data["empresas_precisas"]
empresas_encontradas = data["empresas_encontradas"]
faltantes = data["faltantes"]
cargos = data["cargos"]
senioridades = data["senioridades"]
departamentos = data["departamentos"]
envios = data["envios"]
respostas = data["respostas"]

# =============================
# Header
# =============================
st.markdown(
    """
    <div class="hero">
        <h1>Dashboard de Prospects, Eventos, Contatos e Envios</h1>
        <p>Visão executiva para comparar empresas mapeadas, setores, eventos, cobertura de contatos, senioridades, cargos, envios e respostas.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# KPIs principais
# =============================
total_empresas = len(empresas)
total_eventos = len(eventos)
total_setores = len(setores)
total_setores_hard = len(setores_hard)
total_precisas = int(data["total_empresas_precisas"])
total_encontradas = int(data["total_empresas_encontradas"])
total_contatos = int(data["total_contatos"])
total_enviados = int(data["enviados_total"])
coverage = total_encontradas / total_precisas if total_precisas else 0
respostas_total = int(data["respostas_total"])
respostas_com_status = int(data["respostas_com_status"])
taxa_status = respostas_com_status / total_enviados if total_enviados else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Empresas mapeadas", format_int(total_empresas), "Empresas únicas no bloco de prospects")
with k2:
    kpi_card("Eventos únicos", format_int(total_eventos), "Eventos deduplicados identificados")
with k3:
    kpi_card("Setores hard", format_int(total_setores_hard), f"{format_int(total_setores)} setores detalhados")
with k4:
    kpi_card("Cobertura de contatos", format_pct(coverage), f"{format_int(total_encontradas)} de {format_int(total_precisas)} empresas")

k5, k6, k7, k8 = st.columns(4)
with k5:
    kpi_card("Contatos totais", format_int(total_contatos), "Total calculado no bloco de contatos")
with k6:
    kpi_card("Cargos únicos", format_int(len(cargos)), "Cargos diferentes encontrados")
with k7:
    kpi_card("Emails enviados", format_int(total_enviados), "Soma dos envios por dia")
with k8:
    kpi_card("Respostas com status", format_int(respostas_com_status), f"Taxa sobre envios: {format_pct(taxa_status)}")

# =============================
# Filtros gerais
# =============================
st.sidebar.divider()
st.sidebar.title("Filtros visuais")

selected_setores_hard = st.sidebar.multiselect(
    "Setor hard",
    options=setores_hard["setor_hard"].tolist(),
    default=[],
)
selected_tipos = st.sidebar.multiselect(
    "Tipo de evento",
    options=tipos_evento["tipo_evento"].tolist(),
    default=[],
)
selected_nichos = st.sidebar.multiselect(
    "Nicho/segmento",
    options=nichos["nicho"].tolist(),
    default=[],
)
selected_status = st.sidebar.multiselect(
    "Estado da resposta",
    options=respostas["estado_resposta"].tolist(),
    default=[],
)

view_setores_hard = setores_hard if not selected_setores_hard else setores_hard[setores_hard["setor_hard"].isin(selected_setores_hard)]
view_tipos = tipos_evento if not selected_tipos else tipos_evento[tipos_evento["tipo_evento"].isin(selected_tipos)]
view_nichos = nichos if not selected_nichos else nichos[nichos["nicho"].isin(selected_nichos)]
view_respostas = respostas if not selected_status else respostas[respostas["estado_resposta"].isin(selected_status)]

# =============================
# Abas
# =============================
tab_geral, tab_empresas, tab_eventos, tab_contatos, tab_envios, tab_explorar = st.tabs(
    ["Visão geral", "Empresas", "Eventos", "Contatos", "Envios e respostas", "Explorar dados"]
)

with tab_geral:
    c1, c2 = st.columns([1.1, .9])
    with c1:
        section("Panorama da base", "Um resumo rápido para entender volume, cobertura e avanço comercial.")
        resumo = pd.DataFrame(
            [
                ["Empresas mapeadas", total_empresas],
                ["Eventos únicos", total_eventos],
                ["Setores detalhados", total_setores],
                ["Setores hard", total_setores_hard],
                ["Empresas desejadas para contato", total_precisas],
                ["Empresas com contato encontrado", total_encontradas],
                ["Empresas ainda sem contato", max(total_precisas - total_encontradas, 0)],
                ["Contatos totais", total_contatos],
                ["Emails enviados", total_enviados],
                ["Respostas classificadas", respostas_total],
                ["Respostas com status útil", respostas_com_status],
            ],
            columns=["Métrica", "Valor"],
        )
        st.dataframe(resumo, use_container_width=True, hide_index=True, height=420)
    with c2:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=coverage * 100,
                number={"suffix": "%", "valueformat": ".1f"},
                title={"text": "Cobertura de empresas com contatos"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"thickness": 0.24},
                    "steps": [
                        {"range": [0, 50], "color": "rgba(239,68,68,.18)"},
                        {"range": [50, 80], "color": "rgba(245,158,11,.18)"},
                        {"range": [80, 100], "color": "rgba(34,197,94,.18)"},
                    ],
                },
            )
        )
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        donut_chart(view_tipos, "tipo_evento", "qtd", "Distribuição por tipo de evento")
    with c4:
        donut_chart(view_respostas, "estado_resposta", "qtd", "Distribuição dos estados de resposta")

with tab_empresas:
    section("Empresas e setores", "Aqui a leitura boa é separar setor detalhado de setor hard. O hard é a visão limpa para decisão.")
    c1, c2 = st.columns([1, 1])
    with c1:
        bar_chart(view_setores_hard, "qtd", "setor_hard", "Setores hard por quantidade", orientation="h", height=520, top_n=25)
    with c2:
        if setores_hard.empty:
            st.info("Sem setores para exibir.")
        else:
            fig = px.treemap(setores_hard, path=["setor_hard"], values="qtd", title="Mapa de concentração por setor hard")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=55, b=10))
            st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns([1.15, .85])
    with c3:
        bar_chart(setores, "qtd", "setor_dedup", "Top setores detalhados", orientation="h", height=560, top_n=30)
    with c4:
        section("Lista de empresas", "Busca rápida por empresa mapeada.")
        searchable_table(empresas, "empresa", "Buscar empresa", height=480)

with tab_eventos:
    section("Eventos", "Volume total, tipo de evento e nichos. Bom para enxergar onde sua base está mais concentrada.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Eventos únicos", format_int(total_eventos))
    with c2:
        st.metric("Tipos de evento", format_int(len(tipos_evento)))
    with c3:
        st.metric("Nichos/segmentos", format_int(len(nichos)))

    c4, c5 = st.columns([.85, 1.15])
    with c4:
        donut_chart(view_tipos, "tipo_evento", "qtd", "Eventos por tipo", height=430)
    with c5:
        bar_chart(view_nichos, "qtd", "nicho", "Nichos/segmentos por quantidade", orientation="h", height=430, top_n=25)

    section("Lista de eventos", "Use a busca para encontrar um evento específico.")
    searchable_table(eventos, "evento", "Buscar evento", height=360)

with tab_contatos:
    section("Contatos", "Mostra a cobertura das empresas desejadas, contatos encontrados, senioridade, cargos e departamentos.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Empresas desejadas", format_int(total_precisas))
    with c2:
        st.metric("Empresas encontradas", format_int(total_encontradas))
    with c3:
        st.metric("Faltantes", format_int(max(total_precisas - total_encontradas, 0)))
    with c4:
        st.metric("Contatos totais", format_int(total_contatos))

    c5, c6 = st.columns([1, 1])
    with c5:
        donut_chart(senioridades, "senioridade", "qtd", "Contatos por senioridade", height=430)
    with c6:
        if departamentos.empty:
            st.info("Sem departamentos para exibir.")
        else:
            dept_count = departamentos.value_counts("departamento").reset_index(name="qtd")
            bar_chart(dept_count, "qtd", "departamento", "Departamentos identificados", orientation="h", height=430)

    c7, c8 = st.columns([1, 1])
    with c7:
        section("Empresas que precisamos")
        searchable_table(empresas_precisas, "empresa", "Buscar nas empresas desejadas", height=380)
    with c8:
        section("Empresas ainda faltantes")
        if faltantes.empty:
            st.success("Todas as empresas desejadas aparecem como encontradas. Bonito de ver.")
        else:
            searchable_table(faltantes, "empresa", "Buscar nas faltantes", height=380)

    section("Cargos encontrados", "Lista de cargos únicos para apoiar segmentação e abordagem.")
    searchable_table(cargos, "cargo", "Buscar cargo", height=420)

with tab_envios:
    section("Envios e respostas", "Exibe volume enviado por dia, acumulado, evolução e leitura dos estados de resposta.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Emails enviados", format_int(total_enviados))
    with c2:
        st.metric("Dias de envio", format_int(len(envios)))
    with c3:
        st.metric("Estados de resposta", format_int(len(respostas)))
    with c4:
        st.metric("Taxa com status útil", format_pct(taxa_status))

    if not envios.empty:
        c5, c6 = st.columns([1.15, .85])
        with c5:
            fig = px.bar(envios, x="data_label", y="qtd_enviados", text="qtd_enviados", title="Emails enviados por dia")
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(height=430, margin=dict(l=10, r=20, t=55, b=20), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
        with c6:
            fig = px.line(envios, x="data_label", y="acumulado", markers=True, title="Acumulado de envios")
            fig.update_traces(texttemplate="%{y}", textposition="top center")
            fig.update_layout(height=430, margin=dict(l=10, r=20, t=55, b=20), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

        envios_view = envios[["data_label", "qtd_enviados", "acumulado", "variacao_abs", "variacao_pct"]].copy()
        envios_view["variacao_pct"] = envios_view["variacao_pct"].map(format_pct)
        envios_view = envios_view.rename(
            columns={
                "data_label": "Dia",
                "qtd_enviados": "Enviados",
                "acumulado": "Acumulado",
                "variacao_abs": "Variação absoluta",
                "variacao_pct": "Variação percentual",
            }
        )
        st.dataframe(envios_view, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de envio para exibir.")

    c7, c8 = st.columns([1, 1])
    with c7:
        donut_chart(view_respostas, "estado_resposta", "qtd", "Estados de resposta", height=430)
    with c8:
        bar_chart(view_respostas, "qtd", "estado_resposta", "Quantidade por estado", orientation="h", height=430)

with tab_explorar:
    section("Explorar dados", "Tabelas separadas por bloco. Isso ajuda muito quando alguém pergunta: de onde saiu esse número?")
    bloco = st.selectbox(
        "Escolha o bloco",
        [
            "Empresas",
            "Eventos",
            "Setores detalhados",
            "Setores hard",
            "Tipos de evento",
            "Nichos",
            "Empresas desejadas",
            "Empresas encontradas",
            "Empresas faltantes",
            "Cargos",
            "Senioridades",
            "Departamentos",
            "Envios",
            "Respostas",
        ],
    )
    tables = {
        "Empresas": empresas,
        "Eventos": eventos,
        "Setores detalhados": setores,
        "Setores hard": setores_hard,
        "Tipos de evento": tipos_evento,
        "Nichos": nichos,
        "Empresas desejadas": empresas_precisas,
        "Empresas encontradas": empresas_encontradas,
        "Empresas faltantes": faltantes,
        "Cargos": cargos,
        "Senioridades": senioridades,
        "Departamentos": departamentos,
        "Envios": envios,
        "Respostas": respostas,
    }
    selected_df = tables[bloco]
    st.dataframe(selected_df, use_container_width=True, hide_index=True, height=520)
    st.download_button(
        "Baixar este bloco em CSV",
        data=selected_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{bloco.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("Ver arquivo bruto"):
        st.dataframe(data["raw"], use_container_width=True, height=420)

st.caption(
    "Leitura baseada nos blocos do CSV: Prospect Eventos, Eventos, Contatos e Dados. Para análises cruzadas profundas, o ideal é ter depois uma base normalizada empresa x evento x contato x envio."
)
