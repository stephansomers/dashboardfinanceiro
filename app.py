import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.markdown("""
    <style>
    /* Radio horizontal estilo tab moderna */
div[role="radiogroup"] {
    gap: 25px;
}

/* Cada opção */
div[role="radiogroup"] label {
    background-color: #1E222D;
    padding: 10px 24px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 17px;
}

/* Selecionado */
div[role="radiogroup"] input:checked + div {
    background-color: #00C896;
    color: black;
    border-radius: 12px;
}

/* Remove label invisível */
div[role="radiogroup"] > label > div:first-child {
    display: none;
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
    try:
        if val > 0:
            return "color: #00E676; font-weight: bold;"
        elif val < 0:
            return "color: #FF5252; font-weight: bold;"
    except:
        pass
    return ""


# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("dados.csv", encoding="utf-8-sig", sep=None, engine="python")
    except:
        df = pd.read_csv("dados.csv", encoding="latin-1", sep=None, engine="python")

    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    # valor numérico real
    df["Valor_num"] = (
        df["Valor"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df["Valor_num"] = pd.to_numeric(df["Valor_num"], errors="coerce").fillna(0)

    # data
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")

    # tipo movimento
    df["tipo_mov"] = df["Tipo"].str.lower().apply(
        lambda x: "Receita" if "receita" in x else "Despesa"
    )

    df["ano"] = df["Data"].dt.year
    df["mes"] = df["Data"].dt.month
    df["mes_nome"] = df["mes"].map(MESES_PT)

    return df

df = load_data()

@st.cache_data
def load_patrimonio():
    try:
        df_p = pd.read_csv("patrimonio.csv", encoding="utf-8-sig", sep=None, engine="python")
    except:
        df_p = pd.read_csv("patrimonio.csv", encoding="latin-1", sep=None, engine="python")

    df_p.columns = df_p.columns.str.strip().str.replace("\ufeff", "", regex=False)

    # 🔥 TRATAMENTO DO VALOR (igual financeiro)
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

    df_p["ano"] = df_p["Data"].dt.year
    df_p["mes"] = df_p["Data"].dt.month

    return df_p

menu = st.radio(
    "",
    ["💰 Financeiro", "📈 Wealth Tracker"],
    horizontal=True
)

if menu == "💰 Financeiro":
    # tudo que já existe

    st.title("💰 Dashboard Financeiro")

    # =========================
    # FILTROS
    # =========================

    hoje = datetime.today()
    ano_atual = hoje.year
    mes_atual = hoje.month

    st.subheader("🎛️ Filtros")

    f1, f2 = st.columns(2)

    anos = sorted(df["ano"].dropna().unique())

    if ano_atual in anos:
        index_ano = anos.index(ano_atual)
    else:
        index_ano = len(anos) - 1  # fallback último ano disponível

    ano_sel = f1.selectbox("Ano", anos, index=index_ano)

    meses_disp = sorted(df[df["ano"] == ano_sel]["mes"].dropna().unique())

    if mes_atual in meses_disp and ano_sel == ano_atual:
        index_mes = meses_disp.index(mes_atual)
    else:
        index_mes = len(meses_disp) - 1  # fallback último mês disponível

    mes_nome_sel = f2.selectbox(
        "Mês",
        [MESES_PT[m] for m in meses_disp],
        index=index_mes
    )
    mes_sel = [k for k, v in MESES_PT.items() if v == mes_nome_sel][0]

    filtered = df[(df["ano"] == ano_sel) & (df["mes"] == mes_sel)]

    st.divider()


    # =========================
    # CONSOLIDADO
    # =========================

    st.subheader(f"📅 Consolidado do Ano {ano_sel}")

    df_ano = df[df["ano"] == ano_sel]

    pivot = df_ano.pivot_table(
        index="tipo_mov",
        columns="mes",
        values="Valor_num",
        aggfunc="sum",
        fill_value=0
    )

    pivot = pivot.reindex(columns=ORDEM_MESES, fill_value=0)

    # linha viagem
    viagem = (
        df_ano[df_ano["Subcategoria"].str.contains("viagem", case=False, na=False)]
        .pivot_table(
            index=lambda x: "Viagem",
            columns="mes",
            values="Valor_num",
            aggfunc="sum",
            fill_value=0
        )
    ).reindex(columns=ORDEM_MESES, fill_value=0)

    # saldo
    receita_row = pivot.loc["Receita"] if "Receita" in pivot.index else pd.Series(0, index=pivot.columns)
    despesa_row = pivot.loc["Despesa"] if "Despesa" in pivot.index else pd.Series(0, index=pivot.columns)

    pivot.loc["Saldo"] = receita_row - despesa_row

    pivot.index.name = None
    pivot = pd.concat([pivot, viagem])

    # ordem correta
    ordem = ["Receita", "Despesa", "Viagem", "Saldo"]
    pivot = pivot.reindex(ordem)

    # coluna total anual
    pivot["Total Ano"] = pivot.sum(axis=1)

    pivot.columns = [MESES_PT.get(c, c) for c in pivot.columns]
    pivot = pivot.reset_index().rename(columns={"index": ""})

    colunas_valores = pivot.columns[1:]

    styled = (
        pivot.style
        .format({col: formatar_real for col in colunas_valores})
        .applymap(
            colorir_saldo,
            subset=pd.IndexSlice[pivot[pivot[""] == "Saldo"].index, colunas_valores]
        )
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # =========================
    # 🔽 BLOCO COLAPSÁVEL
    # =========================

    with st.expander(f"🔎 Receitas e Despesas por Subcategoria — {ano_sel}"):

     colA, colB = st.columns(2)

    with colA:
        st.markdown("**Receitas por Subcategoria**")

        rec_sub = (
            df_ano[df_ano["tipo_mov"] == "Receita"]
            .groupby("Subcategoria")["Valor_num"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        if not rec_sub.empty:
            fig_rec = px.pie(rec_sub, names="Subcategoria", values="Valor_num", hole=0.6)
            fig_rec.update_traces(texttemplate="%{percent:.2%}")
            st.plotly_chart(fig_rec, use_container_width=True)

        with colB:
            st.markdown("**Despesas por Subcategoria**")

            desp_sub = (
                df_ano[df_ano["tipo_mov"] == "Despesa"]
                .groupby("Subcategoria")["Valor_num"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )

            if not desp_sub.empty:
                fig_desp = px.pie(desp_sub, names="Subcategoria", values="Valor_num", hole=0.6)
                fig_desp.update_traces(texttemplate="%{percent:.2%}")
                st.plotly_chart(fig_desp, use_container_width=True)

    st.divider()

    # =========================
    # KPI
    # =========================

    st.subheader(f"📊 Resumo — {mes_nome_sel} {ano_sel}")

    receitas = filtered[filtered["tipo_mov"] == "Receita"]["Valor_num"].sum()
    despesas = filtered[filtered["tipo_mov"] == "Despesa"]["Valor_num"].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", formatar_real(receitas))
    c2.metric("Despesas", formatar_real(despesas))
    c3.metric("Saldo", formatar_real(saldo))

    st.divider()

    # =========================
    # TENDÊNCIA
    # =========================

    st.subheader(f"📈 Tendência do Saldo — {ano_sel}")

    trend = (
        df_ano.groupby(["mes", "tipo_mov"])["Valor_num"]
        .sum()
        .unstack(fill_value=0)
    )

    trend["saldo"] = trend.get("Receita", 0) - trend.get("Despesa", 0)
    trend = trend.reindex(ORDEM_MESES, fill_value=0)
    trend["mes_label"] = trend.index.map(MESES_PT)

    fig_trend = px.line(trend, x="mes_label", y="saldo", markers=True)
    fig_trend.update_layout(xaxis_title=None)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # =========================
    # TRANSAÇÕES
    # =========================

    st.subheader(f"📋 Transações do Mês {mes_nome_sel} {ano_sel}")

    tabela_mes = filtered.copy()

    # 🔥 ordenação NUMÉRICA real
    tabela_mes = tabela_mes.sort_values("Data", ascending=True)

    tabela_mes["Data"] = tabela_mes["Data"].dt.strftime("%d/%m/%y")
    tabela_mes["Valor"] = tabela_mes["Valor_num"].apply(formatar_real)

    tabela_mes = tabela_mes[
        ["Data", "Descricao", "Subcategoria", "Tipo", "Valor"]
    ]

    st.dataframe(
        tabela_mes.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================
    # CONSOLIDADO FIXO DESPESAS CASA
    # =========================

    with st.expander(f"## 🏠 Consolidado Despesas Casa — {ano_sel}"):

        categorias_fixas = [
            "Academia Mami",
            "COMGÁS",
            "ENEL",
            "Fatura Mami",
            "IPTU",
            "Mercado",
            "NET Claro",
            "Prevent Sênior",
            "SABESP",
            "Casa",
            "Faxina",
            "Jardineiro",
            "Lima",
            "Piscina",
        ]

        df_ano = df[df["ano"] == ano_sel]

        # Filtra apenas essas subcategorias
        df_casa = df_ano[df_ano["Subcategoria"].isin(categorias_fixas)]

        pivot_casa = df_casa.pivot_table(
            index="Subcategoria",
            columns="mes",
            values="Valor_num",
            aggfunc="sum",
            fill_value=0
        )

        # garante todos os meses
        pivot_casa = pivot_casa.reindex(columns=ORDEM_MESES, fill_value=0)

        # garante todas as categorias mesmo se não houver valor
        pivot_casa = pivot_casa.reindex(categorias_fixas, fill_value=0)

        # coluna total ano por linha
        pivot_casa["Total Ano"] = pivot_casa.sum(axis=1)

        # linha total por mês
        total_mes = pivot_casa.sum(axis=0)
        pivot_casa.loc["Total do Ano Geral"] = total_mes

        # renomeia meses
        pivot_casa.columns = [
            MESES_PT.get(c, c) for c in pivot_casa.columns
        ]

        # formatação
        styled_casa = pivot_casa.style.format(
            {col: formatar_real for col in pivot_casa.columns}
        )

        st.dataframe(
            styled_casa,
            use_container_width=True
        )

        st.markdown("#### 📊 Visualização Analítica")

        # Reset para gráfico
        df_visual = pivot_casa.drop(index="Total do Ano Geral", errors="ignore").copy()

        # Remove coluna Total Ano do heatmap
        heatmap_data = df_visual.drop(columns=["Total Ano"], errors="ignore")

        # =========================
        # 🔥 HEATMAP
        # =========================
        import plotly.express as px

        fig_heatmap = px.imshow(
            heatmap_data,
            aspect="auto",
            labels=dict(x="Mês", y="Categoria", color="Valor"),
            text_auto=".2f"
        )

        fig_heatmap.update_layout(
            height=500
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)


elif menu == "📈 Wealth Tracker":

    st.title("📈 Evolução do Patrimônio")

    df_p = load_patrimonio()

    # =========================
    # TABELA CONSOLIDADA COMPLETA
    # =========================

    st.subheader("📊 Patrimônio por Instituição")

    df_p["mes_ano"] = df_p["Data"].dt.to_period("M")

    pivot_pat = df_p.pivot_table(
        index="Instituicao",
        columns="mes_ano",
        values="Valor_num",
        aggfunc="sum",
        fill_value=0
    )

    pivot_pat = pivot_pat.sort_index(axis=1)

    # converte colunas para string tipo Jan/2024
    colunas_periodo = pivot_pat.columns
    pivot_pat.columns = [
        f"{MESES_PT[col.month]}/{col.year}"
        for col in colunas_periodo
    ]

    # 🔥 TOTAL DO MÊS
    total_mes = pivot_pat.sum(axis=0)

    # 🔥 VARIAÇÃO % MÊS A MÊS
    var_mes = total_mes.pct_change().fillna(0) * 100

    # adiciona no dataframe
    pivot_pat.loc["Total do Mês"] = total_mes
    pivot_pat.loc["% Var. Mês"] = var_mes

    # =========================
    # FORMATAÇÃO
    # =========================

    def formatar_percentual(val):
        return f"{val:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

    def colorir_percentual(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: #00E676; font-weight: bold;"
            elif val < 0:
                return "color: #FF5252; font-weight: bold;"
        return ""

    def aplicar_formatacao(val, linha):
        if linha == "% Var. Mês":
            return formatar_percentual(val)
        else:
            return formatar_real(val)

    styled = pivot_pat.style.format(
        lambda v: formatar_percentual(v),
        subset=pd.IndexSlice[pivot_pat.index == "% Var. Mês", :]
    )

    styled = styled.format(
        lambda v: formatar_real(v),
        subset=pd.IndexSlice[pivot_pat.index != "% Var. Mês", :]
    )

    styled = styled.applymap(
        colorir_percentual,
        subset=pd.IndexSlice[pivot_pat.index == "% Var. Mês", :]
    )

    st.table(styled)

    # =========================
    # 💎 Patrimônio Total Consolidado
    # =========================

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

    fig_total.update_layout(
        yaxis_title="Patrimônio Total",
        xaxis_title=None
    )

    st.plotly_chart(fig_total, use_container_width=True)

    # =========================
    # 🏦 Evolução por Instituição (Escala Padronizada)
    # =========================

    df_inst = (
        df_p.groupby(["mes_ano", "Instituicao"])["Valor_num"]
        .sum()
        .reset_index()
    )

    df_inst["Data"] = df_inst["mes_ano"].dt.to_timestamp()

    fig_inst = px.line(
        df_inst,
        x="Data",
        y="Valor_num",
        color="Instituicao",
        markers=True
    )

    # 🔥 força escala única automática
    fig_inst.update_layout(
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True
        ),
        xaxis_title=None,
        yaxis_title="Valor"
    )

    st.plotly_chart(fig_inst, use_container_width=True)

    # =========================
    # 📈 Composição do Patrimônio (Área Correta)
    # =========================

    df_area = (
        df_p.groupby(["mes_ano", "Instituicao"])["Valor_num"]
        .sum()
        .reset_index()
        .sort_values("mes_ano")
    )

    # converte para data real
    df_area["Data"] = df_area["mes_ano"].dt.to_timestamp()

    fig_area = px.area(
        df_area,
        x="Data",
        y="Valor_num",
        color="Instituicao"
    )

    fig_area.update_layout(
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True
        ),
        xaxis_title=None,
        yaxis_title="Patrimônio"
    )

    st.plotly_chart(fig_area, use_container_width=True)