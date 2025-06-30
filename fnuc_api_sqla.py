import streamlit as st
from utils.chroma_filter_builder import ChromaFilterBuilder
from utils.config import load_config
import pandas as pd 
# Mise en cache du chargement de la config
@st.cache_data
def get_config():
    return load_config()
    
@st.cache_data
def load_full_data():
    # Adapter selon le format du fichier de données complet
    return pd.read_json("..//..//data//processed//dataset.jsonl",lines=True)
def get_dynamic_options(df, filter_key, active_filters):
    filtered_df = df.copy()
    if active_filters:
        for k, v in active_filters.items():
            if k != filter_key and v:
                if isinstance(v, dict):
                    inner = v.get(k, {})
                    for op, val in inner.items():
                        if op == "$in":
                            filtered_df = filtered_df[filtered_df[k].isin(val)]
                        elif op == "$eq":
                            filtered_df = filtered_df[filtered_df[k] == val]
                        elif op == "$ne":
                            filtered_df = filtered_df[filtered_df[k] != val]
                        elif op == "$gte":
                            filtered_df = filtered_df[filtered_df[k] >= val]
                        elif op == "$lte":
                            filtered_df = filtered_df[filtered_df[k] <= val]
                        # Ajoute d'autres opérateurs si besoin
                elif isinstance(v, list):
                    filtered_df = filtered_df[filtered_df[k].isin(v)]
                else:
                    filtered_df = filtered_df[filtered_df[k] == v]
    return sorted(filtered_df[filter_key].dropna().unique())

import streamlit as st

