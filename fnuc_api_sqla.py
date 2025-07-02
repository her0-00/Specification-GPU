import streamlit as st
from components.conversation import clear_conversation, render_conversation, afficher_dataframe_dataset
from components.message_input import render_message_input
from components.sidebar  import render_sidebar

from utils.config import load_config

def main():
    st.set_page_config(
        page_title="DA",
        page_icon="🤖",
        layout="wide",
    )

    st.markdown("""
    <style>
    .custom-title-block {
        background: url('images/mon_fond.jpg') center/cover no-repeat;
        border-radius: 12px;
        padding: 50px 0 40px 0;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 3px 12px rgba(0,0,0,0.15);
    }
    .custom-title-block h1 {
        color: #fff;
        font-size: 2.7em;
        font-weight: 800;
        text-shadow: 1px 2px 8px #00205B99;
        margin: 0;
    }
    /* Reste du style général */
    .stApp {
        background-color: #F4F4F4;
        color: #1C1C1C;
        font-family: "Segoe UI", sans-serif;
    }
    h1, h2, h3, h4 {
        color: #00205B;
        font-weight: 600;
    }
    .block-container > div {
        border: 1px solid #D0D0D0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 25px;
        background-color: white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #FF6A13;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5em 1em;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #e65c00;
    }
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input,
    .stMultiSelect div[data-baseweb="select"],
    .stNumberInput input,
    .stDateInput input {
        border: 2px solid #1976D2 !important;
        border-radius: 6px !important;
        background-color: white !important;
        color: #1C1C1C !important;
    }
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stTextInput input:focus,
    .stMultiSelect div[data-baseweb="select"]:focus-within,
    .stNumberInput input:focus,
    .stDateInput input:focus {
        border: 2px solid #00205B !important;
        box-shadow: 0 0 0 2px rgba(0,32,91,0.2);
    }
    section[data-testid="stSidebar"] {
        background-color: #00A9E0;
        color: white;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    .sidebar-badge {
        background: #FF6A13;
        color: white;
        padding: 0.2em 0.7em;
        border-radius: 12px;
        margin-right: 4px;
        font-size: 0.9em;
        display: inline-block;
    }
    .sidebar-reset-btn > button {
        background-color: #e53935 !important;
        color: white !important;
        border-radius: 8px !important;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    load_config()

    for key, default in {
        "messages": [],
        "messages_llm": [],
        "filters": [],
        "interface_locked": False,
        "processing_query": False,
        "needs_processing": False,
        "query_to_process": "",
        "current_query_type": "Specific Question"
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # SECTION TITRE AVEC IMAGE DE FOND
    st.markdown("""
    <div class="custom-title-block">
        <h1>Solution d'aide à la décision dans le traitement des DA</h1>
    </div>
    """, unsafe_allow_html=True)

    # SECTION PRINCIPALE
    with st.container():
        st.markdown("### 💬 Recherche")
        render_conversation()
        render_message_input()

        _, col2, _ = st.columns([1, 1, 1])
        with col2:
            if st.button("🧹 Effacer l'historique", use_container_width=True, disabled=st.session_state.interface_locked):
                clear_conversation()

        if st.session_state.interface_locked:
            st.markdown("""
                <div class="overlay">
                    <div class="overlay-content">
                        <h3>⏳ Traitement en cours</h3>
                        <p>Merci de patienter pendant le traitement de votre requête...</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🎯 Objectifs de l’outil")
        st.markdown("""
        <div style="background-color: white; border: 2px solid #00205B; border-radius: 10px; padding: 20px; margin-bottom: 25px; color: black;">
            <p>
                Cet outil a été conçu pour <strong>faciliter l’analyse et le traitement des Déclarations d’Anomalie (DA)</strong> 
                en capitalisant sur l’historique des cas rencontrés depuis <strong>2020</strong>.
            </p>
            <ul>
                <li>🔍 <strong>Retrouver rapidement des cas similaires</strong> à une anomalie en cours, à partir d’une description ou d’un mot-clé.</li>
                <li>🧠 <strong>S’inspirer des résolutions passées</strong> pour accélérer le diagnostic et la prise de décision.</li>
                <li>🗂️ <strong>Explorer l’historique des DA</strong> via une base de données enrichie et filtrable.</li>
                <li>🧭 <strong>Affiner les recherches</strong> grâce aux filtres disponibles(programme, ligne, dates, etc.).</li>
                <li>✏️ <strong>Interroger l’outil librement</strong> en saisissant une description ou un mot-clé du défaut.</li>
            </ul>
            <p>
                En résumé, cette solution d’aide à la décision vise à <strong>réduire les délais d’analyse</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Rafraîchissement si déverrouillage
    if st.session_state.get("_previous_lock_state", False) and not st.session_state.interface_locked:
        st.session_state._previous_lock_state = False
        st.rerun()
    st.session_state._previous_lock_state = st.session_state.interface_locked

if __name__ == "__main__":
    main()
