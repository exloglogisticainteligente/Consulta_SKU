import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Consulta SKU - Riachuelo",
    page_icon="📦",
    layout="wide"
)

# ==================================================
# INICIALIZAÇÃO DA MEMÓRIA DA SESSÃO
# ==================================================

if "base_resgate" not in st.session_state:
    st.session_state.base_resgate = None

if "base_carregamento" not in st.session_state:
    st.session_state.base_carregamento = None

if "historico" not in st.session_state:

    st.session_state.historico = pd.DataFrame(
        columns=[
            "DATA_HORA",
            "SKU",
            "LOJA",
            "ONDA",
            "PALLETE",
            "DATA_CARREGAMENTO",
            "STATUS"
        ]
    )

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# ==================================================
# TRATAMENTO DOS CÓDIGOS DE BARRAS
# ==================================================

def tratar_sku(codigo_lido):

    codigo_lido = str(codigo_lido).strip()

    # Código de barras padrão E30
    if codigo_lido.startswith("E30"):

        return codigo_lido[3:14]

    # Código de barras padrão iniciado por 2
    if (
        codigo_lido.startswith("2")
        and len(codigo_lido) > 12
    ):

        return codigo_lido[1:12]

    # Se já for SKU digitado
    return codigo_lido

# ==================================================
# CONSULTA SKU
# ==================================================

def consultar_sku(sku_lido):

    sku = tratar_sku(sku_lido)

    base_resgate = st.session_state.base_resgate
    base_carregamento = st.session_state.base_carregamento

    historico = st.session_state.historico

    # Padroniza os tipos para texto

    base_resgate["SKU"] = (
        base_resgate["SKU"]
        .astype(str)
    )

    historico["SKU"] = (
        historico["SKU"]
        .astype(str)
    )

    base_resgate["ONDA"] = (
        base_resgate["ONDA"]
        .astype(str)
    )

    historico["ONDA"] = (
        historico["ONDA"]
        .astype(str)
    )

    base_resgate["PALLETE"] = (
        base_resgate["PALLETE"]
        .astype(str)
    )

    historico["PALLETE"] = (
        historico["PALLETE"]
        .astype(str)
    )

    ocorrencias = base_resgate[
    base_resgate["SKU"] == sku
    ]

    # --------------------------------------
    # SKU NÃO ENCONTRADO
    # --------------------------------------

    if ocorrencias.empty:

        novo_registro = pd.DataFrame([{
            "DATA_HORA": datetime.now(),
            "SKU": sku,
            "LOJA": "",
            "ONDA": "",
            "PALLETE": "",
            "DATA_CARREGAMENTO": "",
            "STATUS": "SEM RESGATE"
        }])

        st.session_state.historico = pd.concat(
            [historico, novo_registro],
            ignore_index=True
        )

        return {
            "status": "SEM RESGATE",
            "sku": sku
        }

    # --------------------------------------
    # VERIFICA RESGATES JÁ UTILIZADOS
    # --------------------------------------

    disponiveis = ocorrencias.merge(
        historico[
            ["SKU", "ONDA", "PALLETE"]
        ],
        on=["SKU", "ONDA", "PALLETE"],
        how="left",
        indicator=True
    )

    disponiveis = disponiveis[
        disponiveis["_merge"] == "left_only"
    ]

    # --------------------------------------
    # SEM RESGATES DISPONÍVEIS
    # --------------------------------------

    if disponiveis.empty:

        novo_registro = pd.DataFrame([{
            "DATA_HORA": datetime.now(),
            "SKU": sku,
            "LOJA": "",
            "ONDA": "",
            "PALLETE": "",
            "DATA_CARREGAMENTO": "",
            "STATUS": "SEM RESGATE"
        }])

        st.session_state.historico = pd.concat(
            [historico, novo_registro],
            ignore_index=True
        )

        return {
            "status": "SEM RESGATE",
            "sku": sku
        }

    # --------------------------------------
    # RESGATE ENCONTRADO
    # --------------------------------------

    proximo = disponiveis.iloc[0]

    onda = str(proximo["ONDA"])

    loja = onda[:4]

    dados_loja = base_carregamento[
        base_carregamento["LOJA"].astype(str)
        == loja
    ]

    if not dados_loja.empty:

        carregamento = dados_loja.iloc[0][
            "DATA_CARREGAMENTO"
        ]

    else:

        carregamento = "NÃO LOCALIZADO"

    novo_registro = pd.DataFrame([{
        "DATA_HORA": datetime.now(),
        "SKU": proximo["SKU"],
        "LOJA": loja,
        "ONDA": proximo["ONDA"],
        "PALLETE": proximo["PALLETE"],
        "DATA_CARREGAMENTO": carregamento,
        "STATUS": "ENCONTRADO"
    }])

    st.session_state.historico = pd.concat(
        [
            historico,
            novo_registro
        ],
        ignore_index=True
    )

    return {
        "status": "ENCONTRADO",
        "sku": proximo["SKU"],
        "onda": proximo["ONDA"],
        "pallete": proximo["PALLETE"],
        "qtd_pecas": proximo["QTD_PECAS"],
        "loja": loja,
        "carregamento": carregamento,
        "restantes": len(disponiveis) - 1
    }

