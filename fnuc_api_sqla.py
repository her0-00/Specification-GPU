import traceback

import streamlit as st

from utils.grid_utils import create_and_display_grid
import pandas as pd 

def is_non_empty(context):  # type: ignore
    """
    Return True if context is a non-empty string (ignoring "null"/"none")
    or a non-empty dict/list.
    """
    if context is None:
        return False
    if isinstance(context, str):
        return context.strip().lower() not in ["", "null", "none"]
    if isinstance(context, (dict, list)):
        return bool(context)  # type: ignore
    return False


def render_assistant_message(message, index):  # type: ignore
    """
    Render an assistant message. If the message content is a dict, render the
    header based on query type, the text, and (if available) the associated context.
    """
    content = message.get("content", "")  # type: ignore

    if isinstance(content, dict):
        query_type = content.get("query_type", "Specific Question")  # type: ignore

        # Set the header based on the query type
        if query_type == "Exhaustive List":
            header_html = """
            <div style="padding: 10px; border-radius: 5px; background-color: #f0f8ff; margin-bottom: 10px;">
                <strong>📋 Exhaustive Document List:</strong> Showing all documents matching your current filters.
            </div>
            """
        elif query_type == "Specific Question":
            header_html = """
            <div style="padding: 10px; border-radius: 5px; background-color: #e6f3ff; margin-bottom: 10px;">
                <strong>📚 Database-Augmented Response:</strong> This answer is based on information retrieved from the database: first using your filters and then matching similarity with your query.
            </div>
            """
        elif query_type == "Follow-up":
            header_html = """
            <div style="padding: 10px; border-radius: 5px; background-color: #fff7e6; margin-bottom: 10px;">
                <strong>🤖 LLM-Only Response:</strong> This answer is generated solely by the language model without database search, based on the current conversation's elements.
            </div>
            """
        else:
            header_html = ""

        st.markdown(header_html, unsafe_allow_html=True)
        st.markdown(content.get("text", ""))  # type: ignore

        # Retrieve context data and grid key if available
        context_data = content.get("context")  # type: ignore
        grid_key = content.get("grid_key")  # type: ignore

        # Render the grid if context exists and we're not processing a new query
        if is_non_empty(context_data) and not st.session_state.get(
            "processing_query", False
        ):
            header = "Documents" if query_type == "Exhaustive List" else "Sources"
            st.markdown(f"### {header}")
            try:
                key_to_use = grid_key if grid_key else f"conv_{index}"  # type: ignore
                create_and_display_grid(
                    context_data=context_data,  # type: ignore
                    key_suffix=key_to_use,  # type: ignore
                )  # type: ignore
            except Exception as grid_err:
                st.error(f"Error displaying context table: {grid_err}")
                st.exception(grid_err)
                st.text(traceback.format_exc())
                st.text("Context data:")
                st.text(context_data)  # type: ignore
    else:
        # For old-format messages (plain strings)
        st.markdown(content)  # type: ignore

def load_jsonl_to_dataframe(jsonl_path):
    try:
        df = pd.read_json(jsonl_path, lines=True)
        return df
    except Exception as e:
        print(f"Erreur lors du chargement du fichier : {e}")
        return None

def convert_timestamps_to_iso(df, columns):
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], unit='ms').dt.strftime('%Y-%m-%dT%H:%M:%S')
    return df


def afficher_dataframe_dataset():
    dataset_path = "..//..//data//processed//dataset.jsonl" # Appel direct à ta fonction
    df = convert_timestamps_to_iso(load_jsonl_to_dataframe(dataset_path),['Date de creation', 'Date de cloture'])
    if df is not None:
        st.dataframe(df)


def render_conversation():
    """
    Render the conversation history from st.session_state.messages.
    """
    conversation_container = st.container()

    with conversation_container:
        for idx, message in enumerate(st.session_state.get("messages", [])):
            try:
                role = message.get("role", "")
                if role == "user":
                    st.chat_message("user").write(message.get("content", ""))  # type: ignore
                elif role == "assistant":
                    with st.chat_message("assistant"):
                        render_assistant_message(message, idx)
            except Exception as render_err:
                st.error(f"Error rendering message: {render_err}")
                st.exception(render_err)
                st.text(traceback.format_exc())


def clear_conversation():
    """
    Clear the conversation history and reset session state.
    """
    st.session_state.messages = []
    st.session_state.messages_llm = []
    st.session_state.interface_locked = False
    st.session_state.processing_query = False
    st.session_state.current_query_type = "Specific Question"
    st.rerun()  # type: ignore
