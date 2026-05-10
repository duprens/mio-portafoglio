import streamlit as st

THEMES = {
    "Grigio Fumo": {"main": "#555555", "hover": "#666666", "rgb": "130, 130, 130"},
    "Azzurro Cielo": {"main": "#a2c2e1", "hover": "#b9d1e9", "rgb": "162, 194, 225"},
    "Arancio Pesca": {"main": "#f4d1a6", "hover": "#f8e1c7", "rgb": "244, 209, 166"},
    "Giallo Sabbia": {"main": "#ece2c6", "hover": "#f2ebd9", "rgb": "236, 226, 198"},
    "Verde Acqua": {"main": "#b2d8d8", "hover": "#c9e5e5", "rgb": "178, 216, 216"},
    "Violetto Lavanda": {"main": "#d1d1f0", "hover": "#e2e2f7", "rgb": "209, 209, 240"}
}

PAGE_CONFIG = dict(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

CSS = """
<style>
.stAppDeployButton {display:none;}
/* Nasconde il widget di stato "Running..." in alto a destra */
div[data-testid="stStatusWidget"] { visibility: hidden; display: none !important; }
/* Slider: esorcismo definitivo del rosso su traccia, pallino e label numerica */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] { background-color: #888888 !important; border-color: #888888 !important; box-shadow: none !important; }
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div > div { background-color: #555555 !important; }
/* Tratto riempito (linear-gradient inline) -> grigio */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[style*="linear-gradient"] { background: #888888 !important; }
/* Eventuali residui rossi inline (rgb(255,...)) -> grigio */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[style*="rgb(255"] { background-color: #888888 !important; color: #fafafa !important; }
/* Label numerica sopra al pallino -> bianco sporco */
div[data-testid="stSlider"] [data-testid="stThumbValue"] { color: #fafafa !important; }

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


def apply(theme_name="Grigio Fumo"):
    conf = THEMES.get(theme_name, THEMES["Grigio Fumo"])
    p, h, r = conf["main"], conf["hover"], conf["rgb"]

    # Iniettiamo i colori del tema nel CSS sostituendo i valori statici
    themed_css = CSS.replace("#555555", p).replace("#666666", h).replace("130, 130, 130", r)

    st.set_page_config(**PAGE_CONFIG)
    st.markdown(themed_css, unsafe_allow_html=True)
