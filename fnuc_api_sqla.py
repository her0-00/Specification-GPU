import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import re
import seaborn as sns
import matplotlib.pyplot as plt


API_URL = "http://127.0.0.1:8000"

st.title("Apprentissaga automatique + prevision ( E-prod -CasQ'it)")

# --- Choix de la source

def convert_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Convertir les colonnes numériques (même si elles sont au format string)
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass  # Ignore si la conversion échoue

    
    return df
source = st.radio("Source de données", ["csv", "db"])
filename, table_name, username, password = None, None, None, None
df = None

if source == "csv":
    uploaded_file = st.file_uploader("Uploader un fichier CSV", type=["csv"])
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        resp = requests.post(f"{API_URL}/upload_csv/", files=files)
        if resp.ok:
            filename = resp.json()["filename"]
            st.success(f"Fichier {filename} uploadé !")
            data_resp = requests.get(f"{API_URL}/get_csv_data/", params={"filename": filename})
            if data_resp.ok:
                data_json = data_resp.json()
                df = convert_dataframe_types(pd.DataFrame(data_json["data"], columns=data_json["columns"]))
          

                # Remplacer les None explicites par NaN (au cas où)
                df = df.where(pd.notnull(df), None)

                # Calcul du seuil : au moins 50 % de valeurs non manquantes
                seuil = len(df) * 0.5

                # Supprimer les colonnes avec plus de 50 % de valeurs manquantes
                df = df.dropna(axis=1, thresh=seuil)




                
            st.dataframe(df)
        else:
                st.error("Erreur de lecture des données")
    else:
            st.error("Erreur upload")

elif source == "db":
    st.header("Connexion à la base PostgreSQL")
    username = st.text_input("Nom d'utilisateur DB")
    password = st.text_input("Mot de passe DB", type="password")
    if username and password:
        if st.button("Lister les tables"):
            req = {"username": username, "password": password, "query": ""}
            tables = requests.post(f"{API_URL}/db/list_tables/", json=req).json()
            st.session_state["db_tables"] = tables
        tables = st.session_state.get("db_tables", [])
        table_name = st.selectbox("Table", tables) if tables else None
        if table_name:
            sql = f"SELECT * FROM {table_name} limit 10"
            req = {"username": username, "password": password, "query": sql}
            data_resp = requests.post(f"{API_URL}/db/query/", json=req)
            if data_resp.ok:
                data_json = data_resp.json()
                df = convert_dataframe_types(pd.DataFrame(data_json["data"], columns=data_json["columns"]))
                 # Remplacer les None explicites par NaN (au cas où)
                df = df.where(pd.notnull(df), None)

                # Calcul du seuil : au moins 50 % de valeurs non manquantes
                seuil = len(df) * 0.5

                # Supprimer les colonnes avec plus de 50 % de valeurs manquantes
                df = df.dropna(axis=1, thresh=seuil)
                st.dataframe(df)

            else:
                st.error("Erreur de lecture des données")
if df is not None :
   
    df_clean = df.copy()
    df_clean = df_clean.replace([float('inf'), float('-inf')], pd.NA)
    df_clean = df_clean.dropna()



# --- Analyses si DataFrame chargé
if df_clean is not None:
    # Statistiques
    with st.expander("Statistiques descriptives"):
        req = {
            "data": df_clean.to_numpy().tolist(),
            "columns": list(df_clean.columns)
        }
        desc = requests.post(f"{API_URL}/stats/describe/", json=req).json()
        st.write(pd.DataFrame(desc))

    with st.expander("Skewness & Kurtosis"):
        req = {
            "data": df_clean.to_numpy().tolist(),
            "columns": list(df_clean.columns)
        }
        response = requests.post(f"{API_URL}/stats/skew_kurtosis/", json=req)

        if response.ok:
            skew_kurt = response.json()
            st.json(skew_kurt)
        else:
            st.error(f"❌ Erreur API : {response.status_code} - {response.text}")

        

    # Outliers
    with st.expander("Détection d'outliers"):
        method = st.selectbox("Méthode", ["zscore", "iqr"])
        threshold = st.slider("Seuil (z-score)", 2.0, 5.0, 3.0)
        req = {
            "data": df_clean.to_numpy().tolist(),
            "columns": list(df_clean.columns)
        }
        outliers = requests.post(
            f"{API_URL}/stats/outliers/",
            json=req,
            params={"method": method, "threshold": threshold}
        ).json()
        st.write(outliers)

    # Visualisation

st.header("Visualisation")



