import streamlit as st
import base64
from components.conversation import clear_conversation, render_conversation
from components.message_input import render_message_input
from utils.config import load_config

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def main():
    st.set_page_config(
        page_title="DA Search",
        page_icon="🔎",
        layout="wide",
    )

    load_config()
    img_base64_1 = get_base64_of_bin_file('utils/fond_app.png')
    img_base64_2 = get_base64_of_bin_file('utils/fond_ciel.png')

    st.markdown(f"""
    <style>
    .search-bar-wide {{
        background:url("data:image/png;base64,{img_base64_1}") center/cover no-repeat;
        padding: 34px 0 22px 0;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 100;
        width: 100%;
    }}
    .search-bar-wide h1 {{
        color: #fff;
        font-size: 2.1em;
        font-weight: 800;
        text-shadow: 0 1px 8px #00205B99;
        margin: 0 0 8px 0;
        letter-spacing: 1.1px;
    }}
    .large-search-container {{
        display: flex;
        justify-content: center;
        margin-top: 16px;
        margin-bottom: 0;
    }}
    .large-search-box {{
        width: 84vw;
        max-width: 1100px;
        display: flex;
        align-items: center;
        gap: 0.5em;
        background: rgba(255,255,255,0.95);
        border-radius: 13px;
        box-shadow: 0 2px 8px #00205B15;
        padding: 0.8em 1.2em;
    }}
    .large-search-box input[type="text"] {{
        font-size: 1.15em;
        width: 100%;
        border: none;
        outline: none;
        background: transparent;
        color: #1C1C1C;
        padding: 0.7em 0.6em;
    }}
    .objectives {{
        background:url("data:image/png;base64,{img_base64_2}") center/cover no-repeat;
        border-radius: 12px;
        padding: 18px 28px;
        margin-bottom: 20px;
        color: #00205B;
        box-shadow: 0 1px 5px rgba(0,0,0,0.07);
    }}
    .stApp {{
        background: #F3F6FA;
        color: #1C1C1C;
        font-family: "Segoe UI", "Inter", sans-serif;
    }}
    .stButton>button {{
        background: linear-gradient(90deg,#1976D2, #00A9E0 90%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.4em;
        font-weight: bold;
        font-size: 1em;
    }}
    .stButton>button:hover {{
        background: #1976D2;
    }}
    /* Nouveau style pour le bloc flottant effacer */
    .effacer-float-bloc {{
        position: fixed;
        bottom: 32px;
        right: 32px;
        z-index: 999;
        background: #fff;
        border-radius: 18px;
        box-shadow: 0 4px 22px rgba(0,32,91,0.11), 0 0px 0px #00205b09;
        padding: 22px 28px 18px 28px;
        display: flex;
        align-items: center;
        min-width: 200px;
        justify-content: center;
        transition: box-shadow 0.2s;
    }}
    .effacer-float-bloc:hover {{
        box-shadow: 0 6px 28px rgba(0,32,91,0.16);
    }}
    .effacer-float-bloc button {{
        background: linear-gradient(90deg,#e53935,#ff6a13 80%);
        color: #fff !important;
        border: none;
        border-radius: 7px;
        font-weight: bold;
        font-size: 1.09em;
        padding: 0.7em 1.6em;
        box-shadow: 0 2px 7px #e5393530;
        transition: background 0.15s;
    }}
    .effacer-float-bloc button:hover {{
        background: #e53935 !important;
        color: #fff !important;
    }}
    </style>
    """, unsafe_allow_html=True)

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

    # --- LARGE SEARCH BAR ALWAYS ON TOP ---
    st.markdown("""
    <div class="search-bar-wide">
        <h1>Recherche intelligente d'anomalies (DA)</h1>
    """, unsafe_allow_html=True)
    render_message_input()
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- CONVERSATION / RESULTATS ---
    with st.container():
        st.markdown("#### 💬 Résultats")
        render_conversation()

    # --- OBJECTIFS EN BAS ---
    with st.expander("🎯 Objectifs de l’outil", expanded=False):
        st.markdown("""
        <ul>
            <li>🔍 <strong>Recherche rapide</strong> de cas similaires (description ou mot-clé).</li>
            <li>🧠 <strong>Inspiration via cas déjà résolus</strong> pour accélérer le diagnostic.</li>
            <li>🗂️ <strong>Exploration historique</strong> via filtres (programme, ligne, dates...)</li>
            <li>✏️ <strong>Recherche libre</strong> sur toute la base depuis 2020.</li>
            <li>⏳ <strong>Réduction des délais</strong> d’analyse grâce à l’IA et l’ergonomie.</li>
        </ul>
        """)

    # --- EFFACER TJR ACCESSIBLE DANS UN BLOC BLANC FLOTTANT ---
    st.markdown("""
    <div class="effacer-float-bloc">
    """, unsafe_allow_html=True)
    if st.button("🧹 Réinitialiser la conversation", key="clear_btn", disabled=st.session_state.interface_locked):
        clear_conversation()
    st.markdown("</div>", unsafe_allow_html=True)

    # Overlay de “traitement en cours”
    if st.session_state.interface_locked:
        st.markdown("""
            <div class="overlay">
                <div class="overlay-content">
                    <h3>⏳ Traitement en cours</h3>
                    <p>Merci de patienter pendant le traitement de votre requête...</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Rafraîchissement si déverrouillage
    if st.session_state.get("_previous_lock_state", False) and not st.session_state.interface_locked:
        st.session_state._previous_lock_state = False
        st.rerun()
    st.session_state._previous_lock_state = st.session_state.interface_locked

if __name__ == "__main__":
    main()