# ==================================================
# CABEÇALHO
# ==================================================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:

    try:

        st.image(
            "logo.jpeg",
            width=180
        )

    except:

        pass

with col_titulo:

    st.title(
        "CONSULTA SKU - RIACHUELO"
    )

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title(
    "ADMINISTRAÇÃO"
)

base_resgate_file = st.sidebar.file_uploader(
    "Base Resgate",
    type=["xlsx"]
)

if base_resgate_file is not None:

    st.session_state.base_resgate = pd.read_excel(
    base_resgate_file
    )

    st.session_state.base_resgate[
        "SKU"
    ] = st.session_state.base_resgate[
        "SKU"
    ].astype(str)

    st.session_state.base_resgate[
        "ONDA"
    ] = st.session_state.base_resgate[
        "ONDA"
    ].astype(str)

    st.session_state.base_resgate[
        "PALLETE"
    ] = st.session_state.base_resgate[
        "PALLETE"
    ].astype(str)

    st.sidebar.success(
        "Base Resgate carregada."
    )

base_carregamento_file = st.sidebar.file_uploader(
    "Base Carregamento",
    type=["xlsx"]
)

if base_carregamento_file is not None:

    st.session_state.base_carregamento = pd.read_excel(
        base_carregamento_file
    )

    st.sidebar.success(
        "Base Carregamento carregada."
    )

# ==================================================
# CONSULTA
# ==================================================

if (
    st.session_state.base_resgate is not None
    and
    st.session_state.base_carregamento is not None
):

    st.subheader("Consulta")

    # ENTER funciona automaticamente em formulário

    with st.form(
        "form_consulta",
        clear_on_submit=True
    ):

        sku = st.text_input(
            "Digite ou bipa o SKU"
        )

        consultar = st.form_submit_button(
            "CONSULTAR"
        )

    if consultar:

        st.session_state.resultado = consultar_sku(
            sku
        )

    if st.session_state.resultado:

        resultado = st.session_state.resultado

        if resultado["status"] == "SEM RESGATE":

            st.error(
                f"❌ SEM RESGATE - SKU {resultado['sku']}"
            )

        else:

            st.success(
                "✅ RESGATE DISPONÍVEL"
            )

            st.write(
                f"**SKU:** {resultado['sku']}"
            )

            st.write(
                f"**ONDA:** {resultado['onda']}"
            )

            st.write(
                f"**PALLETE:** {resultado['pallete']}"
            )

            st.write(
                f"**QTD PEÇAS:** {resultado['qtd_pecas']}"
            )

            st.write(
                f"**LOJA:** {resultado['loja']}"
            )

            st.write(
                f"**CARREGAMENTO:** {resultado['carregamento']}"
            )

            st.write(
                f"**RESGATES RESTANTES:** {resultado['restantes']}"
            )

else:

    st.warning(
        "Faça upload da Base Resgate e da Base Carregamento para iniciar."
    )

# ==================================================
# HISTÓRICO
# ==================================================

st.divider()

st.subheader(
    "HISTÓRICO DA SESSÃO"
)

st.dataframe(
    st.session_state.historico,
    use_container_width=True
)

# ==================================================
# DOWNLOAD HISTÓRICO
# ==================================================

if not st.session_state.historico.empty:

    buffer = BytesIO()

    st.session_state.historico.to_excel(
        buffer,
        index=False
    )

    st.download_button(
        label="📥 BAIXAR HISTÓRICO",
        data=buffer.getvalue(),
        file_name=f"Historico_{datetime.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button(
        "🗑️ ZERAR HISTÓRICO"
    ):

        st.session_state.historico = pd.DataFrame(
            columns=[
                "DATA_HORA",
                "SKU",
                "LOJA",
                "ONDA",
                "PALLETE",
                "DATA_CARREGAMENTO",
                "STATUS"
            ]
        )

        st.session_state.resultado = None

        st.rerun()