if df is not None:
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    req = {
        "data": df_clean.to_numpy().tolist(),
        "columns": list(df_clean.columns)
    }
   
    # Exemple : sélection de la colonne à visualiser
    col_name = st.selectbox("📌 Sélectionnez une colonne à visualiser", df_clean.columns)


    # Appel à l'API
    response = requests.post(
        f"{API_URL}/visualization/histogram/",
        json=req,
        params={"col_name": col_name}
    )

    # Affichage du graphique
    if response.ok:
        hist_response = response.json()

        if pd.api.types.is_numeric_dtype(df_clean[col_name]):
            # Histogramme pour données quantitatives
            hist_df = pd.DataFrame({
                "count": hist_response["hist"],
                "bin_start": hist_response["bin_edges"][:-1],
                "bin_end": hist_response["bin_edges"][1:]
            })
            st.subheader("📊 Histogramme")
            st.plotly_chart(
                px.bar(hist_df, x="bin_start", y="count", labels={"bin_start": col_name}),
                use_container_width=True
            )
        else:
            # Diagramme en barres pour données qualitatives
            hist_df = pd.DataFrame({
                "modalities": hist_response["modalities"],
                "frequencies": hist_response["frequencies"]
            })
            st.subheader("📊 Diagramme en barres")
            st.plotly_chart(
                px.bar(hist_df, x="modalities", y="frequencies", labels={"modalities": col_name}),
                use_container_width=True
            )
    else:
        st.error(f"❌ Erreur lors de la récupération des données : {response.text}")

        # Boxplot
        col_num = st.selectbox("Colonne numérique", num_cols, key="hist_box_col")
        box_response = requests.post(
            f"{API_URL}/visualization/boxplot/", json=req,
            params={"col_nums": col_num}
        ).json()
        box_df = pd.DataFrame({
            "stat": ["min", "q1", "median", "q3", "max"],
            "value": [box_response["min"], box_response["q1"], box_response["median"], box_response["q3"], box_response["max"]]
        })
        st.subheader("Boxplot")
        st.plotly_chart(px.box(df, y=col_num), use_container_width=True)

    # Scatter plot
    st.subheader("Nuage de points")
    col_x = st.selectbox("Axe X", num_cols, key="scatter_x")
    col_y = st.selectbox("Axe Y", num_cols, key="scatter_y")
    if col_x and col_y:
        scatter_response = requests.post(
            f"{API_URL}/visualization/scatter/", json=req,
            params={"x": col_x, "y": col_y}
        ).json()
        scatter_df = pd.DataFrame({
            col_x: scatter_response["x"],
            col_y: scatter_response["y"]
        })
        st.plotly_chart(px.scatter(scatter_df, x=col_x, y=col_y), use_container_width=True)

