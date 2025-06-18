import ast
import time
import traceback

import pandas as pd
import streamlit as st

from utils.api import get_rag, query_llm, query_rag
from utils.grid_utils import create_and_display_grid


def is_non_empty(context):  # type: ignore
    """Helper function to check if the given context is non-empty."""
    if context is None:
        return False
    if isinstance(context, str):
        cleaned = context.strip().lower()
        return cleaned not in ["", "null", "none"]
    if isinstance(context, (dict, list)):
        return bool(context)  # type: ignore
    return True


def build_conversation(messages):  # type: ignore
    """Build the conversation list for the API call from session messages."""
    conversation = []
    for msg in messages:  # type: ignore
        if msg["role"] == "assistant":
            content = msg["content"].get("text", "")  # type: ignore
            if is_non_empty(msg["content"].get("context")):  # type: ignore
                content += f"\n ###Sources\n {msg['content']['context']}"  # type: ignore
            conversation.append({"role": msg["role"], "content": content})  # type: ignore
        elif msg["role"] == "user":
            conversation.append({"role": msg["role"], "content": msg["content"]})  # type: ignore
    return conversation  # type: ignore


def extract_context_data_and_llm(context_unified):  # type: ignore
    """
    Extract display context and LLM context from the unified context structure.

    Args:
        context_unified: Dictionary with the full context and usage flags

    Returns:
        Tuple of (context_data, context_llm)
    """
    if not context_unified:
        return None, None

    # Extract fields for display
    context_data = {}
    context_llm = {}

    for key, value in context_unified.items():  # type: ignore
        if isinstance(value, dict) and "data" in value and "usage" in value:
            # Add to context_data if flagged for display
            if value["usage"].get("display", False):  # type: ignore
                context_data[key] = value["data"]

            # Add to context_llm if flagged for LLM
            if value["usage"].get("llm", False):  # type: ignore
                context_llm[key] = value["data"]

    return context_data, context_llm  # type: ignore


