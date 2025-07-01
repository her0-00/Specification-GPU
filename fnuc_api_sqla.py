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
    AgGrid,
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
    if not context_data or (
        isinstance(context_data, str)
        and context_data.strip().lower() in ["", "null", "none"]
    ):
        st.markdown("No data to display.")
        return {}

    try:
        if isinstance(context_data, str):
            try:
                cleaned_data = context_data.replace("'", '"')
                data = json.loads(cleaned_data)
            except Exception:
                data = ast.literal_eval(context_data)
        else:
            data = context_data
    except Exception as e:
        st.error(f"Error evaluating context_data: {e}")
        st.error(
            f"Raw data: {context_data[:200]}..."
            if isinstance(context_data, str)
            else "Non-string data"
        )
        return {}

    try:
        df = pd.DataFrame.from_dict(data)
        try:
            df = convert_timestamps_to_iso(df)
        except Exception:
            pass
        try:
            if 'relevance_score' in df.columns:
                df['relevance_score'] = (df['relevance_score'].astype(float) * 100).round(2).astype(str) + '%'
        except Exception:
            pass
        fixed_order = [
            'Code DA',
            'Operateur responsable',
            'relevance_score',
            'Similarité',
            'Code article',
            'Libelle article',
            'Content'
        ]
        remaining_cols = sorted([col for col in df.columns if col not in fixed_order])
        if 'relevance_score' in df.columns and (df['relevance_score'] == '').any():
            cols = list(df.columns)
            cols.remove("relevance_score")
            df = df[cols]
        final_order = fixed_order + remaining_cols
        df = df[[col for col in final_order if col in df.columns]]
    except Exception as e:
        st.error(f"Error creating DataFrame: {e}")
        st.json(data)
        return {}

    has_table_dict = "table_dict" in df.columns
    has_image_array = "image_array" in df.columns
    df["_row_index"] = range(len(df))

    grid_container = st.container()

    with grid_container:
        grid_col, details_col = st.columns([40, 1])
        with grid_col:
            row_count = len(df)
            estimated_height = min(max(row_count * 60 + 100, min_height), max_height)
            if row_count > page_size:
                visible_rows = min(page_size, row_count)
                estimated_height = min(visible_rows * 60 + 100, max_height)
                
                      
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
                    cols.insert(3, 'Similarité')
                    df = df[cols]
            except Exception as e:
                print("Erreur lors de la génération de la barre :", e)



            gb = GridOptionsBuilder.from_dataframe(df)

            cell_style = {
                "font-size": f"{font_size}px",
                "line-height": f"{int(font_size * 1.2)}px",
                "padding": "4px",
            }

            gb.configure_selection("single", use_checkbox=True)
            if has_table_dict:
                gb.configure_column("table_dict", hide=True)
            if has_image_array:
                gb.configure_column("image_array", hide=True)
            gb.configure_column("_row_index", hide=True)

            for col in df.columns:
                if col in ["table_dict", "image_array", "_row_index"]:
                    continue
                elif col == "relevance_score":
                    gb.configure_column(
                        col,
                        autoSizeColumn=True,
                        minWidth=80,
                        maxWidth=150,
                        cellRenderer="""
                            function(params) {
                                const val = params.value || '';
                                let score = 0;
                                if(val.includes('%')) {score = parseFloat(val.replace('%',''));}
                                else {score = parseFloat(val);}
                                let color = '#ff4136';
                                if(score >= 70) color = '#2ecc40';
                                else if(score >= 40) color = '#ffae42';
                                return `<span style='font-size:18px; color:${color}; vertical-align:middle;'>●</span>
                                        <span style='color:${color}; font-weight:bold;'>${val}</span>`;
                            }
                        """,
                        filter=True,
                        cellStyle={"fontWeight": "bold", "fontSize": "13px"}
                    )
                elif col == "Similarité":
                    gb.configure_column(
                        col,
                        autoSizeColumn=True,
                        minWidth=80,
                        maxWidth=150,
                        cellStyle={"fontWeight": "bold", "color": "#3f51b5", "fontSize": "12px"},
                        filter=True
                    )
                elif col in ["Code DA", "Operateur responsable","Code article","Libelle article",]:
                    gb.configure_column(
                        col,
                        minWidth=150,
                        maxWidth=200,
                        autoSizeColumn=True,
                        cellStyle={"fontWeight": "bold", "fontSize": "11.5px"},
                        filter=True
                    )
                elif col == content_col_name:
                    gb.configure_column(
                        col,
                        autoSizeColumn=True,
                        minWidth=250,
                        maxWidth=1000,
                        flex=1,
                        wrapText=True,
                        autoHeight=True,
                        cellStyle=cell_style,
                        filter=True,
                    )
                else:
                    avg_length = df[col].astype(str).apply(len).mean()
                    if avg_length < 15:
                        gb.configure_column(
                            col,
                            autoSizeColumn=True,
                            minWidth=80,
                            maxWidth=150,
                            flex=0.5,
                            cellStyle=cell_style,
                            filter=True,
                        )
                    elif avg_length < 50:
                        gb.configure_column(
                            col,
                            autoSizeColumn=True,
                            minWidth=120,
                            maxWidth=300,
                            flex=0.8,
                            wrapText=True,
                            cellStyle=cell_style,
                            filter=True,
                        )
                    else:
                        gb.configure_column(
                            col,
                            autoSizeColumn=True,
                            minWidth=150,
                            maxWidth=500,
                            flex=0.9,
                            wrapText=True,
                            autoHeight=True,
                            cellStyle=cell_style,
                            filter=True,
                        )

            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "color": "#FF6A13",
                    "font-size": f"{font_size+2}px"
                }
            }

            gb.configure_grid_options(
                domLayout="normal",
                rowHeight=int(font_size * 3.5),
                autoSizeColumns=True,
                suppressColumnVirtualisation=False,
                suppressSizeToFit=False,
                headerHeight=int(font_size * 2),
                defaultColDef={"cellStyle": cell_style},
                enableFilter=True,
                minWidth=80,
                maxWidth=150
            )
            gb.configure_default_column(
                editable=False,
                groupable=True,
                sortable=True,
                filterable=True,
                resizable=True,
                autoSizeColumn=True,
                minWidth=80,
                maxWidth=150
            )

            grid_options = gb.build()
            grid_key = f"grid_{key_suffix}"

            grid_response = AgGrid(
                df,
                gridOptions=grid_options,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True,
                theme="streamlit",
                enable_enterprise_modules=False,
                height=estimated_height,
                custom_css=custom_css,
                key=grid_key,
                allow_unsafe_jscode=True,
            )

            filtered_data = grid_response["data"]
            filtered_df = pd.DataFrame(filtered_data)
            if "_row_index" in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=["_row_index"])
            csv = filtered_df.to_csv(
                index=False, quoting=2, quotechar='"', sep=";"
            ).encode()
            b64 = base64.b64encode(csv).decode()
            href = (
                f'<a href="data:file/csv;base64,{b64}" download="exported_data.csv" '
                f'class="download-button">Export to CSV</a>'
            )
            st.markdown("""
            <style>
            .download-button {
                display: inline-block;
                padding: 0.5em 1em;
                margin-top: 10px;
                color: white;
                background-color: #FF6A13;
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
            """, unsafe_allow_html=True)
            st.markdown(href, unsafe_allow_html=True)

        with details_col:
            selected_rows = grid_response.get("selected_rows", None)
            if selected_rows is not None and len(selected_rows) > 0:
                selected_row = selected_rows.iloc[0] if hasattr(selected_rows, 'iloc') else selected_rows[0]
                row_index = selected_row.get("_row_index")
                if row_index is not None:
                    row_index = int(row_index)
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
                                        table_dict_str = table_dict_str.replace("'", '"')
                                        table_data = json.loads(table_dict_str)
                                    except Exception:
                                        table_data = ast.literal_eval(table_dict_str)
                                else:
                                    table_data = table_dict_str
                                try:
                                    table_df = pd.DataFrame(table_data)
                                    st.dataframe(table_df, use_container_width=True)
                                except Exception as df_err:
                                    st.warning(
                                        f"Could not convert to DataFrame: {df_err}"
                                    )
                                    st.json(table_data)
                            except Exception as e:
                                st.error(f"Error processing table data: {e}")
                                st.code(str(df.loc[row_index, "table_dict"])[:500])
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
                                    except Exception:
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
    return grid_response