#--ML--



    st.header("🧠 Machine Learning non supervisé")



    st.subheader("⚙️ Entraînement d’un modèle")

    features = st.multiselect("🔢 Variables explicatives (features)", list(df_clean.columns), key="train_features")
    target = st.selectbox("🎯 Variable cible", list(df_clean.columns), key="train_target")
    # Remplacer les valeurs nulles dans la colonne cible par "Non renseigné"
    df_clean[target] = df_clean[target].fillna("Non renseigné")
    df_clean[target].where(pd.notnull(df_clean[target]), None)
    df_clean[target] = df_clean[target].fillna("Non renseigné")
    def normaliser_statut(texte):
        if pd.isnull(texte):
            return texte
        # Remplacer les variantes de "accepté"
        texte = re.sub(r"\b(accepte[eé]?|accepté[e]?|accepte|accepteé|accepteee|accepteé|acepte|acpté)\b", "Acceptée", str(texte), flags=re.IGNORECASE)
        # Remplacer les variantes de "refusé"
        texte = re.sub(r"\b(refuse[eé]?|refusé[e]?|refuse|refusee|refuseé|refus)\b", "Refusée", str(texte), flags=re.IGNORECASE)
        return texte


    df_clean[target]  = df_clean[target].apply(normaliser_statut)

    model_type = st.selectbox("🧪 Modèle", [
        "RandomForest", "LogisticRegression", "SVM", "GradientBoosting", "MLP"
    ], key="train_model")

    if st.button("🚀 Entraîner le modèle") and features and target:
        df_ss = df_clean[features + [target]]  # Sous-ensemble des colonnes sélectionnées
        
        st.write(f"📉 Nombre de lignes après nettoyage : {len(df_ss)}")

        if df_ss.empty:
            st.warning("⚠️ Aucune donnée disponible après nettoyage. Veuillez vérifier les valeurs manquantes ou infinies dans votre fichier.")
        else:

            req = {
                "data": df_ss.to_numpy().tolist(),
                "columns": list(df_ss.columns),
                "target_column": target,
                "model_type": model_type,
                "test_size": 0.2,
                "random_state": 42,
                "selected_features": features,
                "session_id": "session1"
            }

            with st.spinner("Entraînement en cours..."):
                ml_resp = requests.post(f"{API_URL}/ml/train/", json=req)

            if ml_resp.ok:
                ml_res = ml_resp.json()
                st.success("✅ Modèle entraîné avec succès !")
                st.write("🎯 **Accuracy** :", ml_res["accuracy"])
                st.text("📊 Rapport de classification :")
                st.code(ml_res["report"])
                # Conversion en matrice numpy
                confusion_matrix = np.array([
                    [ ml_res["confusion_matrix"][0][0],  ml_res["confusion_matrix"][0][1],  ml_res["confusion_matrix"][0][2]],
                    [ ml_res["confusion_matrix"][1][0],  ml_res["confusion_matrix"][1][1],  ml_res["confusion_matrix"][1][2]],
                    [ ml_res["confusion_matrix"][2][0],  ml_res["confusion_matrix"][2][1],  ml_res["confusion_matrix"][2][2]]
                ])

                # Étiquettes des classes
                class_labels = ["Classe 0", "Classe 1", "Classe 2"]

                # Affichage de la heatmap
                fig, ax = plt.subplots()
                sns.heatmap(confusion_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=class_labels, yticklabels=class_labels, ax=ax)
                ax.set_xlabel("Prédit")
                ax.set_ylabel("Réel")
                ax.set_title("🧩 Matrice de confusion")

                st.pyplot(fig)

                st.session_state["model_path"] = ml_res["model_path"]
            else:
                st.error(f"❌ Erreur dans l'entraînement : {ml_resp.text}")




    st.subheader("📊 Comparaison de plusieurs modèles")

    compare_features = st.multiselect("Variables explicatives (features)", list(df_clean.columns), key="compare_features")
    compare_target = st.selectbox("Variable cible", list(df_clean.columns), key="compare_target")
    model_types = st.multiselect("Modèles à comparer", [
        "RandomForest", "LogisticRegression", "SVM", "GradientBoosting", "MLP"
    ], default=["RandomForest", "LogisticRegression"], key="compare_models")

    if st.button("Comparer les modèles") and compare_features and compare_target and model_types:
        req = {
            "data": df_clean.to_numpy().tolist(),
            "columns": list(df_clean.columns),
            "target_column": compare_target,
            "test_size": 0.2,
            "random_state": 42,
            "session_id": "session1",
            "selected_features": compare_features,
            "model_types": model_types
        }

        compare_resp = requests.post(f"{API_URL}/ml/compare/", json=req)
        if compare_resp.ok:
            results = compare_resp.json()
            for model_name, metrics in results.items():
                st.subheader(f"🧠 Résultats pour {model_name}")
                if "error" in metrics:
                    st.error(f"Erreur : {metrics['error']}")
                else:
                    st.write("🎯 Accuracy :", metrics["accuracy"])
                    st.text("📊 Rapport de classification :")
                    st.code(metrics["report"])
                    st.write("🧩 Matrice de confusion :", metrics["confusion_matrix"])
        else:
            st.error(f"❌ Erreur lors de la comparaison : {compare_resp.text}")

    st.subheader("🔮 Prédiction sur les 5 premières lignes")

    if  features is not None :#"model_path" in st.session_state and features:
        if st.button("Prediction"):
            pred_data = df_clean[features].head(5).values.tolist()
            pred_req = {
                "data": pred_data,
                "columns": features,
                "session_id": "session1"
            } 
            pred_resp = requests.post(f"{API_URL}/ml/predict/", json=pred_req)
            if pred_resp.ok:
                st.write("📈 Prédictions :", pred_resp.json()["predictions"])
            else:
                st.error(f"❌ Erreur lors de la prédiction : {pred_resp.text}")


        # Clustering


    st.header("🔍 Clustering non supervisé (KMeans)")

    if df is not None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        features = st.multiselect("Sélectionnez les variables numériques à utiliser", numeric_cols)
        n_clusters = st.slider("Nombre de clusters", min_value=2, max_value=10, value=3)

        if st.button("Lancer le clustering") and features:
            params = {
                "source": "local",
                "features": features,
                "n_clusters": n_clusters
            }

            try:
                response = requests.post(f"{API_URL}/clustering/kmeans/", params=params)
                if response.ok:
                    result = response.json()
                    df["cluster"] = result["clusters"]
                    st.success("✅ Clustering effectué avec succès !")
                    st.write("📍 Centres des clusters :", result["centers"])

                    if len(features) == 2:
                        fig = px.scatter(
                            df,
                            x=features[0],
                            y=features[1],
                            color=df["cluster"].astype(str),
                            title="Visualisation des clusters",
                            labels={"color": "Cluster"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Sélectionnez exactement 2 variables pour afficher un graphique de dispersion.")
                else:
                    st.error(f"Erreur lors du clustering : {response.text}")
            except Exception as e:
                st.error(f"Erreur de communication avec l'API : {str(e)}")
