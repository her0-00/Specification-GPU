import streamlit as st

from utils.chroma_filter_builder import ChromaFilterBuilder
from utils.config import load_config


def render_sidebar():
    """
    Render the sidebar with enhanced filter options and convert them into well formatted complex filters.
    """
    with st.sidebar:
        st.title("Options")
        st.header("Filters")

        # Load available filters from config
        config = st.session_state.get("config", load_config())
        st.session_state.config = config

        # Initialize active filters if not present
        if "active_filters" not in st.session_state:
            st.session_state.active_filters = {}

        if "loose_filters" not in st.session_state:
            st.session_state.loose_filters = {}

        if "document_filters" not in st.session_state:
            st.session_state.document_filters = {"contains": [], "not_contains": []}

        # Initialize session state variables for search terms if they don't exist
        if "contains_terms" not in st.session_state:
            st.session_state.contains_terms = []

        if "not_contains_terms" not in st.session_state:
            st.session_state.not_contains_terms = []

        # Initialize lock state for interface if not present
        if "interface_locked" not in st.session_state:
            st.session_state.interface_locked = False

        # MOVED METADATA FILTERS TO APPEAR FIRST
        # Add filter group options
        st.subheader("Metadata Filters")

        # Select filter grouping method at the top level
        filter_grouping = st.radio(
            "Filter grouping method",
            ["AND", "OR"],
            horizontal=True,
            key="filter_grouping",
            disabled=st.session_state.interface_locked,
        )

        # Render each filter based on its type
        for filter_def in config.get("available_filters", []):  # type: ignore
            filter_type = filter_def.get("type", "")
            filter_key = filter_def.get("key", "")
            filter_name = filter_def.get("name", filter_key)

            with st.expander(filter_name):
                # Add a toggle for strict/loose filtering for this filter
                is_strict = st.toggle(
                    "Strict filtering (exclude documents with missing values)",
                    value=True,
                    key=f"{filter_key}_strict",
                    disabled=st.session_state.interface_locked,
                )

                # Store the strict/loose preference
                st.session_state.loose_filters[filter_key] = not is_strict  # type: ignore

                if filter_type == "date_range":
                    # Set up a more flexible date range filter
                    date_filter_type = st.radio(
                        "Date filter type",
                        ["Range", "Before", "After", "Exact"],
                        horizontal=True,
                        key=f"{filter_key}_filter_type",
                        disabled=st.session_state.interface_locked,
                    )

                    # Initialize filter operators with defaults
                    operator_start = "$gte"
                    operator_end = "$lt"

                    if date_filter_type == "Range":
                        # Traditional range with two sides
                        col1, col2 = st.columns(2)
                        with col1:
                            start_date = st.date_input(
                                "From",
                                key=f"{filter_key}_start",
                                disabled=st.session_state.interface_locked,
                            )
                            include_start = st.checkbox(
                                "Include start date",
                                value=True,
                                key=f"{filter_key}_include_start",
                                disabled=st.session_state.interface_locked,
                            )
                            operator_start = "$gte" if include_start else "$gt"

                        with col2:
                            end_date = st.date_input(
                                "To",
                                key=f"{filter_key}_end",
                                disabled=st.session_state.interface_locked,
                            )
                            include_end = st.checkbox(
                                "Include end date",
                                value=False,
                                key=f"{filter_key}_include_end",
                                disabled=st.session_state.interface_locked,
                            )
                            operator_end = "$lte" if include_end else "$lt"

                        # Create filter if both dates are provided
                        if start_date and end_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                start_date=start_date,  # type: ignore
                                end_date=end_date,  # type: ignore
                                operator_start=operator_start,
                                operator_end=operator_end,
                            )

                            # Apply filter
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)

                    elif date_filter_type == "Before":
                        # One-sided before a date
                        end_date = st.date_input(
                            "Before date",
                            key=f"{filter_key}_before",
                            disabled=st.session_state.interface_locked,
                        )
                        include_end = st.checkbox(
                            "Include this date",
                            value=False,
                            key=f"{filter_key}_include_before",
                            disabled=st.session_state.interface_locked,
                        )
                        operator_end = "$lte" if include_end else "$lt"

                        if end_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                end_date=end_date,  # type: ignore
                                operator_end=operator_end,
                            )

                            # Apply filter
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)

                    elif date_filter_type == "After":
                        # One-sided after a date
                        start_date = st.date_input(
                            "After date",
                            key=f"{filter_key}_after",
                            disabled=st.session_state.interface_locked,
                        )
                        include_start = st.checkbox(
                            "Include this date",
                            value=True,
                            key=f"{filter_key}_include_after",
                            disabled=st.session_state.interface_locked,
                        )
                        operator_start = "$gte" if include_start else "$gt"

                        if start_date:
                            date_filter = ChromaFilterBuilder.date_range(
                                field=filter_key,
                                start_date=start_date,  # type: ignore
                                operator_start=operator_start,
                            )

                            # Apply filter
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)

                    elif date_filter_type == "Exact":
                        # Exact date match
                        exact_date = st.date_input(
                            "Exact date",
                            key=f"{filter_key}_exact",
                            disabled=st.session_state.interface_locked,
                        )

                        if exact_date:
                            # Format date as string for exact matching
                            date_str = exact_date.isoformat()  # type: ignore
                            date_filter = ChromaFilterBuilder.eq(
                                field=filter_key, value=date_str
                            )

                            # Apply filter
                            apply_filter(filter_key, date_filter, is_strict)
                        else:
                            clear_filter(filter_key)

                elif filter_type == "multiselect":
                    options = filter_def.get("options", [])
                    selected = st.multiselect(
                        "Select options",
                        options=options,
                        key=f"{filter_key}_select",
                        disabled=st.session_state.interface_locked,
                    )

                    # Determine if this is an inclusion or exclusion filter
                    filter_mode = st.radio(
                        "Filter mode",
                        ["Include selected", "Exclude selected"],
                        horizontal=True,
                        key=f"{filter_key}_mode",
                        disabled=st.session_state.interface_locked,
                    )

                    # Select operator for this specific filter
                    inner_operator = st.radio(
                        "Selection operator",
                        ["OR (any selected item)", "AND (all selected items)"],
                        horizontal=True,
                        key=f"{filter_key}_operator",
                        disabled=st.session_state.interface_locked,
                    )

                    if selected:
                        if filter_mode == "Include selected":
                            # Handle inclusion logic (as before)
                            if inner_operator.startswith("OR"):
                                # Use in_list for OR logic (any matching value)
                                multiselect_filter = ChromaFilterBuilder.in_list(
                                    field=filter_key, values=selected
                                )
                            else:
                                # Use AND logic (all values must match)
                                conditions = [
                                    ChromaFilterBuilder.eq(
                                        field=filter_key, value=value
                                    )
                                    for value in selected
                                ]
                                multiselect_filter = ChromaFilterBuilder.and_filter(
                                    conditions=conditions
                                )
                        else:  # "Exclude selected"
                            # Handle exclusion logic
                            if inner_operator.startswith("OR"):
                                # If OR: Document can match if ANY of the selected values is missing
                                # This is the same as NOT IN
                                multiselect_filter = ChromaFilterBuilder.not_in_list(
                                    field=filter_key, values=selected
                                )
                            else:
                                # If AND: Document must not match ANY of the selected values
                                # (all selected values must be absent)
                                conditions = [
                                    ChromaFilterBuilder.ne(
                                        field=filter_key, value=value
                                    )
                                    for value in selected
                                ]
                                multiselect_filter = ChromaFilterBuilder.and_filter(
                                    conditions=conditions
                                )

                        # Apply filter with strict/loose setting
                        apply_filter(filter_key, multiselect_filter, is_strict)
                    else:
                        clear_filter(filter_key)

                elif filter_type == "selectbox":
                    options = filter_def.get("options", [])

                    # Create a blank/empty option as the first option for no selection
                    display_options = [""] + options

                    selected = st.selectbox(
                        "Select an option",
                        options=display_options,
                        key=f"{filter_key}_select",
                        disabled=st.session_state.interface_locked,
                    )

                    # Add an option for not equal (exclusion)
                    filter_mode = st.radio(
                        "Filter mode",
                        ["Equal to selected", "Not equal to selected"],
                        horizontal=True,
                        key=f"{filter_key}_mode",
                        disabled=st.session_state.interface_locked,
                    )

                    if (
                        selected
                    ):  # Only apply filter if something is selected (not blank)
                        if filter_mode == "Equal to selected":
                            # Create equality filter for the selected value
                            selectbox_filter = ChromaFilterBuilder.eq(
                                field=filter_key, value=selected
                            )
                        else:  # "Not equal to selected"
                            # Create not-equal filter for the selected value
                            selectbox_filter = ChromaFilterBuilder.ne(
                                field=filter_key, value=selected
                            )

                        # Apply filter with strict/loose setting
                        apply_filter(filter_key, selectbox_filter, is_strict)
                    else:
                        clear_filter(filter_key)

                elif filter_type == "text":
                    text_value = st.text_input(
                        "Enter value",
                        key=f"{filter_key}_text",
                        disabled=st.session_state.interface_locked,
                    )

                    # Add comparison operators for text fields
                    comparison_operator = st.selectbox(
                        "Comparison operator",
                        ["Equals", "Not equals", "Contains", "Does not contain"],
                        key=f"{filter_key}_comparison",
                        disabled=st.session_state.interface_locked,
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
                            # For contains, we'll use $like if it's supported by ChromaDB
                            # If not, we can implement basic contains functionality
                            text_filter = {filter_key: {"$contains": text_value}}
                        elif comparison_operator == "Does not contain":
                            # For does not contain, we'll invert the contains logic
                            text_filter = {filter_key: {"$not_contains": text_value}}

                        # Apply filter with strict/loose setting
                        apply_filter(filter_key, text_filter, is_strict)  # type: ignore
                    else:
                        clear_filter(filter_key)

        # Create a section for full-text search
        st.subheader("Full-Text Search")

        # Create separate expanders for contains and not contains - set expanded=False
        with st.expander("Contains Terms", expanded=False):
            # Display current contains terms
            if st.session_state.contains_terms:  # type: ignore
                st.write("Current 'contains' search terms:")  # type: ignore
                for i, term in enumerate(st.session_state.contains_terms):  # type: ignore
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.text(f"• {term}")
                    with col2:
                        if st.button(
                            "✕",
                            key=f"remove_contains_{i}",
                            help="Remove term",
                            disabled=st.session_state.interface_locked,
                        ):
                            st.session_state.contains_terms.pop(i)  # type: ignore
                            st.rerun()

            # Add new contains term
            new_contains = st.text_input(
                "Add term that documents must contain:",
                key="new_contains_term",
                disabled=st.session_state.interface_locked,
            )
            if (
                st.button(
                    "Add Contains Term", disabled=st.session_state.interface_locked
                )
                and new_contains.strip()
            ):
                st.session_state.contains_terms.append(new_contains.strip())  # type: ignore
                st.rerun()

            # Choose operator for contains terms
            if len(st.session_state.contains_terms) > 1:  # type: ignore
                contains_operator = st.radio(  # type: ignore  # noqa: F841
                    "How to combine 'contains' terms:",
                    [
                        "AND (all terms must be present)",
                        "OR (any term must be present)",
                    ],
                    key="contains_operator",
                    disabled=st.session_state.interface_locked,
                )

        with st.expander("Does Not Contain Terms", expanded=False):
            # Display current not_contains terms
            if st.session_state.not_contains_terms:  # type: ignore
                st.write("Current 'does not contain' search terms:")  # type: ignore
                for i, term in enumerate(st.session_state.not_contains_terms):  # type: ignore
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.text(f"• {term}")
                    with col2:
                        if st.button(
                            "✕",
                            key=f"remove_not_contains_{i}",
                            help="Remove term",
                            disabled=st.session_state.interface_locked,
                        ):
                            st.session_state.not_contains_terms.pop(i)  # type: ignore
                            st.rerun()

            # Add new not_contains term
            new_not_contains = st.text_input(
                "Add term that documents must NOT contain:",
                key="new_not_contains_term",
                disabled=st.session_state.interface_locked,
            )
            if (
                st.button(
                    "Add 'Does Not Contain' Term",
                    disabled=st.session_state.interface_locked,
                )
                and new_not_contains.strip()
            ):
                st.session_state.not_contains_terms.append(new_not_contains.strip())  # type: ignore
                st.rerun()

            # Choose operator for not_contains terms
            if len(st.session_state.not_contains_terms) > 1:  # type: ignore
                not_contains_operator = st.radio(  # type: ignore  # noqa: F841
                    "How to combine 'does not contain' terms:",
                    [
                        "AND (none of these terms should be present)",
                        "OR (at least one term should be absent)",
                    ],
                    key="not_contains_operator",
                    disabled=st.session_state.interface_locked,
                )

        # Choose the top-level operator between contains and not_contains conditions
        if st.session_state.contains_terms and st.session_state.not_contains_terms:  # type: ignore
            doc_filter_top_operator = st.radio(  # type: ignore  # noqa: F841
                "How to combine 'contains' and 'does not contain' conditions:",
                [
                    "AND (both conditions must be satisfied)",
                    "OR (either condition must be satisfied)",
                ],
                key="doc_filter_top_operator",
                disabled=st.session_state.interface_locked,
            )

        # Build document filter based on selections
        build_document_filter()

        # Combine metadata filters based on grouping method
        if st.session_state.active_filters:  # type: ignore
            combined_filters = list(st.session_state.active_filters.values())  # type: ignore

            # Only use logical operators if we have multiple conditions
            if len(combined_filters) > 1:  # type: ignore
                if filter_grouping == "AND":
                    complex_filter = ChromaFilterBuilder.and_filter(
                        conditions=combined_filters  # type: ignore
                    )
                else:  # OR
                    complex_filter = ChromaFilterBuilder.or_filter(
                        conditions=combined_filters  # type: ignore
                    )
            else:
                # Just use the single filter directly
                complex_filter = combined_filters[0]  # type: ignore

            st.session_state.metadata_filters = complex_filter
        else:
            st.session_state.metadata_filters = None

        # Display active filters for debugging
        if st.checkbox(
            "Show active filters", disabled=st.session_state.interface_locked
        ):
            st.subheader("Metadata Filters")
            st.json(st.session_state.metadata_filters or {})  # type: ignore

            st.subheader("Document Content Filters")
            st.json(st.session_state.where_document or {})

            st.subheader("Loose Filters Settings")
            st.json(st.session_state.loose_filters or {})  # type: ignore


def apply_filter(filter_key, filter_value, is_strict):  # type: ignore
    """Helper function to apply a filter with strict/loose setting."""
    if not is_strict:
        # Allow documents with missing values
        st.session_state.active_filters[filter_key] = ChromaFilterBuilder.or_filter(
            [filter_value, ChromaFilterBuilder.eq(field=filter_key, value="")]  # type: ignore
        )
    else:
        st.session_state.active_filters[filter_key] = filter_value


def clear_filter(filter_key):  # type: ignore
    """Helper function to clear a filter if it exists."""
    if filter_key in st.session_state.active_filters:
        del st.session_state.active_filters[filter_key]


def build_document_filter():
    """
    Build the document filter based on the current search terms and operators.
    """
    contains_terms = st.session_state.get("contains_terms", [])
    not_contains_terms = st.session_state.get("not_contains_terms", [])

    # If no search terms are defined, clear the document filter
    if not contains_terms and not not_contains_terms:
        st.session_state.where_document = None
        return

    # Build contains filter
    contains_filter = None
    if contains_terms:
        if len(contains_terms) == 1:
            # Single term - simple contains
            contains_filter = {"$contains": contains_terms[0]}
        else:
            # Multiple terms - need to use operator
            contains_operator = st.session_state.get(
                "contains_operator", "AND (all terms must be present)"
            )
            if contains_operator.startswith("AND"):
                # AND logic - all terms must be present
                contains_filter = {
                    "$and": [{"$contains": term} for term in contains_terms]
                }
            else:
                # OR logic - any term can be present
                contains_filter = {
                    "$or": [{"$contains": term} for term in contains_terms]
                }

    # Build not_contains filter
    not_contains_filter = None
    if not_contains_terms:
        if len(not_contains_terms) == 1:
            # Single term - simple not_contains
            not_contains_filter = {"$not_contains": not_contains_terms[0]}
        else:
            # Multiple terms - need to use operator
            not_contains_operator = st.session_state.get(
                "not_contains_operator", "AND (none of these terms should be present)"
            )
            if not_contains_operator.startswith("AND"):
                # AND logic - all terms must be absent
                not_contains_filter = {
                    "$and": [{"$not_contains": term} for term in not_contains_terms]
                }
            else:
                # OR logic - at least one term should be absent
                not_contains_filter = {
                    "$or": [{"$not_contains": term} for term in not_contains_terms]
                }

    # Combine the two filters if both exist
    if contains_filter and not_contains_filter:
        doc_filter_top_operator = st.session_state.get(
            "doc_filter_top_operator", "AND (both conditions must be satisfied)"
        )

        if doc_filter_top_operator.startswith("AND"):
            # AND logic - both conditions must be met
            st.session_state.where_document = {
                "$and": [contains_filter, not_contains_filter]
            }
        else:
            # OR logic - either condition can be met
            st.session_state.where_document = {
                "$or": [contains_filter, not_contains_filter]
            }
    elif contains_filter:
        # Only contains filter exists
        st.session_state.where_document = contains_filter
    elif not_contains_filter:
        # Only not_contains filter exists
        st.session_state.where_document = not_contains_filter
