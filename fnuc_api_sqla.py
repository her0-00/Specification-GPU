import ast
import base64
import json
from io import BytesIO
from typing import Any, Dict

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from st_aggrid import (
    AgGrid,  # type: ignore
    DataReturnMode,
    GridOptionsBuilder,
    GridUpdateMode 
)





def convert_timestamps_to_iso(df):
        for column in df.columns:
            if "Date" in column:
                df[column] = pd.to_datetime(df[column], unit='ms').dt.strftime('%Y-%m-%d')
        return df

def create_and_display_grid(
    context_data: str,
    key_suffix: str,
    min_height: int = 400,
    max_height: int = 400,
    page_size: int = 20,
    content_col_name: str = "Content",
    font_size: int = 9,
) -> Dict[str, Any]:
    """
    Creates and displays an AgGrid with the given data and a single CSV export button.
    Handles text content properly for CSV export. Uses Streamlit expanders.
    for displaying table_dict and image_array data.

    Args:
        context_data: String representation of a dictionary (or a dictionary) to be converted to DataFrame.
        key_suffix: Suffix for the unique key to identify this grid.
        min_height: Minimum height of the grid in pixels.
        max_height: Maximum height of the grid in pixels.
        page_size: Number of rows per page.
        content_col_name: Name of the content column to make wider.
        font_size: Size of the text in the table cells (in pixels).

    Returns:
        The response from AgGrid which contains filtered and sorted data, or an empty dict if no valid data.
    """
    # Check if context_data is empty or represents a null value.
    if not context_data or (
        isinstance(context_data, str)  # type: ignore
        and context_data.strip().lower() in ["", "null", "none"]
    ):
        st.markdown("No data to display.")
        return {}

    # Evaluate context_data if it's a string
    try:
        if isinstance(context_data, str):  # type: ignore
            # Try json.loads first, with proper quote handling
            try:
                cleaned_data = context_data.replace("'", '"')
                data = json.loads(cleaned_data)
            except json.JSONDecodeError:
                # Fall back to ast.literal_eval
                data = ast.literal_eval(context_data)
        else:
            data = context_data
    except Exception as e:
        st.error(f"Error evaluating context_data: {e}")
        st.error(
            f"Raw data: {context_data[:200]}..."
            if isinstance(context_data, str)  # type: ignore
            else "Non-string data"
        )
        return {}

    # Create DataFrame from data dictionary
    try:
        df = pd.DataFrame.from_dict(data)  # type: ignore
        try :
            df = convert_timestamps_to_iso(df)
        except :
            pass 
        try :
            # Conversion de relevance_score en pourcentage
            if 'relevance_score' in df.columns:
                df['relevance_score'] = (df['relevance_score'].astype(float) * 100).round(2).astype(str) + '%'
        except :
               pass
        # Colonnes fixes dans l’ordre souhaité
        fixed_order = [
            'Code DA',
            'Operateur responsable',
            'relevance_score',
            'Similarité',
            'Code article',
            'Libelle article'
        ]

        # Colonnes restantes triées par nom
        remaining_cols = sorted([col for col in df.columns if col not in fixed_order])
        if 'relevance_score' in df.columns and (df['relevance_score'] == '').any():
            cols = list(df.columns)
            cols.remove("relevance_score")
            df = df[cols]


        # Ordre final
        final_order = fixed_order + remaining_cols

        # Réorganisation du DataFrame
        df = df[[col for col in final_order if col in df.columns]]
    except Exception as e:
        st.error(f"Error creating DataFrame: {e}")
        st.json(data)  # Display the data structure for debugging
        return {}

    # Process metadata columns: track table_dict and image_array
    has_table_dict = "table_dict" in df.columns
    has_image_array = "image_array" in df.columns

    # Add row index for tracking selected rows
    df["_row_index"] = range(len(df))

    # Create the main display container
    grid_container = st.container()

    with grid_container:
        # Create separate columns for the grid and metadata display
        grid_col, details_col = st.columns([40, 1])

        with grid_col:
            # Configure dynamic height based on data size
            row_count = len(df)
            estimated_height = min(max(row_count * 60 + 100, min_height), max_height)
            if row_count > page_size:
                visible_rows = min(page_size, row_count)
                estimated_height = min(visible_rows * 60 + 100, max_height)

            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df)  # type: ignore
                       
               
          
            # Fonction pour créer une barre de progression textuelle
            def render_bar(val, length=10):
                try:
                    val = float(val.strip('%')) / 100  # Convertir "85%" → 0.85
                except:
                    return "░" * length
                filled = int(val * length)
                empty = length - filled
                return "█" * filled + "░" * empty

            # Appliquer la barre de progression dans une nouvelle colonne
            try:
                df['Similarité'] = df['relevance_score'].apply(render_bar)
                # Réorganiser les colonnes pour placer 'Similarité' en 3ᵉ position
                cols = list(df.columns)
                if 'Similarité' in cols:
                    cols.remove('Similarité')
                    cols.insert(2, 'Similarité')
                    df = df[cols]
            except Exception as e:
                print("Erreur lors de la génération de la barre :", e)



            gb.configure_pagination(  # type: ignore
                paginationAutoPageSize=False, paginationPageSize=page_size
            )

            # Define cell style
            cell_style = {
                "font-size": f"{font_size}px",
                "line-height": f"{int(font_size * 1.2)}px",
                "padding": "4px",
            }

            # Configure selection
            gb.configure_selection("single", use_checkbox=True)  # type: ignore

            # Hide metadata columns
            if has_table_dict:
                gb.configure_column("table_dict", hide=True)  # type: ignore
            if has_image_array:
                gb.configure_column("image_array", hide=True)  # type: ignore

            # Hide row index
            gb.configure_column("_row_index", hide=True)  # type: ignore

            # Configure columns
            for col in df.columns:
                if col in ["table_dict", "image_array", "_row_index"]:
                    continue  # Already configured above
                elif col == content_col_name:
                    gb.configure_column(  # type: ignore
                        col,
                        minWidth=250,
                        maxWidth=1000,
                        flex=1,
                        wrapText=True,
                        autoHeight=True,
                        cellStyle=cell_style,
                        filter=True,
                    )
                else:
                    avg_length = df[col].astype(str).apply(len).mean()  # type: ignore
                    if avg_length < 15:
                        gb.configure_column(  # type: ignore
                            col,
                            minWidth=80,
                            maxWidth=150,
                            flex=0.5,
                            autoSizeColumn=True,
                            cellStyle=cell_style,
                            filter=True,
                        )
                    elif avg_length < 50:
                        gb.configure_column(  # type: ignore
                            col,
                            minWidth=120,
                            maxWidth=300,
                            flex=0.8,
                            wrapText=True,
                            cellStyle=cell_style,
                            filter=True,
                        )
                    else:
                        gb.configure_column(  # type: ignore
                            col,
                            minWidth=150,
                            maxWidth=500,
                            flex=0.9,
                            wrapText=True,
                            autoHeight=True,
                            cellStyle=cell_style,
                            filter=True,
                        )

            # Custom CSS for header styling
            custom_css = {
                ".header-style": {"font-size": f"{font_size}px", "font-weight": "bold"}
            }

            # Configure grid options
            gb.configure_grid_options(  # type: ignore
                domLayout="normal",
                rowHeight=int(font_size * 3.5),
                autoSizeColumns=True,
                suppressColumnVirtualisation=False,
                headerHeight=int(font_size * 2),
                defaultColDef={"cellStyle": cell_style, "headerClass": "header-style"},
                enableFilter=True,
            )

            # Configure default column properties
            gb.configure_default_column(  # type: ignore
                editable=False,
                groupable=True,
                sortable=True,
                filterable=True,
                resizable=True,
            )
            
          
            # Build grid options
            grid_options = gb.build()  # type: ignore

            # Create a unique key for the grid
            grid_key = f"grid_{key_suffix}"

            # Create the grid
            grid_response = AgGrid(
                df,
                gridOptions=grid_options,  # type: ignore
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED
                | GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True,
                theme="streamlit",
                enable_enterprise_modules=False,
                height=estimated_height,
                custom_css=custom_css,
                key=grid_key,
                allow_unsafe_jscode=True,
            )

            # Get the filtered data for CSV export
            filtered_data = grid_response["data"]  # type: ignore
            filtered_df = pd.DataFrame(filtered_data)  # type: ignore

            # Remove internal columns before export
            if "_row_index" in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=["_row_index"])

            # Create CSV with proper quoting for text content
            csv = filtered_df.to_csv(
                index=False,
                quoting=2,  # QUOTE_NONNUMERIC: quote all non-numeric fields
                quotechar='"',
                sep=";",
            ).encode()

            b64 = base64.b64encode(csv).decode()
            href = (
                f'<a href="data:file/csv;base64,{b64}" download="exported_data.csv" '
                f'class="download-button">Export to CSV</a>'
            )

            st.markdown(
            """
            <style>
            .download-button {
                display: inline-block;
                padding: 0.5em 1em;
                margin-top: 10px;
                color: white;
                background-color: #FF6A13; /* Orange Safran */
                border-radius: 0.25rem;
                text-decoration: none;
                font-weight: bold;
                text-align: center;
            }
            .download-button:hover {
                background-color: #e65c00;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


            st.markdown(href, unsafe_allow_html=True)

        # Create a container for the details panel that now only shows metadata expanders
        with details_col:
            selected_rows = grid_response.get("selected_rows", None)  # type: ignore
            if selected_rows is not None and len(selected_rows) > 0:  # type: ignore
                selected_row = selected_rows.iloc[0]  # type: ignore # Get the first selected row
                row_index = selected_row.get("_row_index")  # type: ignore
                if row_index is not None:
                    row_index = int(row_index)  # type: ignore # Ensure it's an integer

                    # Show table metadata if available
                    if (
                        has_table_dict
                        and 0 <= row_index < len(df)
                        and pd.notna(df.loc[row_index, "table_dict"])
                        and df.loc[row_index, "table_dict"] != ""
                    ):
                        with st.expander("View Table Data", expanded=False):
                            try:
                                table_dict_str = df.loc[row_index, "table_dict"]
                                if isinstance(table_dict_str, str):
                                    try:
                                        table_dict_str = table_dict_str.replace(
                                            "'", '"'
                                        )
                                        table_data = json.loads(table_dict_str)
                                    except json.JSONDecodeError:
                                        table_data = ast.literal_eval(table_dict_str)
                                else:
                                    table_data = table_dict_str
                                try:
                                    table_df = pd.DataFrame(table_data)  # type: ignore
                                    st.dataframe(table_df, use_container_width=True)  # type: ignore
                                except Exception as df_err:
                                    st.warning(
                                        f"Could not convert to DataFrame: {df_err}"
                                    )
                                    st.json(table_data)
                            except Exception as e:
                                st.error(f"Error processing table data: {e}")
                                st.code(str(df.loc[row_index, "table_dict"])[:500])

                    # Show image metadata if available
                    if (
                        has_image_array
                        and 0 <= row_index < len(df)
                        and pd.notna(df.loc[row_index, "image_array"])
                        and df.loc[row_index, "image_array"] != ""
                    ):
                        with st.expander("View Image", expanded=False):
                            try:
                                image_data = df.loc[row_index, "image_array"]
                                if isinstance(image_data, str):
                                    try:
                                        image_data = image_data.replace("'", '"')
                                        image_array = json.loads(image_data)
                                        st.image(np.array(image_array))
                                    except json.JSONDecodeError:
                                        try:
                                            image_bytes = base64.b64decode(image_data)
                                            image = Image.open(BytesIO(image_bytes))
                                            st.image(image)
                                        except Exception as img_err:
                                            st.warning(
                                                f"Could not parse image data: {img_err}"
                                            )
                                            st.code(image_data[:500])
                                elif isinstance(image_data, (list, np.ndarray)):
                                    st.image(np.array(image_data))
                                else:
                                    st.warning(
                                        f"Unsupported image data format: {type(image_data)}"
                                    )
                            except Exception as e:
                                st.error(f"Error displaying image: {e}")
                                st.code(str(df.loc[row_index, "image_array"])[:500])
            # If no row is selected or no metadata exists, nothing is displayed in this panel

    return grid_response  # type: ignore
