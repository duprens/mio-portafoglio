import streamlit as st

PAGE_CONFIG = dict(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

CSS = """
<style>
.stAppDeployButton {display:none;}
/* Nasconde il widget di stato "Running..." in alto a destra */
div[data-testid="stStatusWidget"] { visibility: hidden; display: none !important; }

/* Slider: Pallino, Striscia Piena e Numero in Bianco */
div[data-testid="stSlider"] [data-testid="stThumbValue"] { color: #ffffff !important; }
div[data-testid="stSlider"] [role="slider"] { background-color: #ffffff !important; border-color: #ffffff !important; box-shadow: none !important; }
/* Target della striscia piena (sovrascrive il gradiente dinamico) */
div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] { background: #ffffff !important; }
/* Sfondo della traccia rimanente (quella vuota) per mantenere il contrasto */
div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div > div { background-color: #444444 !important; }

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
