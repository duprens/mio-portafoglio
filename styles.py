import streamlit as st

PAGE_CONFIG = dict(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

CSS = """
<style>
.stAppDeployButton {display:none;}
/* Nasconde il widget di stato "Running..." in alto a destra */
div[data-testid="stStatusWidget"] { visibility: hidden; display: none !important; }

/* --- FIX SLIDER BIANCO TOTALE --- */
div[data-testid="stSlider"] { --primary-color: #ffffff !important; }

/* 1. Numero anni sopra il pallino */
div[data-testid="stSlider"] [data-testid="stThumbValue"] { color: #ffffff !important; }

/* 2. Pallino e Striscia Piena (usano la primary color definita sopra) */
div[data-testid="stSlider"] [role="slider"] { background-color: #ffffff !important; border: 2px solid #ffffff !important; box-shadow: none !important; }

/* 3. Nasconde i numeri 1 e 40 agli estremi (anche al passaggio del mouse) */
div[data-testid="stSlider"] [data-testid="stTickBarMin"], 
div[data-testid="stSlider"] [data-testid="stTickBarMax"] { display: none !important; visibility: hidden !important; }

/* ESORCISMO UNIVERSALE DEL ROSSO */
:root, .stApp { --primary-color: #555555 !important; --focus-ring-color: transparent !important; }
* { -webkit-tap-highlight-color: transparent !important; transition: none !important; }

/* Tasti Primary -> GRIGIO SCURO */
button[kind="primary"] { background-color: #555555 !important; border-color: #555555 !important; color: white !important; }
button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active { background-color: #666666 !important; border-color: #555555 !important; color: white !important; box-shadow: none !important; }

/* Tasti Secondary -> GRIGIO STANDARD/CHIARO SU HOVER */
button[kind="secondary"]:focus, button[kind="secondary"]:active { border-color: rgba(130, 130, 130, 0.4) !important; box-shadow: none !important; color: white !important; }
button[kind="secondary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; color: white !important; }

/* Stili Sidebar Grigia */
section[data-testid="stSidebar"] button[kind="primary"], section[data-testid="stSidebar"] button[kind="primary"]:focus, section[data-testid="stSidebar"] button[kind="primary"]:active { background-color: rgba(130, 130, 130, 0.15) !important; border-color: rgba(130, 130, 130, 0.3) !important; color: inherit !important; }
section[data-testid="stSidebar"] button[kind="primary"]:hover { background-color: rgba(130, 130, 130, 0.25) !important; border-color: rgba(130, 130, 130, 0.4) !important; }

/* Tastini + e - Soglia Ribilanciamento */
[data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:focus, [data-testid="stNumberInputStepDown"]:focus { background-color: rgba(130, 130, 130, 0.25) !important; color: inherit !important; }

/* Sidebar: bottone Esci position fixed in fondo (adjacent sibling, copre testid old + new) */
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(#logout-btn-anchor),
section[data-testid="stSidebar"] [data-testid="element-container"]:has(#logout-btn-anchor) {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(#logout-btn-anchor) + [data-testid="stElementContainer"],
section[data-testid="stSidebar"] [data-testid="element-container"]:has(#logout-btn-anchor) + [data-testid="element-container"] {
    position: fixed !important;
    bottom: 1.5rem !important;
    left: 1.5rem !important;
    right: auto !important;
    width: 17% !important;
    z-index: 999 !important;
}


</style>
"""


def apply():
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(CSS, unsafe_allow_html=True)