def render_sidebar():
    """
    Sidebar optimisée pour le chargement/rafraîchissement des filtres.
    """

    # CSS pour badges/boutons avec couleurs Safran
    st.markdown("""
    <style>
    /* Fond de la sidebar */
    section[data-testid="stSidebar"] {
        background-color:#00A9E0;
        color: white;
    }

    /* Texte dans la sidebar */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Badges */
    .sidebar-badge {
        background: #FF6A13;
        color: white;
        padding: 0.2em 0.7em;
        border-radius: 12px;
        margin-right: 4px;
        font-size: 0.9em;
        display: inline-block;
    }

    /* Bouton de reset */
    .sidebar-reset-btn > button {
        background-color: #e53935 !important;
        color: white !important;
        border-radius: 8px !important;
        margin-top: 8px;
    }
    
    /* Appliquer un contour bleu ciel foncé aux widgets */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input,
    .stMultiSelect div[data-baseweb="select"],
    .stNumberInput input,
    .stDateInput input {
        border: 2px solid #1565C0 !important;
        border-radius: 6px !important;
        background-color: white !important;
        color: black !important;
    }

    /* Focus (quand on clique) */
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stTextInput input:focus,
    .stMultiSelect div[data-baseweb="select"]:focus-within,
    .stNumberInput input:focus,
    .stDateInput input:focus {
        border: 2px solid #1976D2 !important;
        box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.3);
    }
    </style>
""", unsafe_allow_html=True)



    with st.sidebar:
        st.title("🛠️ Options")
        st.markdown("Sélectionnez et combinez les filtres ci-dessous pour affiner votre recherche des DA.", help="Utilisez les filtres pour ajuster la recherche.")

        # Chargement config (mise en cache)
        if "config" not in st.session_state:
            st.session_state.config = get_config()
        config = st.session_state.config

        # Initialisation rapide du state
        for k, v in [
            ("active_filters", {}),
            ("loose_filters", {}),
            ("document_filters", {"contains": [], "not_contains": []}),
            ("contains_terms", []),
            ("not_contains_terms", []),
            ("interface_locked", False)
        ]:
            st.session_state.setdefault(k, v)

        # RESET global
        if st.button("♻️ Réinitialiser tous les filtres", key="reset_all", help="Enlève tous les filtres actifs", type="primary"):
            for k in [
                "active_filters", "loose_filters",
                "document_filters", "contains_terms",
                "not_contains_terms", "where_document", "metadata_filters"
            ]:
                st.session_state[k] = {} if isinstance(st.session_state[k], dict) else []
            st.rerun()

        st.subheader("🔗 Combinaison de filtres")
        filter_grouping = st.radio(
            "Méthode de groupement",
            ["AND", "OR"],
            horizontal=True,
            key="filter_grouping",
            disabled=st.session_state.interface_locked
        )

        # --- Filtres Metadata ---
        st.markdown("### Filtres")

        for filter_def in config.get("available_filters", []):
            filter_type = filter_def.get("type", "")
            filter_key = filter_def.get("key", "")
            filter_name = filter_def.get("name", filter_key)
            df = load_full_data()
            with st.expander(f"{filter_name}", expanded=False):
                if filter_type =="date_range" :
                    filter_enabled = st.toggle(
                        "Activer ce filtre",
                        value=False,
                        key=f"{filter_key}_enabled",
                        disabled=st.session_state.interface_locked,
                        help="Active ou désactive ce filtre."
                    )
          
                is_strict = st.toggle(
                    "Filtrage strict (exclure les documents sans valeur)",
                    value=True,
                    key=f"{filter_key}_strict",
                    help="Si désactivé, les documents sans cette valeur seront inclus.",
                    disabled=st.session_state.interface_locked
                )
                st.session_state.loose_filters[filter_key] = not is_strict

                if filter_type =="date_range" and not filter_enabled:
                    clear_filter(filter_key)
                    continue

                if filter_type == "date_range":
                    date_filter_type = st.radio(
                        "Type de filtre de date",
                        ["Range", "Before", "After", "Exact"],
                        horizontal=True,
                        key=f"{filter_key}_filter_type",
                        help="Choisissez le type de critère temporel à appliquer.",
                        disabled=st.session_state.interface_locked
                    )
                    operator_start = "$gte"
                    operator_end = "$lt"

                    if date_filter_type == "Range":
                        col1, col2 = st.columns(2)
                        with col1:
                            start_date = st.date_input(
                                "De",
                                key=f"{filter_key}_start",
                                disabled=st.session_state.interface_locked,
                            )
                            include_start = st.checkbox(
                                "Inclure cette date",
                                value=True,
                                key=f"{filter_key}_include_start",
                                disabled=st.session_state.interface_locked,
                            )
                            operator_start = "$gte" if include_start else "$gt"
                        with col2:
                            end_date = st.date_input(
                                "À",
                                key=f"{filter_key}_end",
                                disabled=st.session_state.interface_locked,
                            )
                            include_end = st.checkbox(
                                "Inclure cette date",
                                value=False,
                                key=f"{filter_key}_include_end",
                                disabled=st.session_state.interface_locked,
                            )
                            operator_end = "$lte" if include_end else "$lt"
                        if start_date and end_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                start_date=start_date,
                                end_date=end_date,
                                operator_start=operator_start,
                                operator_end=operator_end,
                            )
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)
                    elif date_filter_type == "Before":
                        end_date = st.date_input(
                            "Avant la date",
                            key=f"{filter_key}_before",
                            disabled=st.session_state.interface_locked,
                        )
                        include_end = st.checkbox(
                            "Inclure cette date",
                            value=False,
                            key=f"{filter_key}_include_before",
                            disabled=st.session_state.interface_locked,
                        )
                        operator_end = "$lte" if include_end else "$lt"
                        if end_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                end_date=end_date,
                                operator_end=operator_end,
                            )
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)
                    elif date_filter_type == "After":
                        start_date = st.date_input(
                            "Après la date",
                            key=f"{filter_key}_after",
                            disabled=st.session_state.interface_locked,
                        )
                        include_start = st.checkbox(
                            "Inclure cette date",
                            value=True,
                            key=f"{filter_key}_include_after",
                            disabled=st.session_state.interface_locked,
                        )
                        operator_start = "$gte" if include_start else "$gt"
                        if start_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                start_date=start_date,
                                operator_start=operator_start,
                            )
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)
                    elif date_filter_type == "Exact":
                        exact_date = st.date_input(
                            "Date exacte",
                            key=f"{filter_key}_exact",
                            disabled=st.session_state.interface_locked,
                        )
                        if exact_date:
                            date_str = exact_date.isoformat()
                            date_filter = ChromaFilterBuilder.eq(
                                field=filter_key, value=date_str
                            )
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)

                elif filter_type == "multiselect":
                    options = get_dynamic_options(df, filter_key, st.session_state.active_filters)
                    selected = st.multiselect(
                        "Options",
                        options=options,
                        key=f"{filter_key}_select",
                        help="Sélectionnez une ou plusieurs valeurs.",
                        disabled=st.session_state.interface_locked
                    )
                    filter_mode = st.radio(
                        "Mode de filtre",
                        ["Inclure la sélection", "Exclure la sélection"],
                        horizontal=True,
                        key=f"{filter_key}_mode",
                        disabled=st.session_state.interface_locked,
                    )
                    inner_operator = st.radio(
                        "Opérateur",
                        ["OU (au moins 1)", "ET (toutes)"],
                        horizontal=True,
                        key=f"{filter_key}_operator",
                        disabled=st.session_state.interface_locked,
                    )
                    if selected:
                        if filter_mode == "Inclure la sélection":
                            if inner_operator.startswith("OU"):
                                multiselect_filter = ChromaFilterBuilder.in_list(
                                    field=filter_key, values=selected
                                )
                            else:
                                conditions = [
                                    ChromaFilterBuilder.eq(
                                        field=filter_key, value=value
                                    )
                                    for value in selected
                                ]
                                multiselect_filter = ChromaFilterBuilder.and_filter(
                                    conditions=conditions
                                )
                        else:  # Exclure
                            if inner_operator.startswith("OU"):
                                multiselect_filter = ChromaFilterBuilder.not_in_list(
                                    field=filter_key, values=selected
                                )
                            else:
                                conditions = [
                                    ChromaFilterBuilder.ne(
                                        field=filter_key, value=value
                                    )
                                    for value in selected
                                ]
                                multiselect_filter = ChromaFilterBuilder.and_filter(
                                    conditions=conditions
                                )
                        apply_filter(filter_key, multiselect_filter, is_strict)
                    else:
                        clear_filter(filter_key)

                elif filter_type == "selectbox":
                    options = get_dynamic_options(df, filter_key, st.session_state.active_filters)
                    display_options = [""] + options
                    selected = st.selectbox(
                        "Option unique",
                        options=display_options,
                        key=f"{filter_key}_select",
                        help="Sélectionnez une valeur unique.",
                        disabled=st.session_state.interface_locked
                    )
                    filter_mode = st.radio(
                        "Mode de filtre",
                        ["Égal à la sélection", "Différent de la sélection"],
                        horizontal=True,
                        key=f"{filter_key}_mode",
                        disabled=st.session_state.interface_locked,
                    )
                    if selected:
                        if filter_mode == "Égal à la sélection":
                            selectbox_filter = ChromaFilterBuilder.eq(
                                field=filter_key, value=selected
                            )
                        else:
                            selectbox_filter = ChromaFilterBuilder.ne(
                                field=filter_key, value=selected
                            )
                        apply_filter(filter_key, selectbox_filter, is_strict)
                    else:
                        clear_filter(filter_key)

                elif filter_type == "text":
                    text_value = st.text_input(
                        "Valeur texte",
                        key=f"{filter_key}_text",
                        help="Saisissez une valeur pour filtrer par texte.",
                        disabled=st.session_state.interface_locked
                    )
                    comparison_operator = st.selectbox(
                        "Opérateur",
                        ["Equals", "Not equals", "Contains", "Does not contain"],
                        key=f"{filter_key}_comparison",
                        disabled=st.session_state.interface_locked
                    )
                    if text_value:
                        if comparison_operator == "Equals":
                            text_filter = ChromaFilterBuilder.eq(
                                field=filter_key, value=text_value
                            )
                        elif comparison_operator == "Not equals":
                            text_filter = ChromaFilterBuilder.ne(
                                field=filter_key, value=text_value
                            )
                        elif comparison_operator == "Contains":
                            text_filter = {filter_key: {"$contains": text_value}}
                        elif comparison_operator == "Does not contain":
                            text_filter = {filter_key: {"$not_contains": text_value}}
                        apply_filter(filter_key, text_filter, is_strict)
                    else:
                        clear_filter(filter_key)

        # --- Recherche plein texte ---
        st.markdown("### 🔍 Recherche plein texte")
        with st.expander("Contient les termes…", expanded=False):
            # Affichage sous forme de badges, bouton suppression allégé (un bouton pour tout effacer)
            for i, term in enumerate(st.session_state.get("contains_terms", [])):
                st.markdown(f"<span class='sidebar-badge'>{term}</span>", unsafe_allow_html=True)
            if st.button("Vider tous les termes à contenir", key="clear_all_contains"):
                st.session_state.contains_terms = []
                st.rerun()
            new_contains = st.text_input("Ajouter un terme à contenir :", key="new_contains_term")
            if st.button("Ajouter", key="add_contains_term") and new_contains.strip():
                st.session_state.contains_terms.append(new_contains.strip())
                st.rerun()
            if len(st.session_state.contains_terms) > 1:
                st.radio(
                    "Combinaison des termes",
                    ["AND (tous présents)", "OR (au moins 1 présent)"],
                    key="contains_operator",
                    disabled=st.session_state.interface_locked
                )
        with st.expander("…Ne contient PAS les termes", expanded=False):
            for i, term in enumerate(st.session_state.get("not_contains_terms", [])):
                st.markdown(f"<span class='sidebar-badge'>{term}</span>", unsafe_allow_html=True)
            if st.button("Vider tous les termes à exclure", key="clear_all_not_contains"):
                st.session_state.not_contains_terms = []
                st.rerun()
            new_not_contains = st.text_input("Ajouter un terme à exclure :", key="new_not_contains_term")
            if st.button("Ajouter", key="add_not_contains_term") and new_not_contains.strip():
                st.session_state.not_contains_terms.append(new_not_contains.strip())
                st.rerun()
            if len(st.session_state.not_contains_terms) > 1:
                st.radio(
                    "Combinaison des termes",
                    ["AND (aucun ne doit être présent)", "OR (au moins 1 absent)"],
                    key="not_contains_operator",
                    disabled=st.session_state.interface_locked
                )
        if st.session_state.contains_terms and st.session_state.not_contains_terms:
            st.radio(
                "Combiner 'contient' et 'ne contient pas' :",
                ["AND (les deux conditions)", "OR (au moins une)"],
                key="doc_filter_top_operator",
                disabled=st.session_state.interface_locked
            )

        # Construit les filtres document/content
        build_document_filter()

        # Combine metadata filters
        if st.session_state.active_filters:
            combined_filters = list(st.session_state.active_filters.values())
            if len(combined_filters) > 1:
                if filter_grouping == "AND":
                    complex_filter = ChromaFilterBuilder.and_filter(
                        conditions=combined_filters
                    )
                else:
                    complex_filter = ChromaFilterBuilder.or_filter(
                        conditions=combined_filters
                    )
            else:
                complex_filter = combined_filters[0]
            st.session_state.metadata_filters = complex_filter
        else:
            st.session_state.metadata_filters = None

        # Résumé filtres actifs (badges)
        st.markdown("### 🧾 Filtres actifs")
        if st.session_state.get("active_filters"):
            st.markdown("**Métadonnées**")
            for k in st.session_state.active_filters:
                st.markdown(f"<span class='sidebar-badge'>{k}</span>", unsafe_allow_html=True)
        if st.session_state.get("contains_terms"):
            st.markdown("**Texte contient**")
            for t in st.session_state.contains_terms:
                st.markdown(f"<span class='sidebar-badge'>{t}</span>", unsafe_allow_html=True)
        if st.session_state.get("not_contains_terms"):
            st.markdown("**Texte exclut**")
            for t in st.session_state.not_contains_terms:
                st.markdown(f"<span class='sidebar-badge'>{t}</span>", unsafe_allow_html=True)
        if not (st.session_state.get("active_filters") or st.session_state.get("contains_terms") or st.session_state.get("not_contains_terms")):
            st.info("Aucun filtre actif.", icon="ℹ️")

        import json

        with st.expander("🛠️ Debug / JSON des filtres"):
            def render_json_block(title, data):
                st.markdown(f"**{title}**", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="
                        background-color: black;
                        color: white;
                        border: 2px solid #00205B;
                        border-radius: 8px;
                        padding: 15px;
                        margin-bottom: 15px;
                        font-family: 'Courier New', monospace;
                        white-space: pre-wrap;
                    ">
                        {json.dumps(data, indent=2)}
                    </div>
                """, unsafe_allow_html=True)

            render_json_block("🎯 metadata_filters", st.session_state.get("metadata_filters", {}))
            render_json_block("📄 where_document", st.session_state.get("where_document", {}))
            render_json_block("🧩 loose_filters", st.session_state.get("loose_filters", {}))



# Fonctions utilitaires
def apply_filter(filter_key, filter_value, is_strict):
    """Applique un filtre avec strict/loose."""
    if not is_strict:
        st.session_state.active_filters[filter_key] = ChromaFilterBuilder.or_filter(
            [filter_value, ChromaFilterBuilder.eq(field=filter_key, value="")]
        )
    else:
        st.session_state.active_filters[filter_key] = filter_value

def clear_filter(filter_key):
    """Nettoie un filtre si présent."""
    if filter_key in st.session_state.active_filters:
        del st.session_state.active_filters[filter_key]

def build_document_filter():
    """Construit le filtre document selon les termes de recherche."""
    contains_terms = st.session_state.get("contains_terms", [])
    not_contains_terms = st.session_state.get("not_contains_terms", [])

    if not contains_terms and not not_contains_terms:
        st.session_state.where_document = None
        return

    contains_filter = None
    if contains_terms:
        if len(contains_terms) == 1:
            contains_filter = {"$contains": contains_terms[0]}
        else:
            contains_operator = st.session_state.get(
                "contains_operator", "AND (tous présents)"
            )
            if contains_operator.startswith("AND"):
                contains_filter = {
                    "$and": [{"$contains": term} for term in contains_terms]
                }
            else:
                contains_filter = {
                    "$or": [{"$contains": term} for term in contains_terms]
                }
    not_contains_filter = None
    if not_contains_terms:
        if len(not_contains_terms) == 1:
            not_contains_filter = {"$not_contains": not_contains_terms[0]}
        else:
            not_contains_operator = st.session_state.get(
                "not_contains_operator", "AND (aucun ne doit être présent)"
            )
            if not_contains_operator.startswith("AND"):
                not_contains_filter = {
                    "$and": [{"$not_contains": term} for term in not_contains_terms]
                }
            else:
                not_contains_filter = {
                    "$or": [{"$not_contains": term} for term in not_contains_terms]
                }
    if contains_filter and not_contains_filter:
        doc_filter_top_operator = st.session_state.get(
            "doc_filter_top_operator", "AND (les deux conditions)"
        )
        if doc_filter_top_operator.startswith("AND"):
            st.session_state.where_document = {
                "$and": [contains_filter, not_contains_filter]
            }
        else:
            st.session_state.where_document = {
                "$or": [contains_filter, not_contains_filter]
            }
    elif contains_filter:
        st.session_state.where_document = contains_filter
    elif not_contains_filter:
        st.session_state.where_document = not_contains_filter
