import streamlit as st

PAGE_CONFIG = dict(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

CSS = """
<style>
.stAppDeployButton {display:none;}
/* Slider: esorcismo definitivo del rosso su traccia e pallino */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] { background-color: #555555 !important; border-color: #555555 !important; box-shadow: none !important; }
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div > div { background-color: #555555 !important; }

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

/* LA PILLOLA PERFETTA per D e W */
div[data-testid="stHorizontalBlock"]:has(#pill-anchor) { gap: 0px !important; }
div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1), div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) { width: 36px !important; min-width: 36px !important; max-width: 36px !important; flex: none !important; padding: 0 !important; }
div[data-testid="stHorizontalBlock"]:has(#pill-anchor) button { min-height: 28px !important; height: 28px !important; padding: 0 !important; margin: 0 !important; border-radius: 0 !important; font-size: 13px !important; }
div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(1) button { border-top-left-radius: 6px !important; border-bottom-left-radius: 6px !important; border-right: none !important; }
div[data-testid="stHorizontalBlock"]:has(#pill-anchor) > div[data-testid="column"]:nth-child(2) button { border-top-right-radius: 6px !important; border-bottom-right-radius: 6px !important; }
span#pill-anchor { display: none !important; }
</style>
"""


def apply():
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(CSS, unsafe_allow_html=True)
