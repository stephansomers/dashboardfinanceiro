import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# =========================
# ESTILO
# =========================

st.markdown("""
<style>
div[role="radiogroup"] {
    gap: 25px;
}
div[role="radiogroup"] label {
    background-color: #1E222D;
    padding: 10px 24px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 17px;
}
div[role="radiogroup"] input:checked + div {
    background-color: #00C896;
    color: black;
    border-radius: 12px;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# =========================
# MAPAS
# =========================

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

ORDEM_MESES = list(range(1, 13))

# =========================
# HELPERS
# =========================

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def colorir_saldo(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return "color: #00E676; font-weight: bold;"
        elif val < 0:
            return "color: #FF5252; font-weight: bold;"
    return ""

# =========================
# UPLOADS
# =========================

st.sidebar.header("📂 Upload de Arquivos")

arquivo_financeiro = st.sidebar.file_uploader(
    "Upload Dados Financeiros (CSV)",
    type=["csv"],
    key="financeiro"
)

arquivo_patrimonio = st.sidebar.file_uploader(
    "Upload Patrimônio (CSV)",
    type=["csv"],
    key="patrimonio"
)

# =========================
# LOADERS
# =========================

@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding="utf-8-sig", sep=None, engine="python")
    except:
        df = pd.read_csv(file, encoding="latin-1", sep=None, engine="python")

    df.columns = df.columns.str.strip()

    df["Valor_num"] = (
        df["Valor"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["Valor_num"] = pd.to_numeric(df["Valor_num"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")

    df["tipo_mov"] = df["Tipo"].str.lower().apply(
        lambda x: "Receita" if "receita" in x else "Despesa"
    )

    df["ano"] = df["Data"].dt.year
    df["mes"] = df["Data"].dt.month
    df["mes_nome"] = df["mes"].map(MESES_PT)

    return df


@st.cache_data
def load_patrimonio(file):
    try:
        df_p = pd.read_csv(file, encoding="utf-8-sig", sep=None, engine="python")
    except:
        df_p = pd.read_csv(file, encoding="latin-1", sep=None, engine="python")

    df_p.columns = df_p.columns.str.strip()

    df_p["Valor_num"] = (
        df_p["Valor"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df_p["Valor_num"] = pd.to_numeric(df_p["Valor_num"], errors="coerce").fillna(0)
    df_p["Data"] = pd.to_datetime(df_p["Data"], dayfirst=True, errors="coerce")

    df_p["mes_ano"] = df_p["Data"].dt.to_period("M")

    return df_p

# =========================
# MENU
# =========================

menu = st.radio("", ["💰 Financeiro", "📈 Wealth Tracker"], horizontal=True)

# =========================
# FINANCEIRO
# =========================

if menu == "💰 Financeiro":

    if arquivo_financeiro is None:
        st.info("⬅️ Faça upload do arquivo financeiro para começar.")
        st.stop()

    df = load_data(arquivo_financeiro)

    st.title("💰 Dashboard Financeiro")

    hoje = datetime.today()
    ano_atual = hoje.year
    mes_atual = hoje.month

    anos = sorted(df["ano"].dropna().unique())
    ano_sel = st.selectbox("Ano", anos, index=len(anos)-1)

    meses_disp = sorted(df[df["ano"] == ano_sel]["mes"].dropna().unique())
    mes_nome_sel = st.selectbox("Mês", [MESES_PT[m] for m in meses_disp])
    mes_sel = [k for k, v in MESES_PT.items() if v == mes_nome_sel][0]

    filtered = df[(df["ano"] == ano_sel) & (df["mes"] == mes_sel)]

    receitas = filtered[filtered["tipo_mov"] == "Receita"]["Valor_num"].sum()
    despesas = filtered[filtered["tipo_mov"] == "Despesa"]["Valor_num"].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", formatar_real(receitas))
    c2.metric("Despesas", formatar_real(despesas))
    c3.metric("Saldo", formatar_real(saldo))

    trend = (
        df[df["ano"] == ano_sel]
        .groupby(["mes", "tipo_mov"])["Valor_num"]
        .sum()
        .unstack(fill_value=0)
    )

    trend["saldo"] = trend.get("Receita", 0) - trend.get("Despesa", 0)
    trend = trend.reindex(ORDEM_MESES, fill_value=0)
    trend["mes_label"] = trend.index.map(MESES_PT)

    fig_trend = px.line(trend, x="mes_label", y="saldo", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# =========================
# WEALTH TRACKER
# =========================

elif menu == "📈 Wealth Tracker":

    if arquivo_patrimonio is None:
        st.info("⬅️ Faça upload do arquivo de patrimônio para começar.")
        st.stop()

    df_p = load_patrimonio(arquivo_patrimonio)

    st.title("📈 Evolução do Patrimônio")

    pivot_pat = df_p.pivot_table(
        index="Instituicao",
        columns="mes_ano",
        values="Valor_num",
        aggfunc="sum",
        fill_value=0
    )

    pivot_pat = pivot_pat.sort_index(axis=1)

    pivot_pat.columns = [
        f"{MESES_PT[col.month]}/{col.year}"
        for col in pivot_pat.columns
    ]

    st.dataframe(pivot_pat, use_container_width=True)

    total_mensal = (
        df_p.groupby("mes_ano")["Valor_num"]
        .sum()
        .reset_index()
        .sort_values("mes_ano")
    )

    total_mensal["Data"] = total_mensal["mes_ano"].dt.to_timestamp()

    fig_total = px.line(
        total_mensal,
        x="Data",
        y="Valor_num",
        markers=True
    )

    fig_total.update_yaxes(
        tickprefix="R$ ",
        separatethousands=True
    )

    st.plotly_chart(fig_total, use_container_width=True)