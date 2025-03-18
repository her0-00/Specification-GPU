# Chargement des bibliothèques nécessaires -----
library(shiny)
library(gganimate)
library(tidyverse)
library(DT)
library(shinythemes)
library(shinydashboard)
library(FactoMineR)
library(factoextra)
library(ggplot2)
library(corrplot)
library(skimr)
library(shinyjs)
library(plotly)
library(caret)  # For machine learning algorithms
library(randomForest)
library(e1071)
library(class)  # For KNN
library(cluster)  # For k-means

# Function to train a Random Forest model
train_random_forest <- function(data, target) {
  model <- randomForest(as.formula(paste(target, "~ .")), data = data)
  return(model)
}

# Function to train an SVM model
train_svm <- function(data, target) {
  model <- svm(as.formula(paste(target, "~ .")), data = data)
  return(model)
}

# Function to evaluate the model
evaluate_model <- function(model, data, target) {
  predictions <- predict(model, data)
  confusionMatrix(predictions, data[[target]])
}


# Function to train a KNN model
train_knn <- function(data, target, k) {
  train_data <- data[-which(names(data) == target)]
  train_target <- data[[target]]
  knn_model <- knn(train = train_data, test = train_data, cl = train_target, k = k)
  return(knn_model)
}

# Function to perform k-means clustering
perform_kmeans <- function(data, centers) {
  kmeans_model <- kmeans(data, centers)
  return(kmeans_model)
}

# Function to evaluate the KNN model
evaluate_knn <- function(model, data, target) {
  predictions <- model
  confusionMatrix(predictions, data[[target]])
}

# Chargement des données -----
# Assurez-vous que les chemins sont corrects et adaptés à vos fichiers
df <- read.csv2("data/CG_PC.csv",sep=",",dec=".")
#Identifier les doublons selon les trois premières colonnes
duplicated_rows <- df[duplicated(df[, 1:3]) | duplicated(df[, 1:3], fromLast = TRUE), ]
df<- df[!duplicated(df[, 1:3]), ]
# Préparation et nettoyage des données -----
# Transformation des colonnes en facteurs (si applicable)
fact <- c(1:2,11:14)  # Indices des colonnes à transformer en facteurs (ajustez selon vos données)
df[fact] <- lapply(df[, fact], as.factor)

# Création des listes pour les variables quantitatives et qualitatives -----
# Variables quantitatives (numériques)
quant_vars <- names(df)[sapply(df, is.numeric)]

# Variables qualitatives (facteurs ou catégoriques)
qual_vars <- names(df)[sapply(df, is.factor)]

# Variables actives pour l'ACP (quantitatives uniquement)
quant_vars_actives <- quant_vars  # Modifiez ici si vous voulez limiter les variables spécifiques à l'ACP.

# Variables catégorielles pour l'ACP
cat_vars <- qual_vars  # Utilisé pour ajouter des catégories dans certaines visualisations de l'ACP.

# Préparation pour les filtres dans la barre latérale -----
# Extraction des valeurs uniques pour les champs nécessaires
IGP <- unique(df$igp)  # Assurez-vous que "igp" est une colonne existante
marque <- unique(df$manufacturer)  # Assurez-vous que "manufacturer" est une colonne existante

# Gestion des valeurs manquantes -----
# Si vous voulez supprimer ou manipuler les valeurs manquantes, vous pouvez utiliser :
# df <- na.omit(df)  # Supprime les lignes avec des valeurs manquantes
# Ou bien, remplissez les valeurs manquantes avec une valeur par défaut :
# df[is.na(df)] <- 0

# Notes :
# 1. Assurez-vous que les colonnes mentionnées dans `fact`, `igp` et `manufacturer` existent dans vos données.
# 2. Vérifiez les données pour éviter les erreurs dues à des types de données incorrects (e.g., colonnes numériques mal importées).
# 3. Modifiez `quant_vars_actives` et `cat_vars` si vous voulez restreindre les variables disponibles pour certaines analyses.

# Options supplémentaires pour visualisation -----
# (Optionnel) Vous pouvez ajouter des palettes de couleurs ou des paramètres globaux pour ggplot2, par exemple :
theme_set(theme_minimal())  # Définit un thème global pour les graphiques

# Fonction pour calculer la matrice de variances-covariances
get_S <- function(data) {
  if (!is.data.frame(data)) {
    stop("Les données doivent être sous forme de data.frame")
  }
  
  # Vérifier qu'il y a des colonnes numériques pour le calcul
  numeric_data <- data[sapply(data, is.numeric)]
  if (ncol(numeric_data) == 0) {
    stop("Aucune variable quantitative valide trouvée pour calculer la matrice des variances-covariances")
  }
  
  # Calculer la matrice de variances-covariances
  return(cov(numeric_data, use = "complete.obs"))
}

