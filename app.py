from __future__ import annotations

import io
import os
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
    initial_sidebar_state="collapsed",
)

ARQUIVOS_PADRAO = [
    "dashboard_prospeccao_base.csv",
    "Lista de Prospects - Dados - Dash.csv",
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
    "setor_consolidado_da_empresa",
    "empresas_no_setor_consolidado",
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
    "setor_consolidado_da_empresa": "Setor consolidado",
    "empresas_no_setor_consolidado": "Empresas no setor consolidado",
    "tipo_publico_do_evento": "Tipo do evento",
    "eventos_por_tipo_publico": "Eventos por tipo",
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
    "setor_empresa_consolidado": "setor_consolidado_da_empresa",
    "quantidade_empresas_no_setor_consolidado": "empresas_no_setor_consolidado",
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

PALETAS = {
    "escuro": {
        "bg": "#070B14",
        "bg2": "#0F172A",
        "panel": "#111827",
        "panel_soft": "#172033",
        "line": "#2F3A4D",
        "text": "#F8FAFC",
        "muted": "#CBD5E1",
        "muted2": "#94A3B8",
        "accent": "#F97316",
        "badge_bg": "#3B2416",
        "badge_text": "#FED7AA",
        "hero_a": "rgba(17,24,39,.98)",
        "hero_b": "rgba(30,41,59,.96)",
        "hero_c": "rgba(67,37,22,.92)",
        "shadow": "rgba(0,0,0,.30)",
        "tab_active_bg": "#F97316",
        "tab_active_text": "#111827",
        "plot_template": "plotly_dark",
        "grid": "#273244",
        "hover_bg": "#F8FAFC",
        "hover_text": "#111827",
    },
    "claro": {
        "bg": "#F4F7FB",
        "bg2": "#EEF3F8",
        "panel": "#FFFFFF",
        "panel_soft": "#F8FAFC",
        "line": "#D8E0EA",
        "text": "#111827",
        "muted": "#475569",
        "muted2": "#64748B",
        "accent": "#F97316",
        "badge_bg": "#FFF7ED",
        "badge_text": "#9A3412",
        "hero_a": "rgba(255,255,255,.98)",
        "hero_b": "rgba(239,246,255,.96)",
        "hero_c": "rgba(255,247,237,.96)",
        "shadow": "rgba(15,23,42,.08)",
        "tab_active_bg": "#111827",
        "tab_active_text": "#FFFFFF",
        "plot_template": "plotly_white",
        "grid": "#E5E7EB",
        "hover_bg": "#111827",
        "hover_text": "#FFFFFF",
    },
}

st.session_state.setdefault("modo_escuro", True)
CORES_TEMA = PALETAS["escuro" if st.session_state["modo_escuro"] else "claro"]
ESCALA_GRAFICO = ["#2563EB", "#14B8A6", "#F97316"]
CORES_DONUT = ["#2563EB", "#14B8A6", "#F97316", "#DC2626", "#7C3AED", "#64748B", "#0F766E"]

CSS = f"""
<style>
:root {{
    --bg: {CORES_TEMA["bg"]};
    --bg2: {CORES_TEMA["bg2"]};
    --panel: {CORES_TEMA["panel"]};
    --panel-soft: {CORES_TEMA["panel_soft"]};
    --line: {CORES_TEMA["line"]};
    --text: {CORES_TEMA["text"]};
    --muted: {CORES_TEMA["muted"]};
    --muted2: {CORES_TEMA["muted2"]};
    --accent: {CORES_TEMA["accent"]};
    --badge-bg: {CORES_TEMA["badge_bg"]};
    --badge-text: {CORES_TEMA["badge_text"]};
    --hero-a: {CORES_TEMA["hero_a"]};
    --hero-b: {CORES_TEMA["hero_b"]};
    --hero-c: {CORES_TEMA["hero_c"]};
    --shadow: {CORES_TEMA["shadow"]};
    --tab-active-bg: {CORES_TEMA["tab_active_bg"]};
    --tab-active-text: {CORES_TEMA["tab_active_text"]};
}}

html, body, [class*="css"] {{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 16px;
}}

.stApp {{
    background: linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
    color: var(--text);
}}

[data-testid="stSidebar"], [data-testid="collapsedControl"] {{
    display: none;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    max-width: 1720px;
}}

.hero {{
    padding: 30px 34px;
    border-radius: 18px;
    background: linear-gradient(135deg, var(--hero-a), var(--hero-b) 52%, var(--hero-c));
    border: 1px solid var(--line);
    box-shadow: 0 18px 48px var(--shadow);
    margin-bottom: 20px;
}}

.hero h1 {{
    font-size: clamp(2.2rem, 3vw, 3.2rem);
    line-height: 1.03;
    margin: 4px 0 10px 0;
    font-weight: 900;
    color: var(--text);
    letter-spacing: 0;
}}

.hero p {{
    font-size: 1.08rem;
    line-height: 1.65;
    color: var(--muted);
    margin: 0;
    max-width: 1180px;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    background: var(--badge-bg);
    color: var(--badge-text);
    border: 1px solid var(--accent);
    font-size: .78rem;
    font-weight: 850;
    margin: 0 8px 10px 0;
    letter-spacing: .04em;
}}

.kpi-card, [data-testid="stMetric"] {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    box-shadow: 0 12px 32px var(--shadow);
}}

.kpi-card {{
    padding: 20px 20px 18px 20px;
    min-height: 148px;
}}

.kpi-label {{
    font-size: .8rem;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: var(--muted);
    font-weight: 850;
}}

.kpi-value {{
    font-size: clamp(2.15rem, 2.2vw, 2.75rem);
    margin-top: 10px;
    color: var(--text);
    font-weight: 900;
    letter-spacing: 0;
}}

.kpi-help {{
    font-size: .95rem;
    line-height: 1.45;
    color: var(--muted2);
    margin-top: 8px;
}}

.section-title {{
    font-size: 1.45rem;
    line-height: 1.25;
    font-weight: 900;
    color: var(--text);
    margin: 24px 0 4px 0;
    letter-spacing: 0;
}}

.section-subtitle {{
    font-size: 1rem;
    color: var(--muted2);
    margin-bottom: 16px;
}}

[data-testid="stMetric"] {{
    padding: 16px 18px;
}}

[data-testid="stMetricLabel"] {{
    color: var(--muted);
    font-size: .94rem;
}}

[data-testid="stMetricValue"] {{
    color: var(--text);
    font-weight: 900;
    font-size: 2.05rem;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 8px;
}}

.stTabs [data-baseweb="tab"] {{
    height: 48px;
    padding: 0 18px;
    border-radius: 10px;
    background: var(--panel);
    border: 1px solid var(--line);
    font-weight: 800;
    color: var(--text);
}}

.stTabs [aria-selected="true"] {{
    background: var(--tab-active-bg);
    border-color: var(--tab-active-bg);
    color: var(--tab-active-text);
}}

[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--line);
}}

[data-testid="stDataFrame"] div {{
    font-size: 14px;
}}

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {{
    border-radius: 10px;
}}

[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p {{
    color: var(--text) !important;
    font-weight: 800;
}}

button[kind="secondary"], .stDownloadButton button {{
    border-radius: 10px;
    font-weight: 800;
}}

.small-note {{
    font-size: .9rem;
    color: var(--muted2);
}}

hr {{
    border-color: var(--line);
}}

@media (max-width: 900px) {{
    .block-container {{padding-left: 1rem; padding-right: 1rem;}}
    .hero {{padding: 22px;}}
    .kpi-card {{min-height: 132px;}}
}}
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
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    def normalizar_numero(valor: object) -> str:
        texto = limpar_texto(valor)
        texto = texto.replace("R$", "").replace("%", "").strip()
        texto = re.sub(r"[^0-9,.\-]", "", texto)
        if "," in texto:
            return texto.replace(".", "").replace(",", ".")
        if "." in texto:
            partes = texto.split(".")
            tem_milhar = len(partes) > 1 and len(partes[0]) <= 3 and all(len(parte) == 3 for parte in partes[1:])
            return "".join(partes) if tem_milhar else texto
        return texto

    return pd.to_numeric(serie.map(normalizar_numero), errors="coerce").fillna(0)


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


def localizar_url_padrao() -> str | None:
    candidatos = [
        os.getenv("DASHBOARD_CSV_URL"),
        os.getenv("DATA_URL"),
    ]
    try:
        candidatos.extend([
            st.secrets.get("DASHBOARD_CSV_URL"),
            st.secrets.get("DATA_URL"),
        ])
    except Exception:
        pass

    for candidato in candidatos:
        url = limpar_texto(candidato)
        if url.startswith(("https://", "http://")):
            return url
    return None


def garantir_colunas_oficiais(df: pd.DataFrame) -> pd.DataFrame:
    saida = df.copy()
    for coluna in COLUNAS_OFICIAIS:
        if coluna not in saida.columns:
            saida[coluna] = ""
    return saida[COLUNAS_OFICIAIS]


def coluna_texto(df: pd.DataFrame, *candidatas: str) -> pd.Series:
    for coluna in candidatas:
        if coluna in df.columns:
            return df[coluna].map(limpar_texto)
    return pd.Series([""] * len(df), index=df.index)


def nova_base_vazia(indice: pd.Index) -> pd.DataFrame:
    return pd.DataFrame({coluna: "" for coluna in COLUNAS_OFICIAIS}, index=indice)


def bloco_normalizado(df: pd.DataFrame, nome_bloco: str) -> pd.DataFrame:
    if "bloco" not in df.columns:
        return df.iloc[0:0].copy()
    chave = normalizar_chave(nome_bloco)
    return df[df["bloco"].map(normalizar_chave).eq(chave)].copy()


def converter_csv_normalizado(df: pd.DataFrame) -> pd.DataFrame:
    partes: list[pd.DataFrame] = []

    def adicionar_bloco(nome_bloco: str, mapeamento: dict[str, tuple[str, ...] | str]) -> None:
        origem = bloco_normalizado(df, nome_bloco)
        if origem.empty:
            return
        destino = nova_base_vazia(origem.index)
        for coluna_destino, candidatas in mapeamento.items():
            if isinstance(candidatas, str):
                candidatas = (candidatas,)
            destino[coluna_destino] = coluna_texto(origem, *candidatas)
        partes.append(destino)

    adicionar_bloco(
        "prospect_eventos",
        {
            "empresa_mapeada": "empresa",
            "evento_mapeado_por_empresa": "evento",
            "ano_evento_mapeado": "ano",
        },
    )
    adicionar_bloco("resumo_empresas_mapeadas", {"empresa_mapeada": ("empresa", "categoria")})
    adicionar_bloco("resumo_eventos_mapeados", {"evento_mapeado_por_empresa": ("evento", "categoria")})
    adicionar_bloco("resumo_anos_eventos", {"ano_evento_mapeado": ("ano", "categoria")})
    adicionar_bloco(
        "resumo_setores_detalhados",
        {
            "setor_deduplicado_detalhado_da_empresa": ("setor", "categoria"),
            "empresas_no_setor_deduplicado_detalhado": "quantidade",
        },
    )
    adicionar_bloco(
        "resumo_setores_consolidados",
        {
            "setor_consolidado_da_empresa": ("setor_consolidado", "categoria"),
            "empresas_no_setor_consolidado": "quantidade",
        },
    )
    adicionar_bloco(
        "resumo_tipos_evento",
        {
            "tipo_publico_do_evento": ("tipo_evento", "categoria"),
            "eventos_por_tipo_publico": "quantidade",
        },
    )
    adicionar_bloco(
        "resumo_segmentos_evento",
        {
            "nicho_segmento_do_evento": ("segmento_nicho", "categoria"),
            "eventos_por_nicho_segmento": "quantidade",
        },
    )
    adicionar_bloco("resumo_empresas_priorizadas", {"empresa_priorizada_para_busca_de_contatos": ("empresa_priorizada", "categoria")})
    adicionar_bloco("resumo_empresas_com_contato", {"empresa_com_contato_encontrado": ("empresa_com_contato", "categoria")})
    adicionar_bloco("resumo_cargos", {"cargo_do_contato_encontrado": ("cargo", "categoria")})
    adicionar_bloco(
        "resumo_senioridades",
        {
            "senioridade_do_contato_encontrado": ("senioridade", "categoria"),
            "contatos_por_senioridade": "quantidade",
        },
    )
    adicionar_bloco("resumo_departamentos", {"departamento_do_contato_encontrado": ("departamento", "categoria")})
    adicionar_bloco(
        "resumo_envios_por_dia",
        {
            "data_calendario_envio_email": ("data_envio", "categoria"),
            "dia_mes_envio_email": ("data_envio", "categoria"),
            "emails_enviados_no_dia": "quantidade",
        },
    )
    adicionar_bloco(
        "resumo_status_resposta",
        {
            "status_da_resposta_do_email": ("estado_resposta", "categoria"),
            "respostas_por_status": "quantidade",
        },
    )

    totais = bloco_normalizado(df, "resumo_totais")
    if not totais.empty:
        destino = nova_base_vazia(totais.index)
        for indice, linha in totais.iterrows():
            metrica = normalizar_chave(linha.get("metrica"))
            valor = limpar_texto(linha.get("valor")) or limpar_texto(linha.get("quantidade"))
            if metrica == "total de empresas priorizadas":
                destino.loc[indice, "empresas_priorizadas_para_contato_total"] = valor
            elif metrica == "total de empresas com contato":
                destino.loc[indice, "empresas_com_contato_encontrado_total"] = valor
            elif metrica == "total de contatos encontrados":
                destino.loc[indice, "contatos_encontrados_total"] = valor
        partes.append(destino)

    if not partes:
        raise ValueError("O CSV normalizado não tem blocos reconhecíveis para montar o dashboard.")

    return garantir_colunas_oficiais(pd.concat(partes, ignore_index=True))


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
        "setor_consolidado_da_empresa": col(5),
        "empresas_no_setor_consolidado": col(6),
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
        tem_base_normalizada = {"bloco", "metrica", "categoria"}.issubset(df.columns) and {"empresa", "evento"}.intersection(df.columns)
        if tem_base_normalizada:
            return converter_csv_normalizado(df)
    except Exception:
        pass

    return converter_csv_antigo_com_blocos(file_bytes=file_bytes, caminho=caminho)


def preparar_envios(df: pd.DataFrame, ano_padrao: int) -> pd.DataFrame:
    envios = tabela_contagem_por_coluna(df, "data_calendario_envio_email", "emails_enviados_no_dia", "data_envio_email", "emails_enviados")
    if envios.empty:
        return envios

    texto_data = envios["data_envio_email"].astype(str).str.strip()
    data_iso = pd.to_datetime(texto_data, errors="coerce", format="mixed", dayfirst=True)
    data_dia_mes = pd.to_datetime(texto_data + f"/{ano_padrao}", format="%d/%m/%Y", errors="coerce")
    envios["data_envio"] = data_iso.fillna(data_dia_mes)
    envios = envios.dropna(subset=["data_envio"]).sort_values("data_envio")
    envios["dia_mes"] = envios["data_envio"].dt.strftime("%d/%m")
    valores = envios["emails_enviados"].astype(int)
    usa_acumulado = len(valores) > 1 and valores.is_monotonic_increasing
    if usa_acumulado:
        envios["emails_acumulados"] = valores
        envios["emails_enviados"] = valores.diff().fillna(valores.iloc[0]).clip(lower=0).astype(int)
    else:
        envios["emails_enviados"] = valores
        envios["emails_acumulados"] = valores.cumsum()
    envios["crescimento_absoluto"] = envios["emails_acumulados"].diff().fillna(0).astype(int)
    envios["crescimento_percentual"] = envios["emails_acumulados"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    return envios.reset_index(drop=True)


def inferir_ano_padrao(df: pd.DataFrame) -> int:
    anos_eventos = para_numero(df["ano_evento_mapeado"]) if "ano_evento_mapeado" in df.columns else pd.Series(dtype="float64")
    anos_eventos = anos_eventos[(anos_eventos >= 2020) & (anos_eventos <= 2035)]
    if not anos_eventos.empty:
        return int(anos_eventos.max())
    return datetime.today().year


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


def altura_por_linhas(qtd_linhas: int, minimo: int = 420, por_linha: int = 36, extra: int = 150, maximo: int = 820) -> int:
    return min(max(minimo, extra + qtd_linhas * por_linha), maximo)


def preparar_figura(fig: go.Figure, altura: int) -> go.Figure:
    fig.update_layout(
        template=CORES_TEMA["plot_template"],
        height=altura,
        paper_bgcolor=CORES_TEMA["panel"],
        plot_bgcolor=CORES_TEMA["panel"],
        margin=dict(l=28, r=46, t=72, b=44),
        font=dict(family="Inter, Segoe UI, sans-serif", color=CORES_TEMA["text"], size=15),
        title=dict(font=dict(size=22, color=CORES_TEMA["text"]), x=0, y=.98),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            font=dict(size=14, color=CORES_TEMA["muted"]),
        ),
        hoverlabel=dict(bgcolor=CORES_TEMA["hover_bg"], font=dict(color=CORES_TEMA["hover_text"], size=14)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=CORES_TEMA["grid"], zeroline=False, tickfont=dict(size=14), automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor=CORES_TEMA["grid"], zeroline=False, tickfont=dict(size=14), automargin=True)
    return fig


def grafico_barras(df: pd.DataFrame, categoria: str, quantidade: str, titulo: str, key: str, horizontal: bool = True, top_n: int | None = None, altura: int | None = None) -> None:
    if df.empty:
        st.info("Sem dados para exibir neste bloco.")
        return

    base = df.copy().head(top_n) if top_n else df.copy()
    altura_final = altura or altura_por_linhas(len(base), minimo=430)
    escala = ESCALA_GRAFICO
    if horizontal:
        base = base.sort_values(quantidade, ascending=True)
        fig = px.bar(base, x=quantidade, y=categoria, orientation="h", text=quantidade, title=titulo, color=quantidade, color_continuous_scale=escala)
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title=None)
        maior_valor = base[quantidade].max() if not base.empty else 0
        if maior_valor:
            fig.update_xaxes(range=[0, maior_valor * 1.18])
    else:
        fig = px.bar(base, x=categoria, y=quantidade, text=quantidade, title=titulo, color=quantidade, color_continuous_scale=escala)
        fig.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
        fig.update_xaxes(tickangle=-25)

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        textfont=dict(size=14, color=CORES_TEMA["text"]),
        marker_line_width=0,
        cliponaxis=False,
        hovertemplate=f"{categoria}: %{{y}}<br>{quantidade}: %{{x:,.0f}}<extra></extra>" if horizontal else f"{categoria}: %{{x}}<br>{quantidade}: %{{y:,.0f}}<extra></extra>",
    )
    st.plotly_chart(preparar_figura(fig, altura_final), width="stretch", key=key)


def grafico_donut(df: pd.DataFrame, categoria: str, quantidade: str, titulo: str, key: str, altura: int = 390) -> None:
    if df.empty:
        st.info("Sem dados para exibir neste bloco.")
        return

    total = int(df[quantidade].sum()) if quantidade in df.columns else 0
    fig = px.pie(df, names=categoria, values=quantidade, hole=.58, title=titulo, color_discrete_sequence=CORES_DONUT)
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(size=16, color="#FFFFFF"),
        marker=dict(line=dict(color=CORES_TEMA["panel"], width=2)),
        hovertemplate=f"{categoria}: %{{label}}<br>{quantidade}: %{{value:,.0f}}<br>Participação: %{{percent}}<extra></extra>",
    )
    fig.add_annotation(
        text=f"<b>{formato_inteiro(total)}</b><br><span style='font-size:13px;color:{CORES_TEMA['muted2']}'>total</span>",
        x=.5,
        y=.5,
        showarrow=False,
        font=dict(size=22, color=CORES_TEMA["text"]),
    )
    fig = preparar_figura(fig, altura)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-.06, xanchor="center", x=.5, font=dict(size=14, color=CORES_TEMA["muted"])))
    st.plotly_chart(fig, width="stretch", key=key)


def tabela_com_busca(df: pd.DataFrame, coluna_busca: str, label: str, key: str, altura: int = 420) -> None:
    if df.empty:
        st.info("Sem dados nesta tabela.")
        return

    termo = st.text_input(label, placeholder="Digite para filtrar", key=f"busca_{key}")
    visual = df.copy()
    if termo and coluna_busca in visual.columns:
        visual = visual[visual[coluna_busca].astype(str).str.contains(termo, case=False, na=False)]

    st.dataframe(visual, width="stretch", hide_index=True, height=altura)
    st.download_button(
        "Baixar tabela filtrada em CSV",
        data=visual.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        width="stretch",
        key=f"download_{key}",
    )


def renomear_para_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: ROTULOS.get(c, c) for c in df.columns})


caminho_padrao = localizar_arquivo_padrao()
url_padrao = localizar_url_padrao()
caminho_csv = caminho_padrao or url_padrao
fonte_base = caminho_padrao or "URL configurada"

if not caminho_csv:
    st.error("Não encontrei `dashboard_prospeccao_base.csv`. Coloque o CSV da aba Dados - Dash na raiz do projeto ou configure `DASHBOARD_CSV_URL`.")
    st.stop()

try:
    base = carregar_base(None, caminho_csv)
except Exception as erro:
    st.error(f"Não consegui montar o dashboard com esse arquivo. Erro: {erro}")
    st.stop()

empresas_mapeadas = tabela_lista(base, "empresa_mapeada", "Empresa mapeada")
eventos_mapeados = tabela_lista(base, "evento_mapeado_por_empresa", "Evento mapeado")
empresas_eventos = base[["empresa_mapeada", "evento_mapeado_por_empresa", "ano_evento_mapeado"]].copy()
empresas_eventos = empresas_eventos.apply(lambda coluna: coluna.map(limpar_texto))
empresas_eventos = empresas_eventos[(empresas_eventos["empresa_mapeada"] != "") | (empresas_eventos["evento_mapeado_por_empresa"] != "")]
empresas_eventos = empresas_eventos.drop_duplicates().rename(columns=ROTULOS).reset_index(drop=True)

setores_detalhados = tabela_contagem_por_coluna(base, "setor_deduplicado_detalhado_da_empresa", "empresas_no_setor_deduplicado_detalhado", "Setor deduplicado detalhado", "Empresas mapeadas")
setores_consolidados = tabela_contagem_por_coluna(base, "setor_consolidado_da_empresa", "empresas_no_setor_consolidado", "Setor consolidado", "Empresas mapeadas")
tipos_evento = tabela_contagem_por_coluna(base, "tipo_publico_do_evento", "eventos_por_tipo_publico", "Tipo do evento", "Eventos mapeados")
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
ano_padrao = inferir_ano_padrao(base)
envios = preparar_envios(base, int(ano_padrao))
respostas = tabela_contagem_por_coluna(base, "status_da_resposta_do_email", "respostas_por_status", "Status da resposta do email", "Respostas mapeadas")

total_empresas = contar_unicos(base, "empresa_mapeada")
total_eventos = contar_unicos(base, "evento_mapeado_por_empresa")
total_setores_detalhados = len(setores_detalhados)
total_setores_consolidados = len(setores_consolidados)
total_priorizadas = max(primeiro_numero(base, "empresas_priorizadas_para_contato_total", len(empresas_priorizadas)), len(empresas_priorizadas))
total_com_contato = max(primeiro_numero(base, "empresas_com_contato_encontrado_total", len(empresas_com_contato)), len(empresas_com_contato))
total_contatos = max(primeiro_numero(base, "contatos_encontrados_total", int(cargos_contatos["Contatos mapeados"].sum()) if not cargos_contatos.empty else 0), int(cargos_contatos["Contatos mapeados"].sum()) if not cargos_contatos.empty else 0)
total_enviados = int(envios["emails_acumulados"].max()) if not envios.empty else 0
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

_, tema_coluna = st.columns([.82, .18])
with tema_coluna:
    st.toggle("Modo escuro", key="modo_escuro")

linha1 = st.columns(4)
with linha1[0]:
    kpi_card("Empresas mapeadas", formato_inteiro(total_empresas), "Empresas únicas identificadas na base")
with linha1[1]:
    kpi_card("Eventos mapeados", formato_inteiro(total_eventos), "Eventos únicos relacionados às empresas")
with linha1[2]:
    kpi_card("Setores", formato_inteiro(total_setores_consolidados), f"{formato_inteiro(total_setores_detalhados)} setores detalhados")
with linha1[3]:
    kpi_card("Cobertura de contatos", formato_percentual(taxa_cobertura), f"{formato_inteiro(total_com_contato)} de {formato_inteiro(total_priorizadas)} empresas")

linha2 = st.columns(4)
with linha2[0]:
    kpi_card("Contatos encontrados", formato_inteiro(total_contatos), "Volume total de contatos mapeados")
with linha2[1]:
    kpi_card("Cargos únicos", formato_inteiro(len(cargos_contatos)), "Cargos diferentes encontrados")
with linha2[2]:
    kpi_card("Emails enviados", formato_inteiro(total_enviados), "Total acumulado informado no Dados - Dash")
with linha2[3]:
    kpi_card("Respostas úteis", formato_inteiro(respostas_com_status_util), f"Taxa sobre envios: {formato_percentual(taxa_resposta_util)}")

with st.expander("Ajustes de visualização", expanded=False):
    ajuste1, ajuste2 = st.columns([1, 1])
    with ajuste1:
        top_n_rankings = st.slider("Itens exibidos nos rankings", min_value=8, max_value=40, value=16, step=1)
    with ajuste2:
        tamanho_graficos = st.select_slider("Tamanho dos gráficos", options=["Compacto", "Confortável", "Amplo"], value="Confortável")

    filtro1, filtro2, filtro3 = st.columns(3)
    with filtro1:
        filtro_setores = st.multiselect("Setor consolidado", options=setores_consolidados["Setor consolidado"].tolist(), default=[])
    with filtro2:
        filtro_tipos_evento = st.multiselect("Tipo do evento", options=tipos_evento["Tipo do evento"].tolist(), default=[])
    with filtro3:
        filtro_respostas = st.multiselect("Status da resposta do email", options=respostas["Status da resposta do email"].tolist(), default=[])

multiplicador_altura = {"Compacto": .88, "Confortável": 1.0, "Amplo": 1.18}[tamanho_graficos]


def altura(valor: int) -> int:
    return int(valor * multiplicador_altura)


def altura_ranking(df: pd.DataFrame, minimo: int = 430, por_linha: int = 38, extra: int = 150, maximo: int = 860) -> int:
    return altura(altura_por_linhas(min(top_n_rankings, len(df)), minimo=minimo, por_linha=por_linha, extra=extra, maximo=maximo))


visao_setores_consolidados = setores_consolidados if not filtro_setores else setores_consolidados[setores_consolidados["Setor consolidado"].isin(filtro_setores)]
visao_tipos_evento = tipos_evento if not filtro_tipos_evento else tipos_evento[tipos_evento["Tipo do evento"].isin(filtro_tipos_evento)]
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
                ["Setores consolidados", total_setores_consolidados],
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
        st.dataframe(resumo, width="stretch", hide_index=True, height=altura(450))

    with direita:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=taxa_cobertura * 100,
                number={"suffix": "%", "valueformat": ".1f", "font": {"color": CORES_TEMA["text"], "size": 54}},
                title={"text": "Cobertura de empresas com contatos", "font": {"color": CORES_TEMA["muted"], "size": 18}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": CORES_TEMA["muted2"]},
                    "bar": {"color": CORES_TEMA["accent"], "thickness": 0.26},
                    "bgcolor": CORES_TEMA["panel_soft"],
                    "borderwidth": 1,
                    "bordercolor": CORES_TEMA["line"],
                    "steps": [
                        {"range": [0, 50], "color": "rgba(239,68,68,.24)"},
                        {"range": [50, 80], "color": "rgba(245,158,11,.22)"},
                        {"range": [80, 100], "color": "rgba(34,197,94,.22)"},
                    ],
                },
            )
        )
        st.plotly_chart(preparar_figura(fig, altura(460)), width="stretch", key="gauge_cobertura")

    c1, c2 = st.columns(2)
    with c1:
        grafico_donut(visao_tipos_evento, "Tipo do evento", "Eventos mapeados", "Distribuição por tipo do evento", "donut_tipo_publico", altura=altura(470))
    with c2:
        grafico_donut(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Distribuição dos status de resposta", "donut_respostas", altura=altura(470))

with aba_empresas:
    secao("Empresas e setores", "Use o setor consolidado para leitura executiva. Use o setor detalhado para investigação fina.")
    c1, c2 = st.columns([1.05, .95])
    with c1:
        grafico_barras(visao_setores_consolidados, "Setor consolidado", "Empresas mapeadas", "Empresas por setor consolidado", "bar_setor_consolidado", top_n=top_n_rankings, altura=altura_ranking(visao_setores_consolidados, minimo=520))
    with c2:
        if setores_consolidados.empty:
            st.info("Sem setores para exibir.")
        else:
            fig = px.treemap(setores_consolidados, path=["Setor consolidado"], values="Empresas mapeadas", title="Concentração visual por setor consolidado", color="Empresas mapeadas", color_continuous_scale="Sunsetdark")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(preparar_figura(fig, altura(560)), width="stretch", key="treemap_setor_consolidado")

    c3, c4 = st.columns([1.05, .95])
    with c3:
        grafico_barras(setores_detalhados, "Setor deduplicado detalhado", "Empresas mapeadas", "Top setores detalhados", "bar_setor_detalhado", top_n=top_n_rankings, altura=altura_ranking(setores_detalhados, minimo=560, maximo=920))
    with c4:
        secao("Empresas mapeadas", "Lista pesquisável das empresas identificadas.")
        tabela_com_busca(empresas_mapeadas, "Empresa mapeada", "Buscar empresa mapeada", "empresas_mapeadas", altura=altura(540))

with aba_eventos:
    secao("Eventos", "Leitura dos eventos mapeados, tipos de público e nichos comerciais.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Eventos únicos", formato_inteiro(total_eventos))
    m2.metric("Tipos de público", formato_inteiro(len(tipos_evento)))
    m3.metric("Nichos ou segmentos", formato_inteiro(len(nichos_evento)))

    c1, c2 = st.columns([.85, 1.15])
    with c1:
        grafico_donut(visao_tipos_evento, "Tipo do evento", "Eventos mapeados", "Eventos por tipo", "eventos_tipo_publico", altura=altura(480))
    with c2:
        grafico_barras(nichos_evento, "Nicho ou segmento do evento", "Eventos mapeados", "Nichos e segmentos com mais eventos", "bar_nichos", top_n=top_n_rankings, altura=altura_ranking(nichos_evento))

    secao("Relação empresa x evento", "Tabela útil para investigar quais empresas aparecem relacionadas a quais eventos.")
    tabela_com_busca(empresas_eventos, "Empresa mapeada", "Buscar por empresa", "empresa_evento", altura=altura(520))

with aba_contatos:
    secao("Contatos", "Mostra cobertura das empresas priorizadas, contatos encontrados, senioridade, cargos e departamentos.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Empresas priorizadas", formato_inteiro(total_priorizadas))
    m2.metric("Empresas com contato", formato_inteiro(total_com_contato))
    m3.metric("Empresas faltantes", formato_inteiro(max(total_priorizadas - total_com_contato, 0)))
    m4.metric("Contatos encontrados", formato_inteiro(total_contatos))

    c1, c2 = st.columns([.9, 1.1])
    with c1:
        grafico_donut(senioridades, "Senioridade do contato encontrado", "Contatos mapeados", "Contatos por senioridade", "donut_senioridade", altura=altura(500))
    with c2:
        grafico_barras(cargos_contatos, "Cargo do contato encontrado", "Contatos mapeados", "Cargos com maior recorrência", "bar_cargos", top_n=top_n_rankings, altura=altura_ranking(cargos_contatos))

    c3, c4 = st.columns([1, 1])
    with c3:
        grafico_barras(departamentos, "Departamento do contato encontrado", "Contatos mapeados", "Departamentos mapeados", "bar_departamentos", top_n=top_n_rankings, altura=altura_ranking(departamentos, minimo=430))
    with c4:
        grafico_barras(empresas_sem_contato.assign(**{"Empresas faltantes": 1}), "Empresa priorizada para busca de contatos", "Empresas faltantes", "Empresas priorizadas ainda sem contato", "bar_empresas_faltantes", top_n=top_n_rankings, altura=altura_ranking(empresas_sem_contato, minimo=430))

    c5, c6 = st.columns([1, 1])
    with c5:
        secao("Empresas priorizadas para busca")
        tabela_com_busca(empresas_priorizadas, "Empresa priorizada para busca de contatos", "Buscar empresa priorizada", "empresas_priorizadas", altura=altura(460))
    with c6:
        secao("Empresas com contato encontrado")
        tabela_com_busca(empresas_com_contato, "Empresa com contato encontrado", "Buscar empresa encontrada", "empresas_com_contato", altura=altura(460))

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
            fig = px.bar(envios, x="dia_mes", y="emails_enviados", text="emails_enviados", title="Novos envios registrados por data", color="emails_enviados", color_continuous_scale=ESCALA_GRAFICO)
            fig.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
            fig.update_traces(textposition="outside", textfont=dict(color=CORES_TEMA["text"]), cliponaxis=False)
            st.plotly_chart(preparar_figura(fig, altura(470)), width="stretch", key="bar_envios_dia")
        with c2:
            fig = px.line(envios, x="dia_mes", y="emails_acumulados", markers=True, title="Acumulado de emails enviados")
            fig.update_traces(line=dict(width=4, color=CORES_TEMA["accent"]), marker=dict(size=9, color="#14B8A6"))
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            st.plotly_chart(preparar_figura(fig, altura(470)), width="stretch", key="linha_acumulado_envios")

        tabela_envios = envios[["data_envio", "emails_enviados", "emails_acumulados", "crescimento_absoluto", "crescimento_percentual"]].copy()
        tabela_envios["data_envio"] = tabela_envios["data_envio"].dt.strftime("%d/%m/%Y")
        tabela_envios["crescimento_percentual"] = tabela_envios["crescimento_percentual"].map(formato_percentual)
        tabela_envios = tabela_envios.rename(columns={
            "data_envio": "Data do envio",
            "emails_enviados": "Novos envios",
            "emails_acumulados": "Emails acumulados",
            "crescimento_absoluto": "Crescimento absoluto",
            "crescimento_percentual": "Crescimento percentual",
        })
        st.dataframe(tabela_envios, width="stretch", hide_index=True, height=altura(280))
    else:
        st.info("Sem dados de envio para exibir.")

    c3, c4 = st.columns([.9, 1.1])
    with c3:
        grafico_donut(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Status de resposta", "donut_status_envio", altura=altura(480))
    with c4:
        grafico_barras(visao_respostas, "Status da resposta do email", "Respostas mapeadas", "Quantidade por status de resposta", "bar_status_resposta", top_n=top_n_rankings, altura=altura_ranking(visao_respostas, minimo=460))

with aba_dados:
    secao("Base explorável", "Tabelas separadas por bloco para investigar a origem de cada número.")
    opcoes = {
        "Empresas mapeadas": empresas_mapeadas,
        "Relação empresa x evento": empresas_eventos,
        "Setores detalhados": setores_detalhados,
        "Setores consolidados": setores_consolidados,
        "Tipos de evento": tipos_evento,
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
    st.dataframe(tabela, width="stretch", hide_index=True, height=altura(590))
    st.download_button(
        "Baixar esta visão em CSV",
        data=tabela.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{normalizar_nome_coluna(bloco)}.csv",
        mime="text/csv",
        width="stretch",
        key="download_bloco_exploravel",
    )

st.caption(f"Dashboard montado automaticamente a partir de `{fonte_base}`. Os envios do Dados - Dash são tratados como série acumulada quando os valores aparecem em ordem crescente.")