def render_message_input():
    """
    Render the message input area with query type selection (only for the first question).
    This function handles user input, calls the appropriate API based on query type,
    and displays the response along with any document grids.
    """
    # Initialize session state if keys are missing
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("messages_llm", [])
    st.session_state.setdefault("interface_locked", False)

    # Inject JS to disable chat inputs if the interface is locked
    if st.session_state.get("interface_locked"):
        st.markdown(
            """
            <script>
                const disableInputs = () => {
                    const chatInputs = document.querySelectorAll('.stChatInput textarea, .stChatInput button');
                    if (chatInputs.length > 0) {
                        chatInputs.forEach(el => {
                            el.disabled = true;
                            if (el.tagName === 'TEXTAREA') {
                                el.style.backgroundColor = '#f0f0f0';
                                el.placeholder = 'Processing your request...';
                            }
                        });
                        return true;
                    }
                    return false;
                };
                if (!disableInputs()) {
                    const observer = new MutationObserver(() => {
                        if (disableInputs()) {
                            observer.disconnect();
                        }
                    });
                    observer.observe(document, { childList: true, subtree: true });
                }
            </script>
            """,
            unsafe_allow_html=True,
        )

    # Determine if this is the first message
    is_first_message = len(st.session_state["messages"]) == 0

    # Render the input form with query type selection if it's the first message
    if is_first_message:
        col1, col2 = st.columns([3, 1])
        with col2:
            query_type = st.selectbox(
                "Initial Query Type:",
                options=["Specific Question", "Exhaustive List"],
                index=0,
                disabled=st.session_state.get("interface_locked", False),
                help=(
                    "Specific Question: Get a targeted answer based on your query and filters. "
                    "Exhaustive List: Get all matching documents based on current filters only and reranked with your query."
                ),
            )
        st.session_state.current_query_type = query_type
        placeholder = (
            "Ask a specific question..."
            if query_type == "Specific Question"
            else "Add context for your exhaustive search..."
        )
        with col1:
            prompt = st.chat_input(
                placeholder, disabled=st.session_state.get("interface_locked", False)
            )
    else:
        query_type = "Follow-up"
        placeholder = "Ask a follow-up question..."
        prompt = st.chat_input(
            placeholder, disabled=st.session_state.get("interface_locked", False)
        )

    # Process the user input
    if prompt:
        if st.session_state.get("interface_locked"):
            st.warning("Please wait for the current query to complete.")
            st.stop()

        # Provide a default prompt for exhaustive search if empty
        if (
            is_first_message
            and query_type == "Exhaustive List"
            and prompt.strip() == ""
        ):
            prompt = "Show me all matching documents based on current filters"

        # Append the user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages_llm.append({"role": "user", "content": prompt})
        st.session_state.needs_processing = True
        st.session_state.query_to_process = prompt
        st.session_state.query_type_to_process = query_type
        st.session_state.interface_locked = True
        st.rerun()  # type: ignore

    # If a query needs processing, handle it
    if st.session_state.get("needs_processing", False):
        try:
            st.session_state.needs_processing = False
            prompt = st.session_state.query_to_process
            query_type = st.session_state.query_type_to_process
            st.session_state.processing_query = True

            with st.chat_message("assistant"):
                thinking_placeholder = st.empty()
                if query_type == "Exhaustive List":
                    thinking_message = "Searching for documents..."
                elif query_type == "Follow-up":
                    thinking_message = "Generating response..."
                else:
                    thinking_message = "Thinking..."
                thinking_placeholder.markdown(thinking_message)

                # Build the conversation for the API call
                conversation = build_conversation(st.session_state.messages_llm)  # type: ignore

                # Determine the type of query
                is_get_query = query_type == "Exhaustive List"
                is_rag_query = query_type == "Specific Question"
                response_data = None

                try:
                    if is_get_query:
                        with st.spinner("Retrieving all matching documents..."):
                            response_data = get_rag(
                                conversation=conversation,  # type: ignore
                                where_filter=st.session_state.get("metadata_filters"),
                                where_document_filter=st.session_state.get(
                                    "where_document"
                                ),
                            )
                    elif is_rag_query:
                        with st.spinner("Searching knowledge base..."):
                            response_data = query_rag(
                                conversation=conversation,  # type: ignore
                                n_results_embedder=50,
                                n_results_reranker=10,
                                where_filter=st.session_state.get("metadata_filters"),
                                where_document_filter=st.session_state.get(
                                    "where_document"
                                ),
                            )
                    else:
                        with st.spinner("Generating response..."):
                            response_data = query_llm(conversation=conversation)  # type: ignore

                    if not response_data:
                        response_data = {"error": "Empty response from API."}

                    if "error" in response_data:
                        assistant_response = f"Error: {response_data['error']}"
                        context_data = None
                        context_llm = None
                    else:
                        # Extract context_data and context_llm from context_unified
                        context_unified = response_data.get("context_unified", {})
                        context_data, context_llm = extract_context_data_and_llm(  # type: ignore
                            context_unified
                        )
                        if is_get_query:
                            doc_count = 0
                            if is_non_empty(context_data):
                                try:
                                    parsed_context = (  # type: ignore
                                        ast.literal_eval(context_data)
                                        if isinstance(context_data, str)
                                        else context_data
                                    )
                                    doc_count = len(
                                        pd.DataFrame.from_dict(parsed_context)  # type: ignore
                                    )
                                except (SyntaxError, ValueError) as e:
                                    thinking_placeholder.warning(
                                        f"Error parsing context data: {str(e)}"
                                    )
                                    traceback.print_exc()
                                    doc_count = 0
                            assistant_response = f"Found {doc_count} documents matching your current filters."
                            if doc_count == 0:
                                assistant_response += (
                                    " Try adjusting your filters to see more results."
                                )
                            elif doc_count > 20:
                                assistant_response += " Showing the top results below. You can refine your search using the filters in the sidebar."
                            else:
                                assistant_response += (
                                    " All matching documents are shown below."
                                )
                        elif is_rag_query:
                            assistant_response = response_data.get(
                                "answer", "No response received."
                            )
                        else:
                            assistant_response = response_data.get(
                                "content", "No response received."
                            )
                            context_data = None
                            context_llm = None

                    # Define a source indicator based on query type
                    if is_get_query:
                        source_indicator = (
                            '<div style="padding: 10px; border-radius: 5px; background-color: #f0f8ff; margin-bottom: 10px;">'
                            "<strong>📋 Exhaustive Document List:</strong> Showing all documents matching your current filters."
                            "</div>"
                        )
                    elif is_rag_query:
                        source_indicator = (
                            '<div style="padding: 10px; border-radius: 5px; background-color: #e6f3ff; margin-bottom: 10px;">'
                            "<strong>📚 Database-Augmented Response:</strong> This answer is based on information retrieved from the database: first using your filters and then matching similarity with your query."
                            "</div>"
                        )
                    else:
                        source_indicator = (
                            '<div style="padding: 10px; border-radius: 5px; background-color: #fff7e6; margin-bottom: 10px;">'
                            "<strong>🤖 LLM-Only Response:</strong> This answer is generated solely by the language model without database search, based on the current conversation's elements."
                            "</div>"
                        )
                    formatted_response = f"{source_indicator}\n\n{assistant_response}"
                    thinking_placeholder.markdown(
                        formatted_response, unsafe_allow_html=True
                    )

                    # Display document grid if context data exists
                    grid_key = None
                    if is_non_empty(context_data):
                        header = "Documents" if is_get_query else "Sources"
                        st.markdown(f"### {header}")
                        st.session_state.setdefault("grid_counter", 0)
                        st.session_state.grid_counter += 1
                        grid_key = f"input_{st.session_state.grid_counter}"
                        try:
                            create_and_display_grid(
                                context_data=context_data,  # type: ignore
                                key_suffix=grid_key,
                            )
                        except Exception as e:
                            st.error(f"Error displaying context table: {str(e)}")
                            st.exception(e)
                            traceback.print_exc()

                    # Prepare response content for storage
                    response_content = {  # type: ignore
                        "text": assistant_response,
                        "context": context_data if is_non_empty(context_data) else None,
                        "grid_key": grid_key,
                        "query_type": query_type,
                    }
                    response_content_llm = {  # type: ignore
                        "text": assistant_response,
                        "context": context_llm if is_non_empty(context_llm) else None,
                        "grid_key": grid_key,
                        "query_type": query_type,
                    }

                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_content}
                    )
                    st.session_state.messages_llm.append(
                        {"role": "assistant", "content": response_content_llm}
                    )

                except Exception as api_err:
                    error_message = (
                        f"An error occurred during processing: {str(api_err)}"
                    )
                    st.error(error_message)
                    st.exception(api_err)
                    traceback.print_exc()
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": {"text": error_message, "context": None},
                        }
                    )
                    st.session_state.messages_llm.append(
                        {
                            "role": "assistant",
                            "content": {"text": error_message, "context": None},
                        }
                    )

        except Exception as ex:
            st.error(f"Unexpected error during processing: {str(ex)}")
            st.exception(ex)
            traceback.print_exc()
        finally:
            time.sleep(0.5)
            st.session_state.interface_locked = False
            st.session_state.processing_query = False
            st.session_state.pop("query_to_process", None)
            st.session_state.pop("query_type_to_process", None)
            st.rerun()  # type: ignore
