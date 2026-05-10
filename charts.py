import streamlit as st

THEMES = {
    "Grigio Fumo": {"main": "#555555", "hover": "#666666", "rgb": "130, 130, 130", "bg": "#0e1117", "sidebar": "#1e2127", "text": "#fafafa"},
    "Azzurro Cielo": {"main": "#5dade2", "hover": "#85c1e9", "rgb": "93, 173, 226", "bg": "#f0f8ff", "sidebar": "#d6eaf8", "text": "#1b2631"},
    "Arancio Pesca": {"main": "#edbb99", "hover": "#f5cba7", "rgb": "237, 187, 153", "bg": "#fffaf0", "sidebar": "#fae5d3", "text": "#2e1a05"},
    "Giallo Sabbia": {"main": "#f7dc6f", "hover": "#f8e28b", "rgb": "247, 220, 111", "bg": "#fefdf0", "sidebar": "#fcf3cf", "text": "#1d1d1d"},
    "Verde Acqua": {"main": "#76d7c4", "hover": "#a3e4d7", "rgb": "118, 215, 196", "bg": "#f4fdfb", "sidebar": "#d1f2eb", "text": "#0e2f2f"},
    "Violetto Lavanda": {"main": "#bb8fce", "hover": "#d2b4de", "rgb": "187, 143, 206", "bg": "#fbf9ff", "sidebar": "#ebdef0", "text": "#211a23"}
}

PAGE_CONFIG = dict(layout="wide", page_title="Monitoraggio Portafogli", page_icon="📈")

CSS = """
<style>
.stAppDeployButton {display:none;}
/* Nasconde il widget di stato "Running..." in alto a destra */
div[data-testid="stStatusWidget"] { visibility: hidden; display: none !important; }

/* Sfondi e Testi App */
.stApp { background-color: [[BG]] !important; color: [[TEXT]] !important; }
[data-testid="stSidebar"] { background-color: [[SIDEBAR]] !important; }
[data-testid="stSidebarContent"] { background-color: [[SIDEBAR]] !important; }
[data-testid="stSidebar"] * { color: [[TEXT]] !important; }

/* Slider: esorcismo definitivo del rosso su traccia, pallino e label numerica */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] { background-color: [[MAIN]] !important; border-color: [[MAIN]] !important; box-shadow: none !important; }
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div > div { background-color: [[MAIN]] !important; }
/* Tratto riempito (linear-gradient inline) -> grigio */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[style*="linear-gradient"] { background: [[MAIN]] !important; opacity: 0.5; }
/* Eventuali residui rossi inline (rgb(255,...)) -> grigio */
div[data-testid="stSlider"] div[data-baseweb="slider"] div[style*="rgb(255"] { background-color: [[MAIN]] !important; color: [[TEXT]] !important; }
/* Label numerica sopra al pallino -> bianco sporco */
div[data-testid="stSlider"] [data-testid="stThumbValue"] { color: [[TEXT]] !important; }

/* ESORCISMO UNIVERSALE DEL ROSSO */
:root { --primary-color: [[MAIN]] !important; --focus-ring-color: transparent !important; }
* { -webkit-tap-highlight-color: transparent !important; transition: none !important; }

/* Tasti Primary */
button[kind="primary"] { background-color: [[MAIN]] !important; border-color: [[MAIN]] !important; color: white !important; }
button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active { background-color: [[HOVER]] !important; border-color: [[MAIN]] !important; color: white !important; box-shadow: none !important; }

/* Tasti Secondary */
button[kind="secondary"]:focus, button[kind="secondary"]:active { border-color: rgba([[RGB]], 0.4) !important; box-shadow: none !important; }
button[kind="secondary"]:hover { background-color: rgba([[RGB]], 0.25) !important; border-color: rgba([[RGB]], 0.4) !important; }

/* Stili Sidebar */
section[data-testid="stSidebar"] button[kind="primary"], section[data-testid="stSidebar"] button[kind="primary"]:focus, section[data-testid="stSidebar"] button[kind="primary"]:active { background-color: rgba([[RGB]], 0.15) !important; border-color: rgba([[RGB]], 0.3) !important; color: inherit !important; }
section[data-testid="stSidebar"] button[kind="primary"]:hover { background-color: rgba([[RGB]], 0.25) !important; border-color: rgba([[RGB]], 0.4) !important; }

/* Tastini + e - Soglia Ribilanciamento */
[data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:focus, [data-testid="stNumberInputStepDown"]:focus { background-color: rgba([[RGB]], 0.25) !important; color: inherit !important; }

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
    
    themed_css = CSS.replace("[[MAIN]]", conf["main"]) \
                    .replace("[[HOVER]]", conf["hover"]) \
                    .replace("[[RGB]]", conf["rgb"]) \
                    .replace("[[BG]]", conf["bg"]) \
                    .replace("[[SIDEBAR]]", conf["sidebar"]) \
                    .replace("[[TEXT]]", conf["text"])

    st.set_page_config(**PAGE_CONFIG)
    st.markdown(themed_css, unsafe_allow_html=True)
