import streamlit as st
from utils.chroma_filter_builder import ChromaFilterBuilder
from utils.config import load_config
import pandas as pd
import json

@st.cache_data
def get_config():
    return load_config()

@st.cache_data
def load_full_data():
    return pd.read_json("..//..//data//processed//dataset.jsonl", lines=True)

def get_linked_options(df, filter_key, active_filters, current_selection):
    filtered_df = df.copy()
    for k, v in active_filters.items():
        if k == filter_key or not v:
            continue
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
        elif isinstance(v, list):
            filtered_df = filtered_df[filtered_df[k].isin(v)]
        else:
            filtered_df = filtered_df[filtered_df[k] == v]
    options = set(filtered_df[filter_key].dropna().unique())
    options.update(current_selection)
    return sorted(options)

def render_horizontal_filters():
  
    if "config" not in st.session_state:
        st.session_state.config = get_config()
    config = st.session_state.config
    if st.toggle("##### 🛠️ Filtres disponibles", value=False):
        col1, col2 = st.columns([2, 3])
        # Colonnes avec alignement vertical centré
        if "active_filters" not in st.session_state:
            st.session_state.active_filters = {}

        if st.toggle("#### Retouche existante", key="da_not_null_btn", value=False):
            da_not_null_filter = ChromaFilterBuilder.is_not_null(field="Code DA_DER")
            st.session_state.active_filters["Code DA_DER"] = da_not_null_filter
        else:
            st.session_state.active_filters.pop("Code DA_DER", None)
        with col1:
            st.markdown(
                "<div style='display: flex; align-items: center; height: 100%;'>"
                "<span style='font-weight: 600; font-size: 16px;'>Méthode de regroupement</span>"
                "</div>",
                unsafe_allow_html=True
            )

        with col2:
            filter_grouping = st.radio(
                label="",
                options=["AND", "OR"],
                horizontal=True,
                key="filter_grouping",
                disabled=st.session_state.get("interface_locked", False)
            )
        

        for k, v in [
            ("active_filters", {}),
            ("loose_filters", {}),
            ("document_filters", {"contains": [], "not_contains": []}),
            ("contains_terms", []),
            ("not_contains_terms", []),
            ("interface_locked", False)
        ]:
            st.session_state.setdefault(k, v)

        df = load_full_data()
        filter_defs = config.get("available_filters", [])
        n_cols = min(5, len(filter_defs)) or 1
        cols = st.columns(n_cols)


        # Filtres horizontaux dans expanders
        for i, filter_def in enumerate(filter_defs):
            filter_type = filter_def.get("type", "")
            filter_key = filter_def.get("key", "")
            filter_name = filter_def.get("name", filter_key)
            with cols[i % n_cols]:
                with st.expander(filter_name, expanded=False):  # Rabattu par défaut
                    is_strict = st.toggle(
                        "Strict",
                        value=True,
                        key=f"{filter_key}_strict",
                        help="Si désactivé, les documents sans cette valeur seront inclus.",
                        disabled=st.session_state.interface_locked
                    )
                    st.session_state.loose_filters[filter_key] = not is_strict

                    if filter_type == "date_range":
                        filter_enabled = st.toggle(
                            "Activer",
                            value=False,
                            key=f"{filter_key}_enabled",
                            disabled=st.session_state.interface_locked
                        )
                        if not filter_enabled:
                            clear_filter(filter_key)
                            continue
                        date_filter_type = st.radio(
                            "Type",
                            ["Range", "Before", "After", "Exact"],
                            horizontal=True,
                            key=f"{filter_key}_filter_type",
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
                                    "Inclure",
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
                                    "Inclure",
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
                                "Avant",
                                key=f"{filter_key}_before",
                                disabled=st.session_state.interface_locked,
                            )
                            include_end = st.checkbox(
                                "Inclure",
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
                                "Après",
                                key=f"{filter_key}_after",
                                disabled=st.session_state.interface_locked,
                            )
                            include_start = st.checkbox(
                                "Inclure",
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
                        current_selection = st.session_state.get(f"{filter_key}_select", [])
                        options = get_linked_options(df, filter_key, st.session_state.active_filters, current_selection)
                        selected = st.multiselect(
                            "",
                            options=options,
                            default=current_selection,
                            key=f"{filter_key}_select",
                            disabled=st.session_state.interface_locked
                        )
                        filter_mode = st.radio(
                            "Mode",
                            ["Inclure", "Exclure"],
                            horizontal=True,
                            key=f"{filter_key}_mode",
                            disabled=st.session_state.interface_locked,
                        )
                        inner_operator = st.radio(
                            "Opérateur",
                            ["OU", "ET"],
                            horizontal=True,
                            key=f"{filter_key}_operator",
                            disabled=st.session_state.interface_locked,
                        )
                        if selected:
                            if filter_mode == "Inclure":
                                if inner_operator == "OU":
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
                                if inner_operator == "OU":
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
                        current_selection = st.session_state.get(f"{filter_key}_select", "")
                        options = get_linked_options(df, filter_key, st.session_state.active_filters, [current_selection] if current_selection else [])
                        display_options = [""] + options
                        selected = st.selectbox(
                            "",
                            options=display_options,
                            index=display_options.index(current_selection) if current_selection in display_options else 0,
                            key=f"{filter_key}_select",
                            disabled=st.session_state.interface_locked
                        )
                        filter_mode = st.radio(
                            "Mode",
                            ["Égal", "Différent"],
                            horizontal=True,
                            key=f"{filter_key}_mode",
                            disabled=st.session_state.interface_locked,
                        )
                        if selected:
                            if filter_mode == "Égal":
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
                            "",
                            key=f"{filter_key}_text",
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

        # Recherche plein texte en expander rabattable
        with st.expander("🔍 Recherche plein texte", expanded=False):
            colA, colB = st.columns(2)
            with colA:
                st.write("Contient :")
                for term in st.session_state.get("contains_terms", []):
                    st.markdown(f"<span style='background:#FF6A13;color:white;padding:2px 8px;border-radius:10px;margin-right:2px'>{term}</span>", unsafe_allow_html=True)
                if st.button("Vider", key="clear_all_contains"):
                    st.session_state.contains_terms = []
                    st.rerun()
                new_contains = st.text_input("Ajouter à contenir", key="new_contains_term")
                if st.button("Ajouter", key="add_contains_term") and new_contains.strip():
                    st.session_state.contains_terms.append(new_contains.strip())
                    st.rerun()
            with colB:
                st.write("Ne contient PAS :")
                for term in st.session_state.get("not_contains_terms", []):
                    st.markdown(f"<span style='background:#FF6A13;color:white;padding:2px 8px;border-radius:10px;margin-right:2px'>{term}</span>", unsafe_allow_html=True)
                if st.button("Vider", key="clear_all_not_contains"):
                    st.session_state.not_contains_terms = []
                    st.rerun()
                new_not_contains = st.text_input("Ajouter à exclure", key="new_not_contains_term")
                if st.button("Ajouter", key="add_not_contains_term") and new_not_contains.strip():
                    st.session_state.not_contains_terms.append(new_not_contains.strip())
                    st.rerun()

        build_document_filter()

        # -- Combine metadata filters --
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

       

        # if st.button("♻️ Réinitialiser tous les filtres", key="reset_all", help="Enlève tous les filtres actifs", type="primary"):
            # for k in [
                # "active_filters", "loose_filters",
                # "document_filters", "contains_terms",
                # "not_contains_terms", "where_document", "metadata_filters"
            # ]:
                # if k in st.session_state:
                    # if isinstance(st.session_state[k], dict):
                        # st.session_state[k].clear()
                    # elif isinstance(st.session_state[k], list):
                        # st.session_state[k].clear()
                    # else:
                        # del st.session_state[k]
            # st.rerun()

   


def apply_filter(filter_key, filter_value, is_strict):
    if not is_strict:
        st.session_state.active_filters[filter_key] = ChromaFilterBuilder.or_filter(
            [filter_value, ChromaFilterBuilder.eq(field=filter_key, value="")]
        )
    else:
        st.session_state.active_filters[filter_key] = filter_value

def clear_filter(filter_key):
    if filter_key in st.session_state.active_filters:
        del st.session_state.active_filters[filter_key]

def build_document_filter():
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