# Fonction pour calculer les valeurs propres et les vecteurs propres
get_LambdasAndEigenVectors <- function(data) {
  if (!is.data.frame(data)) {
    stop("Les données doivent être sous forme de data.frame")
  }
  
  # Vérifier qu'il y a des colonnes numériques
  numeric_data <- data[sapply(data, is.numeric)]
  if (ncol(numeric_data) == 0) {
    stop("Aucune variable quantitative valide trouvée pour calculer les valeurs propres")
  }
  
  # Calcul de la décomposition en valeurs propres
  eigen_res <- eigen(cov(numeric_data, use = "complete.obs"))
  return(list(lambdas = eigen_res$values, vectors = eigen_res$vectors))
}

# Fonction pour calculer le pourcentage d'inertie totale
get_InertiaAxes <- function(data) {
  eigen_res <- get_LambdasAndEigenVectors(data)
  inertia_percentages <- (eigen_res$lambdas / sum(eigen_res$lambdas)) * 100
  return(inertia_percentages)
}

# Fonction pour réaliser l'ACP
actives <- df[, c(3:10)]
# Normalisation des variables quantitatives
data_scaled <- as.data.frame(scale(actives[, -1]))
quant_vars_actives <- colnames(actives[, -1])

update_acp <- function(input, df) {
  if (!is.null(input$acp_vars) && length(input$acp_vars) > 1) {
    reactive_acp$selected_vars <- input$acp_vars
    reactive_acp$result <- doitPerformACP(df, input$acp_vars)
  } else {
    reactive_acp$result <- NULL
    reactive_acp$selected_vars <- NULL
  }
}

doitPerformACP <- function(data, vars) {
  df_selected <- data[, vars, drop = FALSE]
  df_selected <- scale(df_selected)  # Centrage et réduction
  row.names(df_selected) <- row.names(data)
  acp_result <- PCA(df_selected, scale.unit = TRUE, graph = FALSE)
  return(acp_result)
}

reactive_acp <- reactiveValues(result = NULL, selected_vars = NULL)

plot_acp_ind <- function(acp_result, df, color_var, contrib_value) {
  if (!is.null(color_var) && color_var %in% names(df) && color_var != "") {
    # Coloration par variable catégorielle si sélectionnée
    fviz_pca_ind(acp_result,
                 repel = TRUE,
                 pointsize = 1,  # Réduire la taille des points
                 habillage = df[[color_var]],  # Utilisation de la variable catégorielle
                 addEllipses = TRUE,  # Ajout des ellipses de concentration
                 palette = "jco", 
                 alpha.ind = 0.5,  # Transparence des points
                 select.ind = list(contrib = contrib_value))  # Sélectionner les individus avec les plus grandes contributions
  } else {
    # Coloration par cos2 si aucune variable catégorielle n'est sélectionnée
    fviz_pca_ind(acp_result,
                 repel = TRUE,
                 pointsize = 1,  # Réduire la taille des points
                 col.ind = "cos2",  # Rétablir la coloration basée sur cos2
                 gradient.cols = c("#00AFBB", "black", "red"), 
                 alpha.ind = 0.5,  # Transparence des points
                 select.ind = list(contrib = contrib_value))  # Sélectionner les individus avec les plus grandes contributions
  }
}

plot_acp_var <- function(acp_result, selected_vars) {
  fviz_pca_var(acp_result, 
               repel = TRUE, 
               col.var = "contrib", 
               gradient.cols = c("#00AFBB", "black", "red"),
               select.var = list(name = selected_vars))  # Sélectionner uniquement les variables actives choisies
}

plot_acp_biplot <- function(acp_result, df, color_var, selected_vars, contrib_value) {
  if (!is.null(color_var) && color_var %in% names(df) && color_var != "") {
    fviz_pca_biplot(acp_result, 
                    repel = TRUE, 
                    label = "all", 
                    habillage = df[[color_var]],  # Coloration par variable catégorielle
                    select.var = list(name = selected_vars),  # Sélectionner les variables choisies
                    addEllipses = TRUE, 
                    arrows = TRUE,  # Affiche bien les vecteurs des variables
                    palette = "jco",
                    select.ind = list(contrib = contrib_value))
  } else {
    fviz_pca_biplot(acp_result, 
                    repel = TRUE, 
                    label = "all", 
                    col.ind = "cos2",  # Coloration des individus selon cos2
                    gradient.cols = c("#00AFBB", "black", "red"),
                    select.var = list(name = selected_vars), 
                    select.ind = list(contrib = contrib_value),
                    arrows = TRUE)  # Forcer l'affichage des vecteurs
  }
}
